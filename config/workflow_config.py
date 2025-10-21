"""
工作流配置模块
定义多智能体工作流的配置参数
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class WorkflowConfig:
    """工作流配置类"""
    # 执行配置
    max_parallel_workflows: int = 3  # 最大并行工作流数量
    timeout_seconds: int = 300  # 单个工作流超时时间（秒）
    retry_attempts: int = 2  # 重试次数

    # 输出配置
    output_dir: str = "output/workflows"
    save_intermediate_results: bool = True  # 保存中间结果
    export_formats: List[str] = None  # 导出格式 ['json', 'txt', 'html']

    # 日志配置
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/workflow.log"

    # 智能体配置
    enable_hotspot_agent: bool = True
    enable_analysis_agent: bool = True
    enable_content_agent: bool = True

    # 性能配置
    enable_caching: bool = True  # 启用结果缓存
    cache_dir: str = "cache/workflows"

    # 发布/平台配置
    dry_run: bool = True  # 是否仅本地导出（不调用平台API）
    enabled_platforms: List[str] = field(default_factory=lambda: [
        "wechat", "weibo", "bilibili"
    ])
    style_default: str = "news"  # 默认风格 preset key（见 style_presets.json）
    style_presets_path: str = "config/style_presets.json"
    platform_guidelines_path: str = "config/platform_guidelines.json"

    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ['json']


# 默认配置实例
default_config = WorkflowConfig()


def get_workflow_config() -> WorkflowConfig:
    """获取工作流配置（支持环境变量覆盖）"""
    config = WorkflowConfig()

    # 从环境变量读取配置
    config.max_parallel_workflows = int(os.getenv(
        'WORKFLOW_MAX_PARALLEL', config.max_parallel_workflows
    ))
    config.timeout_seconds = int(os.getenv(
        'WORKFLOW_TIMEOUT', config.timeout_seconds
    ))
    config.retry_attempts = int(os.getenv(
        'WORKFLOW_RETRY_ATTEMPTS', config.retry_attempts
    ))
    config.output_dir = os.getenv(
        'WORKFLOW_OUTPUT_DIR', config.output_dir
    )
    config.save_intermediate_results = os.getenv(
        'WORKFLOW_SAVE_INTERMEDIATE', 'true'
    ).lower() == 'true'

    config.log_level = os.getenv(
        'WORKFLOW_LOG_LEVEL', config.log_level
    )
    config.log_to_file = os.getenv(
        'WORKFLOW_LOG_TO_FILE', 'true'
    ).lower() == 'true'

    config.enable_caching = os.getenv(
        'WORKFLOW_ENABLE_CACHING', 'true'
    ).lower() == 'true'

    # 平台/风格相关
    config.dry_run = os.getenv('WORKFLOW_DRY_RUN', 'true').lower() == 'true'

    platforms_env = os.getenv('WORKFLOW_ENABLED_PLATFORMS')
    if platforms_env:
        config.enabled_platforms = [p.strip() for p in platforms_env.split(',') if p.strip()]

    config.style_default = os.getenv('WORKFLOW_STYLE_DEFAULT', config.style_default)

    config.style_presets_path = os.getenv(
        'WORKFLOW_STYLE_PRESETS_PATH', config.style_presets_path
    )
    config.platform_guidelines_path = os.getenv(
        'WORKFLOW_PLATFORM_GUIDELINES_PATH', config.platform_guidelines_path
    )

    return config


def create_workflow_config(
    max_parallel: int = None,
    timeout: int = None,
    output_dir: str = None,
    **kwargs
) -> WorkflowConfig:
    """创建自定义配置"""
    config = get_workflow_config()

    if max_parallel is not None:
        config.max_parallel_workflows = max_parallel
    if timeout is not None:
        config.timeout_seconds = timeout
    if output_dir is not None:
        config.output_dir = output_dir

    # 更新其他参数
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config


# 预定义配置模板
workflow_templates = {
    "fast": WorkflowConfig(
        max_parallel_workflows=1,
        timeout_seconds=180,
        enable_caching=False,
        save_intermediate_results=False
    ),

    "standard": WorkflowConfig(
        max_parallel_workflows=2,
        timeout_seconds=300,
        enable_caching=True,
        save_intermediate_results=True,
        export_formats=['json', 'txt']
    ),

    "comprehensive": WorkflowConfig(
        max_parallel_workflows=5,
        timeout_seconds=600,
        enable_caching=True,
        save_intermediate_results=True,
        export_formats=['json', 'txt', 'html']
    ),

    "debug": WorkflowConfig(
        max_parallel_workflows=1,
        timeout_seconds=120,
        log_level="DEBUG",
        enable_caching=False,
        save_intermediate_results=True
    )
}


def get_template_config(template_name: str) -> WorkflowConfig:
    """获取模板配置"""
    if template_name not in workflow_templates:
        available = list(workflow_templates.keys())
        raise ValueError(f"未知的配置模板: {template_name}。可用模板: {available}")

    return workflow_templates[template_name]


def print_config_summary(config: WorkflowConfig):
    """打印配置摘要"""
    print("工作流配置摘要:")
    print(f"  并行工作流数量: {config.max_parallel_workflows}")
    print(f"  超时时间: {config.timeout_seconds}秒")
    print(f"  重试次数: {config.retry_attempts}")
    print(f"  输出目录: {config.output_dir}")
    print(f"  保存中间结果: {config.save_intermediate_results}")
    print(f"  导出格式: {', '.join(config.export_formats)}")
    print(f"  日志级别: {config.log_level}")
    print(f"  启用缓存: {config.enable_caching}")
    if config.enable_caching:
        print(f"  缓存目录: {config.cache_dir}")
    print(f"  干跑模式(dry_run): {config.dry_run}")
    print(f"  启用的平台: {', '.join(config.enabled_platforms)}")
    print(f"  默认风格: {config.style_default}")
    print(f"  风格预设文件: {config.style_presets_path}")
    print(f"  平台规范文件: {config.platform_guidelines_path}")

    enabled_agents = []
    if config.enable_hotspot_agent:
        enabled_agents.append("热点获取")
    if config.enable_analysis_agent:
        enabled_agents.append("内容分析")
    if config.enable_content_agent:
        enabled_agents.append("内容生成")

    print(f"  启用的智能体: {', '.join(enabled_agents)}")


# 配置文件加载工具
def _load_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ 配置文件未找到: {path}")
        return None
    except Exception as e:
        print(f"⚠️ 加载配置文件失败 {path}: {e}")
        return None


def load_style_presets(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    cfg = get_workflow_config()
    return _load_json_file(path or cfg.style_presets_path)


def load_platform_guidelines(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    cfg = get_workflow_config()
    return _load_json_file(path or cfg.platform_guidelines_path)


if __name__ == "__main__":
    # 测试配置
    config = get_workflow_config()
    print_config_summary(config)

    print("\n可用配置模板:")
    for name, template in workflow_templates.items():
        print(f"  {name}: 并行{template.max_parallel_workflows}, 超时{template.timeout_seconds}秒")
