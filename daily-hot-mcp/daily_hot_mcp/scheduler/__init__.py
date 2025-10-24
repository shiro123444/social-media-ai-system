"""
Scheduler module for automatic cache prewarming.

This module provides background scheduling capabilities to automatically
fetch data from all configured sources and populate the cache before
user requests, improving response times.
"""

from .manager import SchedulerManager

__all__ = ["SchedulerManager"]
