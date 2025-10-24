"""
Scheduler manager for orchestrating cache prewarming.

This module provides the main interface for managing the scheduler lifecycle.
"""

from typing import Any, Dict, List, Optional

from daily_hot_mcp.utils.logger import logger
from .config import SchedulerConfig, SourceConfig
from .warmer import CacheWarmer, WarmResult
from .scheduler import TaskScheduler
from .metrics import MetricsCollector


class SchedulerManager:
    """Manages the background scheduler for cache prewarming."""
    
    def __init__(self, config_path: Optional[str] = None, tool_registry: Optional[List] = None):
        """
        Initialize the scheduler manager.
        
        Args:
            config_path: Path to scheduler configuration file.
            tool_registry: List of MCP tools. If None, will be loaded from tools module.
        """
        self.config_path = config_path
        self._config: Optional[SchedulerConfig] = None
        self._cache_warmer: Optional[CacheWarmer] = None
        self._task_scheduler: Optional[TaskScheduler] = None
        self._metrics_collector: MetricsCollector = MetricsCollector()
        self._tool_registry = tool_registry
        self._is_running = False
        
        logger.info("SchedulerManager initialized")

    
    def _load_tool_registry(self) -> List:
        """
        Load tool registry from tools module.
        
        Returns:
            List of MCP tools.
        """
        if self._tool_registry is not None:
            return self._tool_registry
        
        try:
            from daily_hot_mcp.tools import all_tools
            return all_tools
        except ImportError as e:
            logger.error(f"Failed to import tools: {e}")
            return []
    
    def _initialize_components(self) -> bool:
        """
        Initialize scheduler components.
        
        Returns:
            True if initialization successful, False otherwise.
        """
        try:
            # Load configuration
            self._config = SchedulerConfig(self.config_path)
            sources = self._config.load()
            
            if not sources:
                logger.warning("No sources configured, scheduler will not schedule any jobs")
                return False
            
            # Load tool registry
            tool_registry = self._load_tool_registry()
            if not tool_registry:
                logger.error("No tools available, cannot initialize scheduler")
                return False
            
            # Initialize cache warmer
            self._cache_warmer = CacheWarmer(tool_registry)
            
            # Wrap cache warmer to record metrics
            original_warm = self._cache_warmer.warm_source_sync
            
            def warm_with_metrics(source_config: SourceConfig) -> WarmResult:
                result = original_warm(source_config)
                self._metrics_collector.record_warm_result(result)
                return result
            
            self._cache_warmer.warm_source_sync = warm_with_metrics
            
            # Initialize task scheduler
            self._task_scheduler = TaskScheduler(self._cache_warmer)
            
            # Schedule jobs for enabled sources
            enabled_sources = self._config.get_enabled_sources()
            logger.info(f"Scheduling {len(enabled_sources)} enabled sources")
            
            for source in enabled_sources:
                self._task_scheduler.add_job(source, run_immediately=True)
            
            # Start scheduler first
            self._task_scheduler.start()
            
            # Then run initial warming for all sources immediately
            logger.info("Running initial cache warming for all sources...")
            for source in enabled_sources:
                try:
                    logger.info(f"Starting initial warm for {source.name}")
                    result = self._cache_warmer.warm_source_sync(source)
                    if result.success:
                        logger.info(f"Initial warm completed: {result}")
                    else:
                        logger.error(f"Initial warm failed: {result}")
                except Exception as e:
                    logger.error(f"Error during initial warm for {source.name}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler components: {e}")
            return False
    
    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            logger.info("Starting scheduler...")
            
            # Initialize components (this also starts the scheduler and runs initial warming)
            if not self._initialize_components():
                logger.error("Failed to initialize scheduler, will not start")
                return
            
            self._is_running = True
            logger.info("Scheduler started successfully")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            self._is_running = False
    
    def stop(self) -> None:
        """Gracefully stop the scheduler."""
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            logger.info("Stopping scheduler...")
            
            if self._task_scheduler:
                self._task_scheduler.shutdown(wait=True)
            
            self._is_running = False
            logger.info("Scheduler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    
    def reload_config(self) -> None:
        """Reload configuration and reschedule tasks."""
        if not self._is_running:
            logger.warning("Scheduler is not running, cannot reload config")
            return
        
        try:
            logger.info("Reloading scheduler configuration...")
            
            # Load new configuration
            new_config = SchedulerConfig(self.config_path)
            new_sources = new_config.load()
            
            if not self._task_scheduler:
                logger.error("Task scheduler not initialized")
                return
            
            # Get current job IDs
            current_jobs = {job['id'] for job in self._task_scheduler.get_jobs()}
            
            # Get new enabled sources
            new_enabled = new_config.get_enabled_sources()
            new_job_ids = {f"warm_{source.name}" for source in new_enabled}
            
            # Remove jobs that are no longer in config or disabled
            for job_id in current_jobs:
                if job_id not in new_job_ids:
                    source_name = job_id.replace("warm_", "")
                    self._task_scheduler.remove_job(source_name)
                    logger.info(f"Removed job: {job_id}")
            
            # Add or update jobs for enabled sources
            for source in new_enabled:
                self._task_scheduler.add_job(source)
                logger.info(f"Added/updated job for: {source.name}")
            
            # Update config reference
            self._config = new_config
            
            logger.info(f"Configuration reloaded, {len(new_enabled)} sources scheduled")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")

    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status and metrics.
        
        Returns:
            Dictionary containing scheduler state and metrics.
        """
        status = {
            'running': self._is_running,
            'jobs': [],
            'metrics': {}
        }
        
        if self._task_scheduler and self._is_running:
            status['jobs'] = self._task_scheduler.get_jobs()
        
        if self._metrics_collector:
            status['metrics'] = self._metrics_collector.get_all_metrics()
        
        return status
