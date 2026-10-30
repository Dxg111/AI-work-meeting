"""
定时任务调度器
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from core.database import async_session_maker
from models.meeting import Meeting
from services.asr_service import asr_service
from services.llm_service import llm_service
from config import settings


# 创建调度器实例
scheduler = AsyncIOScheduler()


async def poll_asr_tasks():
    """
    定时轮询 ASR 转写任务状态

    扫描所有 status=transcribing 的会议，查询 ASR 结果
    """
    async with async_session_maker() as db:
        try:
            # 查询所有正在转写中的会议
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

                # 查询 ASR 任务结果
                asr_result = await asr_service.poll_transcribe_result(
                    meeting.meeting_id,
                    meeting.asr_task_id,
                    db
                )

                # 如果转写成功，继续生成纪要
                # 注意：ASR 任务无论是自动处理还是手动触发，转写完成后都应继续走 LLM，
                # 否则手动处理的会议会永久停在 transcribed 状态。
                if asr_result and asr_result.status == "succeeded":
                    print(f"[Scheduler] 会议 {meeting.meeting_id} 转写成功，开始生成纪要...")
                    try:
                        await llm_service.generate_minutes(meeting.meeting_id, db)
                    except Exception as e:
                        print(f"[Scheduler] 会议 {meeting.meeting_id} 生成纪要失败: {e}")

        except Exception as e:
            print(f"[Scheduler] 轮询 ASR 任务失败: {e}")


def start_scheduler():
    """启动调度器"""
    # 添加 ASR 轮询任务
    scheduler.add_job(
        poll_asr_tasks,
        trigger=IntervalTrigger(seconds=settings.ASR_POLL_INTERVAL),
        id="poll_asr_tasks",
        name="轮询 ASR 转写任务",
        replace_existing=True
    )

    scheduler.start()
    print(f"[Scheduler] 调度器已启动，ASR 轮询间隔: {settings.ASR_POLL_INTERVAL} 秒")


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] 调度器已关闭")
