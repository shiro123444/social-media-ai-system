"""
工作流监控和管理工具
提供工作流执行监控、统计和错误处理功能
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import threading
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 仅用于类型检查，避免运行时循环导入
    from agents.workflow_coordinator import WorkflowResult

logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """工作流监控器"""

    def __init__(self):
        self.stats = {
            "total_workflows": 0,
            "completed_workflows": 0,
            "failed_workflows": 0,
            "running_workflows": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "start_time": datetime.now(),
            "last_update": datetime.now()
        }

        self.workflow_history: List[Dict[str, Any]] = []
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.error_counts: Dict[str, int] = defaultdict(int)

        # 线程安全
        self._lock = threading.Lock()

    def start_workflow(self, hotspot_id: str):
        """开始工作流"""
        with self._lock:
            self.stats["total_workflows"] += 1
            self.stats["running_workflows"] += 1
            self.stats["last_update"] = datetime.now()

            self.active_workflows[hotspot_id] = {
                "start_time": datetime.now(),
                "status": "running"
            }

            logger.info(f"工作流 {hotspot_id} 开始执行")

    def complete_workflow(self, result: 'WorkflowResult'):
        """完成工作流"""
        with self._lock:
            hotspot_id = result.hotspot_id

            if hotspot_id in self.active_workflows:
                start_time = self.active_workflows[hotspot_id]["start_time"]
                execution_time = result.execution_time or 0.0

                # 更新统计
                self.stats["running_workflows"] -= 1
                if result.status == "completed":
                    self.stats["completed_workflows"] += 1
                else:
                    self.stats["failed_workflows"] += 1

                self.stats["total_execution_time"] += execution_time
                self.stats["average_execution_time"] = (
                    self.stats["total_execution_time"] / self.stats["completed_workflows"]
                    if self.stats["completed_workflows"] > 0 else 0.0
                )
                self.stats["last_update"] = datetime.now()

                # 记录错误
                if result.errors:
                    for error in result.errors:
                        error_type = self._categorize_error(error)
                        self.error_counts[error_type] += 1

                # 保存到历史记录
                history_entry = {
                    "hotspot_id": hotspot_id,
                    "status": result.status,
                    "execution_time": execution_time,
                    "hotspots_count": len(result.hotspots),
                    "has_analysis": result.analysis is not None,
                    "platforms_count": len(result.contents),
                    "errors": result.errors,
                    "timestamp": result.timestamp
                }
                self.workflow_history.append(history_entry)

                # 移除活跃工作流
                del self.active_workflows[hotspot_id]

                logger.info(f"工作流 {hotspot_id} 执行完成，状态: {result.status}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            stats_copy = self.stats.copy()
            stats_copy["uptime"] = str(datetime.now() - stats_copy["start_time"])
            stats_copy["success_rate"] = (
                self.stats["completed_workflows"] / self.stats["total_workflows"] * 100
                if self.stats["total_workflows"] > 0 else 0.0
            )
            stats_copy["active_workflows"] = list(self.active_workflows.keys())
            return stats_copy

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的历史记录"""
        with self._lock:
            return self.workflow_history[-limit:] if self.workflow_history else []

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        with self._lock:
            return dict(self.error_counts)

    def _categorize_error(self, error: str) -> str:
        """对错误进行分类"""
        error_lower = error.lower()

        if "timeout" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "network" in error_lower:
            return "network"
        elif "mcp" in error_lower or "tool" in error_lower:
            return "tool_error"
        elif "json" in error_lower or "parse" in error_lower:
            return "parsing_error"
        elif "validation" in error_lower:
            return "validation_error"
        else:
            return "other"

    def save_stats_to_file(self, filepath: str):
        """保存统计信息到文件"""
        try:
            stats = self.get_stats()
            stats["history"] = self.workflow_history
            stats["error_summary"] = self.get_error_summary()
            stats["export_time"] = datetime.now().isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"统计信息已保存到: {filepath}")

        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")


