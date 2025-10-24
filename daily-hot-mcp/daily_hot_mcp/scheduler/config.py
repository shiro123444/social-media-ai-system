"""
Configuration management for the scheduler.

This module handles loading, validating, and managing scheduler configuration
from JSON files or default values.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from daily_hot_mcp.utils.logger import logger


@dataclass
class SourceConfig:
    """Configuration for a single data source."""
    
    name: str
    tool_name: str
    enabled: bool = True
    interval_minutes: int = 25
    tool_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Source name cannot be empty")
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        if self.interval_minutes < 1:
            raise ValueError(f"Interval must be at least 1 minute, got {self.interval_minutes}")
        if self.interval_minutes > 1440:  # 24 hours
            logger.warning(f"Source {self.name} has very long interval: {self.interval_minutes} minutes")


class SchedulerConfig:
    """Scheduler configuration manager."""
    
    DEFAULT_INTERVAL_MINUTES = 25
    DEFAULT_CONFIG_LOCATIONS = [
        "scheduler_config.json",
        "daily_hot_mcp/scheduler_config.json",
        os.path.expanduser("~/.config/daily-hot-mcp/scheduler_config.json"),
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, searches default locations.
        """
        self.config_path = config_path
        self._sources: List[SourceConfig] = []
        self._default_interval = self.DEFAULT_INTERVAL_MINUTES

    def _find_config_file(self) -> Optional[Path]:
        """
        Find configuration file in default locations.
        
        Returns:
            Path to config file if found, None otherwise.
        """
        # Check environment variable first
        env_path = os.getenv("SCHEDULER_CONFIG_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
            logger.warning(f"Config path from env var not found: {env_path}")
        
        # Check default locations
        for location in self.DEFAULT_CONFIG_LOCATIONS:
            path = Path(location)
            if path.exists():
                return path
        
        return None
    
    def load(self) -> List[SourceConfig]:
        """
        Load and validate configuration.
        
        Returns:
            List of source configurations.
        """
        config_file = None
        
        if self.config_path:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Specified config file not found: {self.config_path}")
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        else:
            config_file = self._find_config_file()
        
        if config_file:
            logger.info(f"Loading scheduler config from: {config_file}")
            self._load_from_file(config_file)
        else:
            logger.info("No config file found, using default configuration")
            self._load_defaults()
        
        return self._sources
    
    def _load_from_file(self, config_file: Path) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file.
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load default interval if specified
            self._default_interval = config_data.get(
                "default_interval_minutes", 
                self.DEFAULT_INTERVAL_MINUTES
            )
            
            # Load sources
            sources_data = config_data.get("sources", [])
            self._sources = []
            
            for source_data in sources_data:
                try:
                    source = SourceConfig(
                        name=source_data["name"],
                        tool_name=source_data["tool_name"],
                        enabled=source_data.get("enabled", True),
                        interval_minutes=source_data.get(
                            "interval_minutes", 
                            self._default_interval
                        ),
                        tool_params=source_data.get("tool_params", {})
                    )
                    self._sources.append(source)
                except (KeyError, ValueError) as e:
                    logger.error(f"Invalid source configuration: {e}")
                    continue
            
            logger.info(f"Loaded {len(self._sources)} source configurations")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            raise
    
    def _load_defaults(self) -> None:
        """Load default configuration (empty sources list)."""
        self._sources = []
        logger.info("Using empty default configuration")
    
    def get_enabled_sources(self) -> List[SourceConfig]:
        """
        Get list of enabled sources.
        
        Returns:
            List of enabled source configurations.
        """
        return [source for source in self._sources if source.enabled]
    
    def get_all_sources(self) -> List[SourceConfig]:
        """
        Get all sources (enabled and disabled).
        
        Returns:
            List of all source configurations.
        """
        return self._sources.copy()
