"""
Metrics collection for scheduler performance tracking.

This module tracks and reports scheduler performance metrics.
"""

import threading
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .warmer import WarmResult


class MetricsCollector:
    """Collects and stores scheduler metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self._lock = threading.Lock()
        self._metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_duration': 0.0,
            'total_items': 0,
            'last_success_time': None,
            'last_failure_time': None,
            'last_error': None,
            'last_duration': 0.0,
            'last_items': 0
        })
    
    def record_warm_result(self, result: WarmResult) -> None:
        """
        Record a cache warming result.
        
        Args:
            result: WarmResult from a cache warming operation.
        """
        with self._lock:
            metrics = self._metrics[result.source_name]
            
            # Update counters
            metrics['total_runs'] += 1
            if result.success:
                metrics['successful_runs'] += 1
                metrics['last_success_time'] = result.timestamp.isoformat()
                metrics['total_items'] += result.items_cached
                metrics['last_items'] = result.items_cached
            else:
                metrics['failed_runs'] += 1
                metrics['last_failure_time'] = result.timestamp.isoformat()
                metrics['last_error'] = result.error_message
            
            # Update duration
            metrics['total_duration'] += result.duration_seconds
            metrics['last_duration'] = result.duration_seconds

    
    def get_source_metrics(self, source_name: str) -> Dict[str, Any]:
        """
        Get metrics for a specific source.
        
        Args:
            source_name: Name of the source.
            
        Returns:
            Dictionary containing metrics for the source.
        """
        with self._lock:
            if source_name not in self._metrics:
                return {}
            
            metrics = self._metrics[source_name].copy()
            
            # Calculate derived metrics
            if metrics['total_runs'] > 0:
                metrics['success_rate'] = metrics['successful_runs'] / metrics['total_runs']
                metrics['average_duration'] = metrics['total_duration'] / metrics['total_runs']
            else:
                metrics['success_rate'] = 0.0
                metrics['average_duration'] = 0.0
            
            if metrics['successful_runs'] > 0:
                metrics['average_items'] = metrics['total_items'] / metrics['successful_runs']
            else:
                metrics['average_items'] = 0
            
            return metrics
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated metrics for all sources.
        
        Returns:
            Dictionary containing aggregated metrics.
        """
        with self._lock:
            all_sources = {}
            total_runs = 0
            total_successful = 0
            total_failed = 0
            total_items = 0
            
            for source_name in self._metrics:
                source_metrics = self.get_source_metrics(source_name)
                all_sources[source_name] = source_metrics
                
                total_runs += source_metrics.get('total_runs', 0)
                total_successful += source_metrics.get('successful_runs', 0)
                total_failed += source_metrics.get('failed_runs', 0)
                total_items += source_metrics.get('total_items', 0)
            
            # Calculate overall metrics
            overall_success_rate = total_successful / total_runs if total_runs > 0 else 0.0
            
            return {
                'sources': all_sources,
                'summary': {
                    'total_sources': len(self._metrics),
                    'total_runs': total_runs,
                    'total_successful': total_successful,
                    'total_failed': total_failed,
                    'total_items_cached': total_items,
                    'overall_success_rate': overall_success_rate
                }
            }
    
    def reset_metrics(self, source_name: Optional[str] = None) -> None:
        """
        Reset metrics for a source or all sources.
        
        Args:
            source_name: Name of source to reset, or None to reset all.
        """
        with self._lock:
            if source_name:
                if source_name in self._metrics:
                    del self._metrics[source_name]
            else:
                self._metrics.clear()
