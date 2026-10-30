"""
会议管理 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func

from config import settings
from core.database import get_db
from core.response import success, error
from core.exceptions import BusinessException
from models.meeting import Meeting
from models.transcript import Transcript
from models.speaker import Speaker
from models.minutes import Minutes
from schemas.meeting import MeetingOut, MeetingDetailOut, MeetingListOut
from schemas.transcript import SpeakerOut, SpeakerUpdateRequest, TranscriptOut
from schemas.minutes import MinutesDetailOut, TodoItem
from services.storage_service import storage_service
from services.meeting_service import meeting_service
from services.speaker_service import speaker_service
from services.llm_service import llm_service
import json

router = APIRouter(prefix="/meetings", tags=["会议管理"])


@router.post("/upload", summary="上传会议音视频")
async def upload_meeting(
    title: str = Form(..., description="会议标题"),
    file: UploadFile = File(..., description="音视频文件"),
    auto_process: bool = Form(True, description="是否自动处理"),
    share_dept: bool = Form(False, description="是否部门分享"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    上传会议音视频文件

    - 保存文件到本地
    - 创建会议记录
    - 如果开启自动处理，后台触发 ASR 转写
    """
    try:
        # 1. 先创建临时会议记录以获取 meeting_id
        temp_meeting = Meeting(
            title=title,
            file_path="",
            file_url="",
            status="uploaded",
            create_user_id=1,  # MVP 阶段固定为 admin 用户
            share_dept=1 if share_dept else 0,
            auto_process=1 if auto_process else 0
        )
        db.add(temp_meeting)
        await db.flush()  # 获取 meeting_id

        # 2. 保存文件
        file_path, file_url = await storage_service.save_upload_file(file, temp_meeting.meeting_id)

        # 3. 更新会议记录
        temp_meeting.file_path = file_path
        temp_meeting.file_url = file_url
        await db.commit()
        await db.refresh(temp_meeting)

        # 4. 如果开启自动处理，触发流水线
        if auto_process:
            background_tasks.add_task(
                _trigger_pipeline_background,
                temp_meeting.meeting_id
            )

        return success(
            data={
                "meeting_id": temp_meeting.meeting_id,
                "title": temp_meeting.title,
                "status": temp_meeting.status,
                "auto_process": auto_process
            },
            message="上传成功" + ("，已启动自动处理" if auto_process else "")
        )

    except BusinessException as e:
        return error(message=str(e))
    except Exception as e:
        return error(message=f"上传失败: {str(e)}")


async def _trigger_pipeline_background(meeting_id: int):
    """后台任务：触发处理流水线"""
    from core.database import async_session_maker

    async with async_session_maker() as db:
        try:
            # 检查公网URL（仅真实 ASR 需要；Mock 模式不下载音频）
            if settings.ASR_PROVIDER != "mock":
                is_valid, msg = storage_service.check_public_url_accessibility()
                if not is_valid:
                    await meeting_service.mark_failed(meeting_id, msg, db)
                    return

            # 提交 ASR 任务
            from services.asr_service import asr_service

            result = await db.execute(
                select(Meeting).where(Meeting.meeting_id == meeting_id)
            )
            meeting = result.scalar_one_or_none()

            if meeting:
                await asr_service.submit_transcribe_task(meeting_id, meeting.file_url, db)

        except Exception as e:
            print(f"[Background] 触发流水线失败: {e}")
            await meeting_service.mark_failed(meeting_id, str(e), db)


