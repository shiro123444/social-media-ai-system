"""
Cache warming logic for the scheduler.

This module handles executing tool functions and populating the cache
with fresh data before user requests.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastmcp.tools import Tool

from daily_hot_mcp.utils.logger import logger
from .config import SourceConfig


@dataclass
class WarmResult:
    """Result of a cache warming operation."""
    
    source_name: str
    success: bool
    timestamp: datetime
    duration_seconds: float
    error_message: Optional[str] = None
    items_cached: int = 0
    
    def __str__(self) -> str:
        """String representation of the result."""
        status = "SUCCESS" if self.success else "FAILED"
        msg = f"[{status}] {self.source_name} ({self.duration_seconds:.2f}s)"
        if self.success:
            msg += f" - {self.items_cached} items"
        else:
            msg += f" - {self.error_message}"
        return msg



class CacheWarmer:
    """Executes data fetching and cache population."""
    
    def __init__(self, tool_registry: List[Tool]):
        """
        Initialize with tool registry.
        
        Args:
            tool_registry: List of all available MCP tools.
        """
        self.tool_registry = tool_registry
        self._tool_map: Dict[str, Tool] = {}
        
        # Build tool name to tool object mapping
        for tool in tool_registry:
            self._tool_map[tool.name] = tool
        
        logger.info(f"CacheWarmer initialized with {len(self._tool_map)} tools")
    
    def _find_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Find a tool by name.
        
        Args:
            tool_name: Name of the tool to find.
            
        Returns:
            Tool object if found, None otherwise.
        """
        return self._tool_map.get(tool_name)
    
    async def warm_source(self, source_config: SourceConfig) -> WarmResult:
        """
        Fetch data for a single source and cache it.
        
        Args:
            source_config: Configuration for the source to warm.
            
        Returns:
            WarmResult with success status and metrics.
        """
        start_time = time.time()
        timestamp = datetime.now()
        
        try:
            # Find the tool
            tool = self._find_tool(source_config.tool_name)
            if not tool:
                error_msg = f"Tool not found: {source_config.tool_name}"
                logger.error(f"[{source_config.name}] {error_msg}")
                return WarmResult(
                    source_name=source_config.name,
                    success=False,
                    timestamp=timestamp,
                    duration_seconds=time.time() - start_time,
                    error_message=error_msg
                )
            
            # Call the tool function with parameters
            logger.info(f"[{source_config.name}] Warming cache with tool {source_config.tool_name}")
            
            # Execute the tool function
            result = await tool.fn(**source_config.tool_params)
            
            # Count items if result is a list
            items_count = len(result) if isinstance(result, list) else 1
            
            duration = time.time() - start_time
            logger.info(
                f"[{source_config.name}] Cache warmed successfully "
                f"({items_count} items, {duration:.2f}s)"
            )
            
            return WarmResult(
                source_name=source_config.name,
                success=True,
                timestamp=timestamp,
                duration_seconds=duration,
                items_cached=items_count
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error(
                f"[{source_config.name}] Failed to warm cache: {error_msg}"
            )
            
            return WarmResult(
                source_name=source_config.name,
                success=False,
                timestamp=timestamp,
                duration_seconds=duration,
                error_message=error_msg
            )
    
    def warm_source_sync(self, source_config: SourceConfig) -> WarmResult:
        """
        Synchronous wrapper for warm_source (for APScheduler).
        
        Args:
            source_config: Configuration for the source to warm.
            
        Returns:
            WarmResult with success status and metrics.
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.warm_source(source_config))
                return result
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"[{source_config.name}] Sync wrapper error: {e}")
            return WarmResult(
                source_name=source_config.name,
                success=False,
                timestamp=datetime.now(),
                duration_seconds=0.0,
                error_message=f"Sync wrapper error: {str(e)}"
            )
