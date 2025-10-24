"""
Task scheduling using APScheduler.

This module manages periodic task execution for cache warming.
"""

from typing import Any, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from daily_hot_mcp.utils.logger import logger
from .config import SourceConfig
from .warmer import CacheWarmer, WarmResult


class TaskScheduler:
    """Manages periodic task scheduling using APScheduler."""
    
    def __init__(self, cache_warmer: CacheWarmer):
        """
        Initialize task scheduler.
        
        Args:
            cache_warmer: CacheWarmer instance for executing warming tasks.
        """
        self.cache_warmer = cache_warmer
        
        # Configure APScheduler with thread pool
        executors = {
            'default': ThreadPoolExecutor(max_workers=10)
        }
        
        job_defaults = {
            'coalesce': True,  # Combine multiple pending executions into one
            'max_instances': 1,  # Only one instance of each job at a time
            'misfire_grace_time': 300  # 5 minutes grace time for misfired jobs
        }
        
        self.scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults
        )
        
        logger.info("TaskScheduler initialized")

    
    def _job_wrapper(self, source_config: SourceConfig) -> None:
        """
        Wrapper function for scheduled jobs.
        
        Args:
            source_config: Configuration for the source to warm.
        """
        try:
            result = self.cache_warmer.warm_source_sync(source_config)
            if result.success:
                logger.info(f"Scheduled job completed: {result}")
            else:
                logger.error(f"Scheduled job failed: {result}")
        except Exception as e:
            logger.error(f"Job wrapper error for {source_config.name}: {e}")
    
    def add_job(self, source_config: SourceConfig, run_immediately: bool = False) -> None:
        """
        Add a periodic job for a data source.
        
        Args:
            source_config: Configuration for the source to schedule.
            run_immediately: Whether to run the job immediately on startup (deprecated, handled by manager).
        """
        job_id = f"warm_{source_config.name}"
        
        # Check if job already exists
        if self.scheduler.get_job(job_id):
            logger.warning(f"Job {job_id} already exists, removing old job")
            self.scheduler.remove_job(job_id)
        
        # Create interval trigger
        trigger = IntervalTrigger(minutes=source_config.interval_minutes)
        
        # Add job
        self.scheduler.add_job(
            func=self._job_wrapper,
            trigger=trigger,
            args=[source_config],
            id=job_id,
            name=f"Warm cache for {source_config.name}",
            replace_existing=True
        )
        
        logger.info(
            f"Added job {job_id} with interval {source_config.interval_minutes} minutes"
        )
    
    def remove_job(self, source_name: str) -> None:
        """
        Remove a scheduled job.
        
        Args:
            source_name: Name of the source whose job should be removed.
        """
        job_id = f"warm_{source_name}"
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler is already running")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler.
        
        Args:
            wait: Whether to wait for running jobs to complete.
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler shut down")
        else:
            logger.warning("Scheduler is not running")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        Get information about all scheduled jobs.
        
        Returns:
            List of job information dictionaries.
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            jobs.append(job_info)
        
        return jobs