@router.get("", summary="会议列表")
async def get_meeting_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    title: Optional[str] = Query(None, description="标题搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取会议列表（分页、搜索、筛选）

    MVP 阶段：返回所有会议（无权限过滤）
    """
    try:
        # 构建查询条件
        conditions = []

        if title:
            conditions.append(Meeting.title.like(f"%{title}%"))

        if status:
            conditions.append(Meeting.status == status)

        # 查询总数
        count_query = select(func.count(Meeting.meeting_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 查询列表
        query = select(Meeting).order_by(Meeting.created_at.desc())
        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        meetings = result.scalars().all()

        return success(data={
            "list": [MeetingOut.model_validate(m) for m in meetings],
            "total": total,
            "page": page,
            "page_size": page_size
        })

    except Exception as e:
        return error(message=f"查询失败: {str(e)}")


@router.get("/{meeting_id}", summary="会议详情")
async def get_meeting_detail(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取会议详情（包含转写、发言人、纪要）
    """
    try:
        detail = await meeting_service.get_meeting_detail(meeting_id, db)

        if not detail:
            return error(message="会议不存在", code=404)

        meeting = detail["meeting"]
        transcripts = detail["transcripts"]
        speakers = detail["speakers"]
        minutes = detail["minutes"]

        # 构建返回数据
        result = {
            "meeting": MeetingOut.model_validate(meeting),
            "transcripts": [TranscriptOut.model_validate(t) for t in transcripts],
            "speakers": [SpeakerOut.model_validate(s) for s in speakers],
            "minutes": None
        }

        # 解析纪要
        if minutes:
            todos = []
            if minutes.todos:
                try:
                    todos_data = json.loads(minutes.todos) if isinstance(minutes.todos, str) else minutes.todos
                    todos = [TodoItem(**t) for t in todos_data]
                except:
                    pass

            speaker_summary = {}
            if minutes.speaker_summary:
                try:
                    speaker_summary = json.loads(minutes.speaker_summary) if isinstance(minutes.speaker_summary, str) else minutes.speaker_summary
                except:
                    pass

            keywords_list = []
            if minutes.keywords:
                keywords_list = [k.strip() for k in minutes.keywords.split(",") if k.strip()]

            result["minutes"] = {
                "summary": minutes.summary,
                "keywords": keywords_list,
                "todos": todos,
                "speaker_summary": speaker_summary,
                "markdown": minutes.markdown
            }

        return success(data=result)

    except Exception as e:
        return error(message=f"查询失败: {str(e)}")


@router.delete("/{meeting_id}", summary="删除会议")
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除会议（级联删除关联数据）"""
    try:
        await meeting_service.delete_meeting(meeting_id, db)
        return success(message="删除成功")

    except BusinessException as e:
        return error(message=str(e))
    except Exception as e:
        return error(message=f"删除失败: {str(e)}")


@router.post("/{meeting_id}/process", summary="手动触发处理")
async def trigger_process(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """手动触发完整流水线（ASR → LLM）"""
    try:
        await meeting_service.trigger_pipeline(meeting_id, db, background_tasks)
        return success(message="处理已启动")

    except BusinessException as e:
        return error(message=str(e))
    except Exception as e:
        return error(message=f"启动失败: {str(e)}")


@router.put("/{meeting_id}/speakers", summary="重命名发言人")
async def rename_speakers(
    meeting_id: int,
    updates: List[SpeakerUpdateRequest],
    db: AsyncSession = Depends(get_db)
):
    """批量重命名发言人"""
    try:
        rename_map = {u.speaker_id: u.speaker_name for u in updates}
        await speaker_service.batch_rename_speakers(meeting_id, rename_map, db)
        return success(message="重命名成功")

    except BusinessException as e:
        return error(message=str(e))
    except Exception as e:
        return error(message=f"重命名失败: {str(e)}")


@router.get("/{meeting_id}/markdown", summary="获取 Markdown 纪要")
async def get_markdown(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取完整 Markdown 纪要（用于导出）"""
    try:
        result = await db.execute(
            select(Minutes).where(Minutes.meeting_id == meeting_id)
        )
        minutes = result.scalar_one_or_none()

        if not minutes or not minutes.markdown:
            return error(message="纪要不存在或尚未生成", code=404)

        return success(data={"markdown": minutes.markdown})

    except Exception as e:
        return error(message=f"查询失败: {str(e)}")


@router.put("/{meeting_id}/share", summary="修改分享设置")
async def update_share_setting(
    meeting_id: int,
    share_dept: bool,
    db: AsyncSession = Depends(get_db)
):
    """开启/关闭部门分享"""
    try:
        await meeting_service.update_share_setting(meeting_id, share_dept, db)
        return success(message="分享设置已更新")

    except BusinessException as e:
        return error(message=str(e))
    except Exception as e:
        return error(message=f"更新失败: {str(e)}")
