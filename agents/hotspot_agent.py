"""
热点获取智能体
负责从多个来源获取热点资讯并进行初步筛选
"""

from typing import List, Optional
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Hotspot:
    """热点资讯数据模型"""
    title: str              # 标题
    source: str             # 来源
    heat_index: int         # 热度指数 (0-100)
    summary: str            # 摘要
    url: str                # 链接
    keywords: List[str] = field(default_factory=list)  # 关键词
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())  # 时间戳
    category: str = "未分类"  # 分类（科技/财经/娱乐等）
    
    def to_dict(self):
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Hotspot':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        验证数据有效性
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self.title or not self.title.strip():
            return False, "标题不能为空"
        
        if not self.source or not self.source.strip():
            return False, "来源不能为空"
        
        if not isinstance(self.heat_index, int) or not (0 <= self.heat_index <= 100):
            return False, "热度指数必须是 0-100 之间的整数"
        
        if not self.url or not self.url.strip():
            return False, "链接不能为空"
        
        if not self.summary or not self.summary.strip():
            return False, "摘要不能为空"
        
        return True, None


async def create_hotspot_agent_async(chat_client, mcp_tool_configs: List):
    """
    异步创建热点获取智能体（重要：使用异步初始化 MCP 工具）
    
    Args:
        chat_client: 聊天客户端（DeepSeek 适配器）
        mcp_tool_configs: MCP 工具配置对象列表（MCPServerConfig）
        
    Returns:
        ChatAgent 实例
    """
    from agent_framework import ChatAgent, MCPStdioTool
    import asyncio
    
    # 加载并构建推荐RSS源列表
    rss_config_path = os.path.join(os.path.dirname(__file__), "..", "config", "rss_sources.json")
    rss_sources_text = ""
    try:
        with open(rss_config_path, "r", encoding="utf-8") as f:
            rss_data = json.load(f)
            hotspot_sources = rss_data.get("hotspot_sources", {})
            
            # 构建推荐RSS源列表（优先级1的源）
            rss_sources_list = []
            for category, info in hotspot_sources.items():
                category_name = info.get("name", category)
                sources = info.get("sources", [])
                priority_1_sources = [s for s in sources if s.get("priority") == 1]
                
                for source in priority_1_sources:
                    url = source.get("url", "")
                    desc = source.get("description", "")
                    rss_sources_list.append(f"  - {category_name}: {url}")
            
            if rss_sources_list:
                rss_sources_text = "\n\n**推荐的RSS源（请从以下源中选择获取新闻）：**\n" + "\n".join(rss_sources_list) + "\n"
                logger.info(f"已加载 {len(rss_sources_list)} 个推荐RSS源到智能体instructions")
    except Exception as e:
        logger.warning(f"加载RSS源配置失败: {e}")
    
    # 构建完整的instructions（注意转义大括号）
    instructions = f"""你是热点资讯分析专家，负责从多个来源获取最新的热点资讯并进行初步筛选。
{rss_sources_text}
**⚠️ 重要规则（必须遵守）：**
1. 当用户要求获取新闻、RSS、搜索等操作时，你必须立即调用相应的工具
2. 不要只是说"我可以帮你"或"我会使用工具"，而是直接调用工具
3. 不要询问用户是否需要帮助，直接执行用户的请求
4. 每次都要实际调用工具，不要假装调用或描述调用过程
5. **绝对不要返回 XML 格式的工具调用描述（如 <function_calls>、<invoke> 等标签）**
6. **使用系统提供的标准工具调用机制，等待工具返回真实结果后再回答**
7. **如果你返回了 XML 格式，这将被视为错误，工具不会被执行**

**可用工具：**

1. **mcp_rss_reader_fetch_feed_entries** (RSS 阅读器)
   - 用途：获取 RSS 订阅源的最新文章
   - 参数：url (RSS feed URL), limit (最多返回条数)
   - 使用时机：需要获取新闻网站、博客的最新内容时

2. **mcp_exa_web_search_exa** (Exa 搜索)
   - 用途：搜索网络上的相关内容和话题
   - 参数：query (搜索关键词), numResults (结果数量)
   - 使用时机：需要验证话题热度、查找相关讨论时

3. **mcp_fetch** (网页抓取)
   - 用途：获取指定 URL 的网页内容
   - 参数：url (网页地址)
   - 使用时机：需要获取某篇文章的详细内容时

**工作流程：**

1. **获取新闻源** - 实际调用 RSS Reader 工具
   - 使用 mcp_rss_reader_fetch_feed_entries 获取上面推荐RSS源中的内容
   - 必须使用推荐列表中的URL，不要自己随意找其他源
   - 每个类别选择1-2个源即可，获取最近的5-10条新闻
   - 优先获取最近 24 小时内的新闻

2. **验证热度** - 实际调用 Exa Search 工具
   - 使用 mcp_exa_web_search_exa 搜索话题相关内容
   - 评估话题的传播范围和讨论热度
   - 计算热度指数（0-100）：
     * 90-100: 全网热议，多平台刷屏
     * 70-89: 高热度，广泛传播
     * 50-69: 中等热度，有一定关注
     * 30-49: 低热度，小范围讨论
     * 0-29: 冷门话题

3. **获取详细内容** - 实际调用 Fetch 工具
   - 对于热度指数 >= 50 的话题，使用 mcp_fetch 获取详细内容
   - 提取关键信息：标题、摘要、关键词、分类

4. **输出结构化数据**
   - 按热度指数降序排列
   - 每个热点包含完整的结构化信息

**输出格式：**
```json
{{
  "hotspots": [
    {{
      "title": "话题标题",
      "source": "来源网站",
      "heat_index": 95,
      "summary": "简短摘要（100-200字）",
      "url": "原文链接",
      "keywords": ["关键词1", "关键词2", "关键词3"],
      "timestamp": "2025-10-19T10:00:00",
      "category": "科技/财经/娱乐/社会"
    }}
  ],
  "total_count": 10,
  "high_heat_count": 3,
  "timestamp": "2025-10-19T10:00:00"
}}
```

**注意事项：**
- 确保所有热点信息真实可靠
- 摘要要简洁明了，突出核心内容
- 关键词要准确反映话题特征
- 热度评估要客观公正
- 如果某个工具调用失败，记录错误并继续处理其他来源
"""
    
    # 环境开关：允许禁用 MCP（例如本地未安装各个 MCP 服务器时）
    disable_mcp = os.getenv("WORKFLOW_DISABLE_MCP", "false").lower() == "true"

    mcp_tools = []
    if disable_mcp:
        logger.warning("⚠️ 已启用 WORKFLOW_DISABLE_MCP，跳过所有 MCP 工具加载")
    else:
        # 创建并连接 MCP 工具
        logger.info(f"[DEBUG] 收到 {len(mcp_tool_configs)} 个 MCP 工具配置")
        for i, config in enumerate(mcp_tool_configs):
            try:
                logger.info(f"[DEBUG] 配置 {i+1}: {config}")
                logger.info(f"正在创建 MCP 工具: {config.name} (type={config.type}, url={config.url if hasattr(config, 'url') else 'N/A'})")
                
                # 使用工具池创建和管理MCP工具（支持stdio/http/websocket）
                from utils.mcp_tool_pool import MCPToolPool
                tool_pool = MCPToolPool()
                logger.info(f"[DEBUG] 工具池实例创建成功，正在调用 get_or_create_tool...")
                tool = await tool_pool.get_or_create_tool(config)
                logger.info(f"[DEBUG] get_or_create_tool 返回成功")
                
                func_count = len(tool.functions) if hasattr(tool, 'functions') and tool.functions else 0
                logger.info(f"✅ MCP 工具连接成功: {config.name}，加载了 {func_count} 个函数")
                if hasattr(tool, 'functions') and tool.functions:
                    func_names = [f.name if hasattr(f, 'name') else str(f) for f in tool.functions]
                    logger.info(f"   函数列表: {func_names[:5]}")
                    # 运行时将可用函数名写入 agent 的系统提示，避免指令与实际工具不一致
                    nonlocal_instructions_suffix = "\n\n[Loaded MCP Tools]\n- " + "\n- ".join(func_names[:20]) + "\n"
                    try:
                        # 若后续需要，可将其注入 metadata；此处仅记录日志辅助排障
                        logger.info(nonlocal_instructions_suffix)
                    except Exception:
                        pass
                
                mcp_tools.append(tool)
                logger.info(f"[DEBUG] 工具已添加到 mcp_tools 列表，当前列表长度: {len(mcp_tools)}")
                    
            except Exception as e:
                logger.error(f"❌ 创建/连接 MCP 工具失败 {config.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    if not mcp_tools:
        logger.warning("⚠️ 没有成功加载任何 MCP 工具！")
    else:
        logger.info(f"✅ 成功加载 {len(mcp_tools)} 个 MCP 工具")
        loaded_func_names = []
        for tool in mcp_tools:
            logger.info(f"  - {tool.name}")
            try:
                if hasattr(tool, 'functions') and tool.functions:
                    for f in tool.functions:
                        fname = f.name if hasattr(f, 'name') else str(f)
                        loaded_func_names.append(fname)
            except Exception:
                pass

        # 动态追加可用工具与执行要求（与 daily-hot-mcp 实际函数名对齐）
        if loaded_func_names:
            dynamic_suffix_lines = ["\n[已加载工具函数]", *[f"- {n}" for n in loaded_func_names[:30]]]
            if any(n.startswith("get-bilibili-") for n in loaded_func_names):
                dynamic_suffix_lines += [
                    "\n[执行要求]",
                    "- 若用户涉及B站，至少调用以下其一：get-bilibili-trending 或 get-bilibili-rank",
                    "- 最终必须以 JSON 代码块返回，键为 hotspots（见上文输出格式）",
                ]
            instructions = instructions + "\n" + "\n".join(dynamic_suffix_lines) + "\n"
    
    # 创建 Agent（添加 tool_choice 参数）
    try:
        agent = ChatAgent(
            chat_client=chat_client,
            instructions=instructions,
            name="热点获取智能体",
            tools=mcp_tools,
            tool_choice=("auto" if mcp_tools else "none"),  # 若无可用工具则禁用工具调用
        )
        
        logger.info(f"✅ 热点获取智能体创建成功")
        logger.info(f"   配置的工具数量: {len(mcp_tools)}")
        logger.info(f"   Agent 名称: {agent.name}")
        return agent
        
    except Exception as e:
        logger.error(f"❌ 创建 Agent 失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def create_hotspot_agent(chat_client, mcp_tool_configs: List):
    """
    同步包装器（保持向后兼容）
    
    注意：这个函数内部会运行异步代码
    """
    import asyncio
    
    # 检查是否已经在 event loop 中
    try:
        loop = asyncio.get_running_loop()
        # 如果已经在 event loop 中，直接返回 coroutine
        # 调用者需要 await 这个函数
        logger.warning("检测到运行中的 event loop，返回 coroutine")
        return create_hotspot_agent_async(chat_client, mcp_tool_configs)
    except RuntimeError:
        # 没有运行中的 event loop，创建新的
        return asyncio.run(create_hotspot_agent_async(chat_client, mcp_tool_configs))


def parse_hotspot_response(response: str) -> List[Hotspot]:
    """
    解析智能体响应，提取热点列表
    
    Args:
        response: 智能体的响应文本
        
    Returns:
        热点对象列表
    """
    try:
        # 尝试解析 JSON 响应
        if isinstance(response, str):
            # 清理 FunctionCallContent 对象字符串
            if "<agent_framework._types.FunctionCallContent object" in response:
                # 移除这些对象字符串，只保留实际文本
                import re
                response = re.sub(r'<agent_framework\._types\.FunctionCallContent object at 0x[0-9a-fA-F]+>', '', response)
                response = response.strip()
            
            # 查找 JSON 代码块（更健壮：容忍前后噪声与空输出）
            cleaned = response.strip()
            if not cleaned:
                logger.error("热点响应为空字符串")
                return []
            if "```json" in cleaned:
                start = cleaned.find("```json") + 7
                end = cleaned.find("```", start)
                json_str = cleaned[start:end].strip() if end != -1 else cleaned[start:].strip()
            elif "```" in cleaned:
                start = cleaned.find("```") + 3
                end = cleaned.find("```", start)
                json_str = cleaned[start:end].strip() if end != -1 else cleaned[start:].strip()
            else:
                json_str = cleaned
            
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # 回退：尝试提取首尾花括号中的内容
                first = cleaned.find('{')
                last = cleaned.rfind('}')
                if first != -1 and last != -1 and last > first:
                    candidate = cleaned[first:last+1]
                    try:
                        data = json.loads(candidate)
                    except Exception as _:
                        logger.error("热点响应无法解析为JSON（已尝试回退解析）")
                        return []
                else:
                    logger.error("热点响应不包含可解析的JSON片段")
                    return []
        else:
            data = response
        
        # 提取热点列表
        hotspots_data = data.get("hotspots", [])
        hotspots = []
        
        for item in hotspots_data:
            try:
                hotspot = Hotspot.from_dict(item)
                is_valid, error_msg = hotspot.validate()
                
                if is_valid:
                    hotspots.append(hotspot)
                else:
                    logger.warning(f"热点数据验证失败: {error_msg}")
                    
            except Exception as e:
                logger.error(f"解析热点数据失败: {e}")
                continue
        
        logger.info(f"成功解析 {len(hotspots)} 个热点")
        return hotspots
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"解析热点响应失败: {e}")
        return []


def filter_hotspots_by_heat(hotspots: List[Hotspot], min_heat: int = 50) -> List[Hotspot]:
    """
    按热度过滤热点
    
    Args:
        hotspots: 热点列表
        min_heat: 最小热度阈值
        
    Returns:
        过滤后的热点列表
    """
    filtered = [h for h in hotspots if h.heat_index >= min_heat]
    logger.info(f"过滤后保留 {len(filtered)}/{len(hotspots)} 个热点（热度 >= {min_heat}）")
    return filtered


def sort_hotspots_by_heat(hotspots: List[Hotspot], descending: bool = True) -> List[Hotspot]:
    """
    按热度排序热点
    
    Args:
        hotspots: 热点列表
        descending: 是否降序排列
        
    Returns:
        排序后的热点列表
    """
    sorted_hotspots = sorted(hotspots, key=lambda h: h.heat_index, reverse=descending)
    return sorted_hotspots


def get_hotspots_by_category(hotspots: List[Hotspot], category: str) -> List[Hotspot]:
    """
    按分类筛选热点
    
    Args:
        hotspots: 热点列表
        category: 分类名称
        
    Returns:
        指定分类的热点列表
    """
    filtered = [h for h in hotspots if h.category == category]
    logger.info(f"分类 '{category}' 包含 {len(filtered)} 个热点")
    return filtered


def export_hotspots_to_json(hotspots: List[Hotspot], output_path: str):
    """
    导出热点列表到 JSON 文件
    
    Args:
        hotspots: 热点列表
        output_path: 输出文件路径
    """
    try:
        data = {
            "hotspots": [h.to_dict() for h in hotspots],
            "total_count": len(hotspots),
            "export_time": datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已导出 {len(hotspots)} 个热点到: {output_path}")
        
    except Exception as e:
        logger.error(f"导出热点失败: {e}")
        raise