class WorkflowManager:
    """工作流管理器"""

    def __init__(self, monitor: WorkflowMonitor):
        self.monitor = monitor
        self.workflows_dir = Path("output/workflows")
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def list_completed_workflows(self) -> List[str]:
        """列出已完成的工作流"""
        try:
            workflow_files = list(self.workflows_dir.glob("workflow_*.json"))
            hotspot_ids = []

            for file_path in workflow_files:
                try:
                    # 从文件名提取热点ID
                    filename = file_path.stem  # workflow_hotspot123_20240101_120000
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        hotspot_id = parts[1]
                        hotspot_ids.append(hotspot_id)
                except:
                    continue

            return list(set(hotspot_ids))  # 去重

        except Exception as e:
            logger.error(f"列出工作流失败: {e}")
            return []

    def get_workflow_result(self, hotspot_id: str) -> Optional['WorkflowResult']:
        """获取工作流结果"""
        try:
            # 延迟导入以避免循环依赖
            from agents.workflow_coordinator import WorkflowResult  # type: ignore
            # 查找最新的结果文件
            pattern = f"workflow_{hotspot_id}_*.json"
            workflow_files = list(self.workflows_dir.glob(pattern))

            if not workflow_files:
                return None

            # 按修改时间排序，取最新的
            latest_file = max(workflow_files, key=lambda f: f.stat().st_mtime)

            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 重建 WorkflowResult 对象
            result = WorkflowResult(
                hotspot_id=data["hotspot_id"],
                status=data["status"],
                errors=data.get("errors", []),
                execution_time=data.get("execution_time"),
                timestamp=data["timestamp"]
            )

            # 加载热点数据
            if "hotspots" in data and data["hotspots"]:
                from agents.hotspot_agent import Hotspot
                result.hotpots = [Hotspot.from_dict(h) for h in data["hotspots"]]

            # 加载分析数据
            if "analysis" in data and data["analysis"]:
                from agents.analysis_agent import AnalysisReport
                result.analysis = AnalysisReport.from_dict(data["analysis"])

            # 加载内容数据
            if "contents" in data and data["contents"]:
                from agents.content_agent import Content
                result.contents = {
                    platform: Content.from_dict(content_data)
                    for platform, content_data in data["contents"].items()
                }

            return result

        except Exception as e:
            logger.error(f"加载工作流结果失败 {hotspot_id}: {e}")
            return None

    def cleanup_old_results(self, days: int = 30):
        """清理旧的结果文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0

            for file_path in self.workflows_dir.glob("*.json"):
                try:
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                except:
                    continue

            logger.info(f"清理了 {deleted_count} 个旧的工作流结果文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理旧结果失败: {e}")
            return 0

    def generate_report(self, output_file: str):
        """生成工作流执行报告"""
        try:
            stats = self.monitor.get_stats()
            error_summary = self.monitor.get_error_summary()
            recent_history = self.monitor.get_recent_history(20)

            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": stats,
                "error_summary": error_summary,
                "recent_workflows": recent_history,
                "completed_workflows": self.list_completed_workflows()
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"工作流报告已生成: {output_file}")
            return True

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return False


# 全局监控器实例
workflow_monitor = WorkflowMonitor()
workflow_manager = WorkflowManager(workflow_monitor)


def get_monitor() -> WorkflowMonitor:
    """获取全局监控器"""
    return workflow_monitor


def get_manager() -> WorkflowManager:
    """获取全局管理器"""
    return workflow_manager


# 便捷函数
def print_monitor_stats():
    """打印监控统计信息"""
    stats = workflow_monitor.get_stats()
    print("\n=== 工作流监控统计 ===")
    print(f"总工作流数: {stats['total_workflows']}")
    print(f"完成工作流: {stats['completed_workflows']}")
    print(f"失败工作流: {stats['failed_workflows']}")
    print(f"运行中工作流: {stats['running_workflows']}")
    print(f"总执行时间: {stats['total_execution_time']:.2f}秒")
    print(f"平均执行时间: {stats['average_execution_time']:.2f}秒")
    print(f"成功率: {stats['success_rate']:.1f}%")
    print(f"运行时间: {stats['uptime']}")
    print(f"活跃工作流: {stats['active_workflows']}")

    if stats['active_workflows']:
        print("\n活跃工作流详情:")
        for hotspot_id in stats['active_workflows']:
            if hotspot_id in workflow_monitor.active_workflows:
                start_time = workflow_monitor.active_workflows[hotspot_id]['start_time']
                duration = datetime.now() - start_time
                print(f"运行时间: {duration.total_seconds():.1f}秒")


def print_error_summary():
    """打印错误摘要"""
    errors = workflow_monitor.get_error_summary()
    if errors:
        print("\n=== 错误统计 ===")
        for error_type, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
            print(f"{error_type}: {count} 次")
    else:
        print("\n暂无错误记录")


if __name__ == "__main__":
    # 测试监控器
    print("工作流监控器测试")

    # 模拟一些工作流
    monitor = get_monitor()

    # 开始几个工作流
    monitor.start_workflow("test_001")
    monitor.start_workflow("test_002")

    time.sleep(1)  # 模拟执行时间

    # 完成工作流
    result1 = WorkflowResult(
        hotspot_id="test_001",
        status="completed",
        execution_time=2.5,
        hotspots=[],  # 空列表
        contents={}
    )
    monitor.complete_workflow(result1)

    result2 = WorkflowResult(
        hotspot_id="test_002",
        status="failed",
        errors=["网络连接超时"],
        execution_time=1.8
    )
    monitor.complete_workflow(result2)

    # 显示统计
    print_monitor_stats()
    print_error_summary()

    # 保存统计
    monitor.save_stats_to_file("test_monitor_stats.json")
