"""
定时任务调度器

使用 APScheduler 管理定时任务。
支持事件提醒调度功能。

Author: FeishuMind Team
Created: 2026-02-06
"""

from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any
import asyncio

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """
    任务调度器

    管理 GitHub Trending 推送等定时任务。

    Attributes:
        scheduler: APScheduler 实例
    """

    def __init__(self):
        """初始化任务调度器"""
        self.scheduler = BackgroundScheduler(
            timezone="Asia/Shanghai",
            job_defaults={
                "coalesce": True,  # 合并错过的任务
                "max_instances": 1,  # 同一任务最多1个实例
                "misfire_grace_time": 3600,  # 错过任务的宽限时间
            },
        )
        self._jobs = {}

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Task scheduler started")

    def shutdown(self, wait: bool = True):
        """关闭调度器

        Args:
            wait: 是否等待任务完成
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Task scheduler shutdown")

    def add_github_trending_job(
        self,
        func,
        hour: int = 9,
        minute: int = 0,
        job_id: str = "github_trending",
    ):
        """添加 GitHub Trending 推送任务

        Args:
            func: 要执行的函数
            hour: 小时 (0-23)
            minute: 分钟 (0-59)
            job_id: 任务唯一标识
        """
        # 移除已存在的任务
        if job_id in self._jobs:
            self.remove_job(job_id)

        # 添加新任务
        trigger = CronTrigger(hour=hour, minute=minute)
        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name="GitHub Trending Push",
            replace_existing=True,
        )

        self._jobs[job_id] = job
        logger.info(f"Added job '{job_id}' at {hour:02d}:{minute:02d}")

    def add_custom_job(
        self,
        func,
        cron_expression: str,
        job_id: str,
        job_name: str = "",
    ):
        """添加自定义 Cron 任务

        Args:
            func: 要执行的函数
            cron_expression: Cron 表达式 (分 时 日 月 周)
            job_id: 任务唯一标识
            job_name: 任务名称
        """
        # 移除已存在的任务
        if job_id in self._jobs:
            self.remove_job(job_id)

        # 解析 Cron 表达式
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        minute, hour, day, month, day_of_week = parts

        # 添加新任务
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        )

        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=job_name or job_id,
            replace_existing=True,
        )

        self._jobs[job_id] = job
        logger.info(f"Added job '{job_id}' with cron '{cron_expression}'")

    def remove_job(self, job_id: str):
        """移除任务

        Args:
            job_id: 任务唯一标识
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self._jobs:
                del self._jobs[job_id]
            logger.info(f"Removed job '{job_id}'")
        except Exception as e:
            logger.warning(f"Failed to remove job '{job_id}': {e}")

    def pause_job(self, job_id: str):
        """暂停任务

        Args:
            job_id: 任务唯一标识
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job '{job_id}'")
        except Exception as e:
            logger.warning(f"Failed to pause job '{job_id}': {e}")

    def resume_job(self, job_id: str):
        """恢复任务

        Args:
            job_id: 任务唯一标识
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job '{job_id}'")
        except Exception as e:
            logger.warning(f"Failed to resume job '{job_id}': {e}")

    def get_job_info(self, job_id: str):
        """获取任务信息

        Args:
            job_id: 任务唯一标识

        Returns:
            任务信息字典，不存在返回 None
        """
        job = self.scheduler.get_job(job_id)
        if not job:
            return None

        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }

    def list_jobs(self):
        """列出所有任务

        Returns:
            任务信息列表
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
            )
        return jobs

    def is_running(self) -> bool:
        """检查调度器是否运行

        Returns:
            是否运行中
        """
        return self.scheduler.running

    def schedule_reminder(
        self,
        event_id: str,
        remind_time: datetime,
        callback: Callable,
        job_id: Optional[str] = None,
    ):
        """添加单次提醒任务。

        Args:
            event_id: 事件 ID
            remind_time: 提醒时间
            callback: 回调函数（异步或同步）
            job_id: 任务 ID（可选，默认为 "reminder_{event_id}"）

        Returns:
            任务 ID

        Examples:
            >>> def send_reminder(event_id):
            ...     print(f"Reminder for {event_id}")
            >>> scheduler.schedule_reminder(
            ...     event_id="evt_123",
            ...     remind_time=datetime(2026, 2, 7, 14, 45),
            ...     callback=send_reminder
            ... )
        """
        if job_id is None:
            job_id = f"reminder_{event_id}_{int(remind_time.timestamp())}"

        logger.info(
            f"Scheduling reminder for event {event_id[:8]}*** "
            f"at {remind_time}"
        )

        # 移除已存在的任务
        if job_id in self._jobs:
            self.remove_job(job_id)

        # 添加提醒任务
        trigger = DateTrigger(run_date=remind_time)

        job = self.scheduler.add_job(
            self._wrap_callback(callback, event_id),
            trigger=trigger,
            id=job_id,
            name=f"Reminder for {event_id}",
            replace_existing=True,
        )

        self._jobs[job_id] = job
        logger.info(f"Added reminder job '{job_id}'")
        return job_id

    def schedule_event_reminders(
        self,
        event_id: str,
        event_start_time: datetime,
        callback: Callable,
        reminder_minutes: list = None,
    ):
        """为事件添加多个提醒时间点。

        Args:
            event_id: 事件 ID
            event_start_time: 事件开始时间
            callback: 回调函数
            reminder_minutes: 提前提醒时间列表（分钟），默认 [15, 60, 1440]

        Returns:
            提醒任务 ID 列表

        Examples:
            >>> job_ids = scheduler.schedule_event_reminders(
            ...     event_id="evt_123",
            ...     event_start_time=datetime(2026, 2, 7, 15, 0),
            ...     callback=send_reminder,
            ...     reminder_minutes=[15, 60, 1440]
            ... )
        """
        if reminder_minutes is None:
            reminder_minutes = [15, 60, 1440]  # 15分钟、1小时、1天

        logger.info(
            f"Scheduling {len(reminder_minutes)} reminders for event {event_id[:8]}***"
        )

        job_ids = []
        current_time = datetime.now()

        for minutes in reminder_minutes:
            remind_time = event_start_time - timedelta(minutes=minutes)

            # 只有当提醒时间在未来时才添加
            if remind_time > current_time:
                job_id = self.schedule_reminder(
                    event_id=event_id,
                    remind_time=remind_time,
                    callback=callback,
                    job_id=f"reminder_{event_id}_{minutes}min",
                )
                job_ids.append(job_id)
            else:
                logger.warning(
                    f"Reminder time {remind_time} is in the past, skipping"
                )

        logger.info(f"Scheduled {len(job_ids)} reminders")
        return job_ids

    def cancel_event_reminders(self, event_id: str):
        """取消事件的所有提醒。

        Args:
            event_id: 事件 ID

        Returns:
            取消的任务数量
        """
        logger.info(f"Cancelling all reminders for event {event_id[:8]}***")

        cancelled_count = 0
        jobs_to_remove = []

        # 查找所有相关任务
        for job_id, job in self._jobs.items():
            if job_id.startswith(f"reminder_{event_id}"):
                jobs_to_remove.append(job_id)

        # 移除任务
        for job_id in jobs_to_remove:
            self.remove_job(job_id)
            cancelled_count += 1

        logger.info(f"Cancelled {cancelled_count} reminder jobs")
        return cancelled_count

    def _wrap_callback(self, callback: Callable, event_id: str) -> Callable:
        """包装回调函数，支持异步和同步函数。

        Args:
            callback: 回调函数
            event_id: 事件 ID

        Returns:
            包装后的函数
        """
        def wrapped():
            try:
                # 检查是否是异步函数
                if asyncio.iscoroutinefunction(callback):
                    # 如果是异步函数，在新事件循环中运行
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 如果循环正在运行，创建任务
                            asyncio.create_task(callback(event_id))
                        else:
                            # 如果循环未运行，直接运行
                            loop.run_until_complete(callback(event_id))
                    except RuntimeError:
                        # 没有事件循环，创建新的
                        asyncio.run(callback(event_id))
                else:
                    # 同步函数，直接调用
                    callback(event_id)

            except Exception as e:
                logger.error(
                    f"Error executing reminder callback for event {event_id[:8]}***: {e}"
                )

        return wrapped

    def get_reminder_jobs(self, event_id: str) -> list:
        """获取事件的所有提醒任务。

        Args:
            event_id: 事件 ID

        Returns:
            提醒任务信息列表
        """
        jobs = []
        for job_id, job in self._jobs.items():
            if job_id.startswith(f"reminder_{event_id}"):
                jobs.append(
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": (
                            job.next_run_time.isoformat() if job.next_run_time else None
                        ),
                    }
                )
        return jobs
