"""
定时任务调度器
"""
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from config import settings
from core.database import async_session_maker
from models.meeting import Meeting
from services.asr_service import asr_service
from services.llm_service import llm_service
from services.storage_service import storage_service


# 创建调度器实例
scheduler = AsyncIOScheduler()


async def poll_asr_tasks():
    """
    定时轮询 ASR 转写任务状态

    扫描所有 status=transcribing 的会议，查询 ASR 结果；
    超过 ASR_TASK_TIMEOUT_SECONDS 的任务直接标记失败，避免永久卡在 transcribing。
    """
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(Meeting).where(Meeting.status == "transcribing")
            )
            meetings = result.scalars().all()

            if not meetings:
                return

            print(f"[Scheduler] 开始轮询 {len(meetings)} 个转写任务...")

            for meeting in meetings:
                if not meeting.asr_task_id:
                    continue

                # 任务超时检查：以提交转写时写入的 updated_at 为计时起点
                if meeting.updated_at:
                    age = (datetime.now() - meeting.updated_at).total_seconds()
                    if age > settings.ASR_TASK_TIMEOUT_SECONDS:
                        timeout_minutes = settings.ASR_TASK_TIMEOUT_SECONDS // 60
                        await asr_service.mark_failed(
                            meeting.meeting_id,
                            f"ASR 任务超时（超过 {timeout_minutes} 分钟未完成）",
                            db,
                        )
                        print(
                            f"[Scheduler] 会议 {meeting.meeting_id} ASR 任务超时，已标记失败"
                        )
                        continue

                # 查询 ASR 任务结果
                asr_result = await asr_service.poll_transcribe_result(
                    meeting.meeting_id,
                    meeting.asr_task_id,
                    db
                )

                # 转写完成后继续生成纪要
                if asr_result and asr_result.status == "succeeded":
                    print(f"[Scheduler] 会议 {meeting.meeting_id} 转写成功，开始生成纪要...")
                    try:
                        await llm_service.generate_minutes(meeting.meeting_id, db)
                    except Exception as e:
                        print(f"[Scheduler] 会议 {meeting.meeting_id} 生成纪要失败: {e}")

        except Exception as e:
            print(f"[Scheduler] 轮询 ASR 任务失败: {e}")


async def recover_stuck_pipelines():
    """
    恢复卡住的流水线

    1. status=summarizing 且超过 LLM_STUCK_TIMEOUT_SECONDS：进程重启/异常退出导致，
       重新生成纪要；
    2. status=transcribed、auto_process=1 且超过 TRANSCRIBED_STUCK_TIMEOUT_SECONDS：
       ASR 成功与 LLM 触发之间进程退出，补跑 LLM。
    """
    async with async_session_maker() as db:
        now = datetime.now()

        try:
            # 1. summarizing 卡住
            result = await db.execute(
                select(Meeting).where(Meeting.status == "summarizing")
            )
            for meeting in result.scalars().all():
                if not meeting.updated_at:
                    continue

                age = (now - meeting.updated_at).total_seconds()
                if age < settings.LLM_STUCK_TIMEOUT_SECONDS:
                    continue

                print(
                    f"[Recovery] 会议 {meeting.meeting_id} 卡在 summarizing "
                    f"{int(age)}s，重新生成纪要"
                )
                try:
                    await llm_service.generate_minutes(meeting.meeting_id, db)
                except Exception as e:
                    print(f"[Recovery] 会议 {meeting.meeting_id} 恢复失败: {e}")

            # 2. 自动处理会议已转写但未继续 LLM
            result = await db.execute(
                select(Meeting).where(
                    Meeting.status == "transcribed",
                    Meeting.auto_process.is_(True),
                )
            )
            for meeting in result.scalars().all():
                if not meeting.updated_at:
                    continue

                age = (now - meeting.updated_at).total_seconds()
                if age < settings.TRANSCRIBED_STUCK_TIMEOUT_SECONDS:
                    continue

                print(
                    f"[Recovery] 会议 {meeting.meeting_id} 已转写但未生成纪要，补跑 LLM"
                )
                try:
                    await llm_service.generate_minutes(meeting.meeting_id, db)
                except Exception as e:
                    print(f"[Recovery] 会议 {meeting.meeting_id} 补跑失败: {e}")

            # 3. uploaded + auto_process=1，但 ASR 一直没启动（例如进程重启丢失后台任务）
            result = await db.execute(
                select(Meeting).where(
                    Meeting.status == "uploaded",
                    Meeting.auto_process.is_(True),
                )
            )
            for meeting in result.scalars().all():
                if not meeting.updated_at:
                    continue

                age = (now - meeting.updated_at).total_seconds()
                if age < settings.UPLOADED_STUCK_TIMEOUT_SECONDS:
                    continue

                print(
                    f"[Recovery] 会议 {meeting.meeting_id} 已上传但 ASR 未启动，补提交"
                )
                try:
                    audio_url = storage_service.get_accessible_url(
                        meeting.file_path, meeting.file_url
                    )
                    if settings.ASR_PROVIDER != "mock":
                        is_valid, msg = storage_service.check_public_url_accessibility(audio_url)
                        if not is_valid:
                            await asr_service.mark_failed(meeting.meeting_id, msg, db)
                            continue

                    await asr_service.submit_transcribe_task(
                        meeting.meeting_id, audio_url, db
                    )
                except Exception as e:
                    print(f"[Recovery] 会议 {meeting.meeting_id} 补提交 ASR 失败: {e}")
                    await asr_service.mark_failed(
                        meeting.meeting_id, f"自动处理启动失败: {e}", db
                    )

        except Exception as e:
            print(f"[Recovery] 恢复任务失败: {e}")


def start_scheduler():
    """启动调度器"""
    scheduler.add_job(
        poll_asr_tasks,
        trigger=IntervalTrigger(seconds=settings.ASR_POLL_INTERVAL),
        id="poll_asr_tasks",
        name="轮询 ASR 转写任务",
        replace_existing=True
    )

    scheduler.add_job(
        recover_stuck_pipelines,
        trigger=IntervalTrigger(seconds=settings.PIPELINE_RECOVERY_INTERVAL),
        id="recover_stuck_pipelines",
        name="恢复卡住的会议流水线",
        replace_existing=True
    )

    scheduler.start()
    print(
        f"[Scheduler] 调度器已启动，ASR 轮询间隔: {settings.ASR_POLL_INTERVAL} 秒，"
        f"流水线恢复扫描间隔: {settings.PIPELINE_RECOVERY_INTERVAL} 秒"
    )


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] 调度器已关闭")
