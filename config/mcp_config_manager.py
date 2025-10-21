"""
MCP 配置管理器
负责加载和管理 MCP 服务器配置
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP 服务器配置"""
    name: str
    type: str  # stdio, http, sse
    command: Optional[str] = None  # stdio类型必需
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None  # http/sse类型必需
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        验证配置有效性
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self.name:
            return False, "服务器名称不能为空"
        
        if self.type not in ['stdio', 'http', 'sse']:
            return False, f"服务器 {self.name} 使用不支持的类型: {self.type}"
        
        # stdio 类型需要 command
        if self.type == 'stdio':
            if not self.command:
                return False, f"服务器 {self.name} (stdio类型) 缺少 command 配置"
            
            if not isinstance(self.args, list):
                return False, f"服务器 {self.name} 的 args 必须是列表"
            
            if not isinstance(self.env, dict):
                return False, f"服务器 {self.name} 的 env 必须是字典"
        
        # http/sse 类型需要 url
        elif self.type in ['http', 'sse']:
            if not self.url:
                return False, f"服务器 {self.name} ({self.type}类型) 缺少 url 配置"
        
        return True, None


class MCPConfigManager:
    """MCP 配置管理器"""
    
    # 智能体与 MCP 工具的映射关系
    AGENT_TOOLS_MAPPING = {
        'hotspot': [
            'daily-hot-mcp'   # 只使用每日热点新闻聚合服务（30+平台），速度更快
        ],
        'analysis': [],  # 暂时不使用 MCP 工具，加快速度
        'content': []    # 主要使用 LLM 能力生成文本内容
    }
    
    def __init__(self, config_path: str = "config/mcp_servers.json"):
        """
        初始化 MCP 配置管理器
        
        Args:
            config_path: MCP 配置文件路径
        """
        self.config_path = config_path
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """
        从 JSON 文件加载 MCP 服务器配置
        
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON 格式错误
            ValueError: 配置验证失败
        """
        # 检查文件是否存在
        if not os.path.exists(self.config_path):
            error_msg = f"MCP 配置文件不存在: {self.config_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            # 读取并解析 JSON 文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证配置文件结构
            if 'mcpServers' not in config:
                raise ValueError("配置文件缺少 'mcpServers' 字段")
            
            if not isinstance(config['mcpServers'], dict):
                raise ValueError("'mcpServers' 必须是字典类型")
            
            # 加载每个服务器配置
            loaded_count = 0
            for name, server_config in config['mcpServers'].items():
                try:
                    # 只加载激活的服务器
                    if not server_config.get('isActive', True):
                        logger.debug(f"跳过未激活的服务器: {name}")
                        continue
                    
                    # 验证必需字段（根据类型不同）
                    server_type = server_config.get('type', 'stdio')
                    if server_type == 'stdio' and 'command' not in server_config:
                        logger.error(f"服务器 {name} (stdio类型) 缺少 'command' 字段")
                        continue
                    elif server_type in ['http', 'sse'] and 'url' not in server_config:
                        logger.error(f"服务器 {name} ({server_type}类型) 缺少 'url' 字段")
                        continue
                    
                    # 处理环境变量替换
                    env = self._process_env_vars(server_config.get('env', {}))
                    
                    # 创建服务器配置对象
                    server = MCPServerConfig(
                        name=server_config.get('name', name),
                        type=server_type,
                        command=server_config.get('command'),  # http/sse类型可以为None
                        args=server_config.get('args', []),
                        env=env,
                        url=server_config.get('url'),  # stdio类型可以为None
                        is_active=server_config.get('isActive', True)
                    )
                    
                    # 验证配置
                    is_valid, error_msg = server.validate()
                    if not is_valid:
                        logger.error(f"服务器配置验证失败: {error_msg}")
                        continue
                    
                    self.servers[name] = server
                    loaded_count += 1
                    logger.debug(f"已加载服务器配置: {name}")
                    
                except Exception as e:
                    logger.error(f"加载服务器 {name} 配置失败: {e}")
                    continue
            
            if loaded_count == 0:
                logger.warning("未加载任何 MCP 服务器配置")
            else:
                logger.info(f"成功加载 {loaded_count} 个 MCP 服务器配置")
            
        except json.JSONDecodeError as e:
            error_msg = f"MCP 配置文件 JSON 格式错误: {e}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"加载 MCP 配置失败: {e}"
            logger.error(error_msg)
            raise
    
    def _process_env_vars(self, env: Dict[str, str]) -> Dict[str, str]:
        """
        处理环境变量替换，支持 ${VAR_NAME} 和 $VAR_NAME 格式
        
        Args:
            env: 环境变量字典，值可能包含环境变量引用
            
        Returns:
            处理后的环境变量字典
        """
        processed_env = {}
        
        # 正则表达式匹配 ${VAR_NAME} 或 $VAR_NAME
        env_var_pattern = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)')
        
        for key, value in env.items():
            if not isinstance(value, str):
                processed_env[key] = value
                continue
            
            # 查找所有环境变量引用
            def replace_env_var(match):
                var_name = match.group(1) or match.group(2)
                env_value = os.getenv(var_name)
                
                if env_value is None:
                    logger.warning(f"环境变量 {var_name} 未设置，保持原值")
                    return match.group(0)
                
                return env_value
            
            # 替换所有环境变量引用
            processed_value = env_var_pattern.sub(replace_env_var, value)
            processed_env[key] = processed_value
        
        return processed_env
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """
        获取指定的 MCP 服务器配置
        
        Args:
            name: 服务器名称
            
        Returns:
            服务器配置，如果不存在则返回 None
        """
        return self.servers.get(name)
    
    def get_all_servers(self) -> Dict[str, MCPServerConfig]:
        """获取所有 MCP 服务器配置"""
        return self.servers
    
    def get_tools_for_agent(self, agent_name: str) -> List[str]:
        """
        获取指定智能体可用的 MCP 工具列表
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            MCP 工具名称列表
        """
        tool_names = self.AGENT_TOOLS_MAPPING.get(agent_name, [])
        
        if not tool_names:
            logger.warning(f"智能体 {agent_name} 未配置任何工具")
            return []
        
        # 过滤出已配置且激活的工具
        available_tools = [
            name for name in tool_names
            if name in self.servers and self.servers[name].is_active
        ]
        
        if len(available_tools) < len(tool_names):
            missing = set(tool_names) - set(available_tools)
            logger.warning(f"智能体 {agent_name} 的部分工具未配置或未激活: {missing}")
        
        logger.info(f"智能体 {agent_name} 可用工具: {available_tools}")
        return available_tools
    
    def get_tool_configs_for_agent(self, agent_name: str) -> List[MCPServerConfig]:
        """
        获取指定智能体可用的 MCP 工具配置对象列表
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            MCP 工具配置对象列表
        """
        tool_names = self.get_tools_for_agent(agent_name)
        return [self.servers[name] for name in tool_names if name in self.servers]
    
    def add_tool_to_agent(self, agent_name: str, tool_name: str) -> bool:
        """
        动态添加工具到智能体
        
        Args:
            agent_name: 智能体名称
            tool_name: 工具名称
            
        Returns:
            是否添加成功
        """
        # 检查工具是否存在
        if tool_name not in self.servers:
            logger.error(f"工具 {tool_name} 不存在")
            return False
        
        # 检查工具是否激活
        if not self.servers[tool_name].is_active:
            logger.error(f"工具 {tool_name} 未激活")
            return False
        
        # 初始化智能体工具列表（如果不存在）
        if agent_name not in self.AGENT_TOOLS_MAPPING:
            self.AGENT_TOOLS_MAPPING[agent_name] = []
        
        # 检查工具是否已存在
        if tool_name in self.AGENT_TOOLS_MAPPING[agent_name]:
            logger.warning(f"工具 {tool_name} 已存在于智能体 {agent_name}")
            return False
        
        # 添加工具
        self.AGENT_TOOLS_MAPPING[agent_name].append(tool_name)
        logger.info(f"已将工具 {tool_name} 添加到智能体 {agent_name}")
        return True
    
    def remove_tool_from_agent(self, agent_name: str, tool_name: str) -> bool:
        """
        从智能体移除工具
        
        Args:
            agent_name: 智能体名称
            tool_name: 工具名称
            
        Returns:
            是否移除成功
        """
        if agent_name not in self.AGENT_TOOLS_MAPPING:
            logger.error(f"智能体 {agent_name} 不存在")
            return False
        
        if tool_name not in self.AGENT_TOOLS_MAPPING[agent_name]:
            logger.warning(f"工具 {tool_name} 不在智能体 {agent_name} 的工具列表中")
            return False
        
        self.AGENT_TOOLS_MAPPING[agent_name].remove(tool_name)
        logger.info(f"已从智能体 {agent_name} 移除工具 {tool_name}")
        return True
    
    def set_tools_for_agent(self, agent_name: str, tool_names: List[str]) -> bool:
        """
        设置智能体的工具列表（覆盖原有配置）
        
        Args:
            agent_name: 智能体名称
            tool_names: 工具名称列表
            
        Returns:
            是否设置成功
        """
        # 验证所有工具是否存在且激活
        invalid_tools = []
        for tool_name in tool_names:
            if tool_name not in self.servers:
                invalid_tools.append(f"{tool_name} (不存在)")
            elif not self.servers[tool_name].is_active:
                invalid_tools.append(f"{tool_name} (未激活)")
        
        if invalid_tools:
            logger.error(f"以下工具无效: {', '.join(invalid_tools)}")
            return False
        
        # 设置工具列表
        self.AGENT_TOOLS_MAPPING[agent_name] = tool_names.copy()
        logger.info(f"已设置智能体 {agent_name} 的工具列表: {tool_names}")
        return True
    
    def get_agent_tool_mapping(self) -> Dict[str, List[str]]:
        """
        获取完整的智能体工具映射
        
        Returns:
            智能体工具映射字典
        """
        return self.AGENT_TOOLS_MAPPING.copy()
    
    def list_agents(self) -> List[str]:
        """
        列出所有已配置的智能体
        
        Returns:
            智能体名称列表
        """
        return list(self.AGENT_TOOLS_MAPPING.keys())
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        验证 MCP 配置完整性
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查是否加载了服务器配置
        if not self.servers:
            errors.append("未加载任何 MCP 服务器配置")
            logger.error(errors[0])
            return False, errors
        
        # 验证每个服务器配置
        for name, server in self.servers.items():
            is_valid, error_msg = server.validate()
            if not is_valid:
                errors.append(error_msg)
                logger.error(error_msg)
        
        # 验证智能体工具映射
        for agent_name, tool_names in self.AGENT_TOOLS_MAPPING.items():
            for tool_name in tool_names:
                if tool_name not in self.servers:
                    warning = f"智能体 {agent_name} 需要的工具 {tool_name} 未配置"
                    logger.warning(warning)
                elif not self.servers[tool_name].is_active:
                    warning = f"智能体 {agent_name} 需要的工具 {tool_name} 未激活"
                    logger.warning(warning)
        
        if errors:
            logger.error(f"MCP 配置验证失败，发现 {len(errors)} 个错误")
            return False, errors
        
        logger.info("MCP 配置验证通过")
        return True, []
    
    def reload(self):
        """
        重新加载配置
        
        Raises:
            Exception: 重新加载失败时抛出异常
        """
        try:
            self.servers.clear()
            self._load_config()
            logger.info("MCP 配置已重新加载")
        except Exception as e:
            logger.error(f"重新加载 MCP 配置失败: {e}")
            raise
    
    def get_server_count(self) -> int:
        """获取已加载的服务器数量"""
        return len(self.servers)
    
    def get_active_server_count(self) -> int:
        """获取激活的服务器数量"""
        return sum(1 for server in self.servers.values() if server.is_active)
    
    def list_servers(self) -> List[str]:
        """列出所有服务器名称"""
        return list(self.servers.keys())
    
    def list_active_servers(self) -> List[str]:
        """列出所有激活的服务器名称"""
        return [name for name, server in self.servers.items() if server.is_active]
    
    def export_config(self, output_path: str):
        """
        导出配置到 JSON 文件
        
        Args:
            output_path: 输出文件路径
        """
        try:
            config = {
                'mcpServers': {
                    name: server.to_dict()
                    for name, server in self.servers.items()
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已导出到: {output_path}")
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            raise
