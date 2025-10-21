"""
社交媒体内容生成工作流 - 带 MCP 工具集成
符合 DevUI 发现机制要求
"""
import os
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"✅ 环境变量已从 {env_file} 加载")
except ImportError:
    logger.warning("⚠️ python-dotenv 未安装，跳过 .env 文件加载")

# 导入必要的模块
from agent_framework import SequentialBuilder, MCPStreamableHTTPTool, Executor, handler, WorkflowContext, ChatMessage
from typing_extensions import Never

# 延迟导入避免初始化错误
def _create_client():
    """延迟创建客户端"""
    try:
        from utils.deepseek_chat_client import create_deepseek_client
        client = create_deepseek_client()
        logger.info(f"✅ DeepSeek 客户端创建成功")
        return client
    except Exception as e:
        # 如果创建失败，使用 OpenAI 客户端作为后备
        logger.warning(f"⚠️ DeepSeek 客户端创建失败，使用 OpenAI 客户端: {e}")
        from agent_framework.openai import OpenAIChatClient
        return OpenAIChatClient(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model_id="deepseek-chat"
        )

# 创建客户端
client = _create_client()

# ✅ 方案 1：使用自定义 Executor 在 workflow 执行时动态创建 MCP 工具
# 参考：https://github.com/microsoft/agent-framework Python MCP 示例
# 关键：在异步 handler 中使用 async with 管理 MCP 工具生命周期

class MCPHotspotExecutor(Executor):
    """在 workflow 执行时动态创建和连接 MCP 工具的 executor"""
    
    def __init__(self, executor_id: str, mcp_url: str, client):
        super().__init__(id=executor_id)
        self.mcp_url = mcp_url
        self.client = client
        logger.info(f"✅ MCPHotspotExecutor 创建: {executor_id}, URL: {mcp_url}")
    
    @handler
    async def fetch_hotspots(self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage], str]) -> None:
        """在异步环境中创建 MCP 工具并获取热点数据
        
        Args:
            messages: 输入的 ChatMessage 列表（来自 workflow 输入）
            ctx: Workflow 上下文，用于发送消息到下游
        """
        # 提取查询文本
        query = ""
        for msg in messages:
            if hasattr(msg, 'text') and msg.text:
                query = msg.text
                break
        
        if not query:
            query = "获取今天的热点资讯"  # 默认查询
        
        logger.info(f"[{self.id}] 开始获取热点: {query}")
        
        try:
            # ✅ 关键：使用 async with 在异步环境中创建和连接 MCP 工具
            async with MCPStreamableHTTPTool(
                name="daily-hot-mcp",
                url=self.mcp_url,
                load_tools=True
            ) as mcp_tool:
                logger.info(f"[{self.id}] MCP 工具已连接")
                
                # 创建临时 agent 使用 MCP 工具
                temp_agent = self.client.create_agent(
                    name="temp_hotspot_agent",
                    instructions=HOTSPOT_INSTRUCTIONS,
                    tools=[mcp_tool]
                )
                
                # 执行查询
                result = await temp_agent.run(query)
                result_text = result.text if hasattr(result, 'text') else str(result)
                
                logger.info(f"[{self.id}] 获取成功，结果长度: {len(result_text)}")
                
                # ✅ 发送完整数据到下一个 executor
                from agent_framework import Role, TextContent
                response_msg = ChatMessage(
                    role=Role.ASSISTANT,
                    contents=[TextContent(text=result_text)]
                )
                await ctx.send_message([response_msg])
                
                # ✅ 同时输出中间结果给用户
                summary = f"📊 **步骤 1: 热点数据获取完成**\n\n获取了 {len(result_text)} 字符的热点数据\n\n预览：\n```\n{result_text[:500]}\n```\n\n---\n"
                await ctx.yield_output(summary)
                
        except Exception as e:
            logger.error(f"[{self.id}] MCP 工具执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 发送错误信息
            from agent_framework import Role, TextContent
            error_result = '{"hotspots": [], "error": "' + str(e) + '"}'
            error_msg = ChatMessage(role=Role.ASSISTANT, contents=[TextContent(text=error_result)])
            await ctx.send_message([error_msg])

# 定义 Agent 指令
HOTSPOT_INSTRUCTIONS = """你是数据转换专家。你的任务是调用 MCP 工具并**原样输出**工具返回的数据。

**严格要求**：
1. 调用 MCP 工具（get-bilibili-trending, get-weibo-trending 等）
2. **逐字逐句**复制工具返回的数据
3. **禁止修改、美化、改写任何标题或内容**
4. **禁止编造数据**

**示例**：
如果工具返回：
```
[{"title": "文科毕业生9.9吃一顿", "view_count": 2547820}]
```

你必须输出：
```json
{
  "hotspots": [
    {"title": "文科毕业生9.9吃一顿", "heat_index": 2547820, "source": "B站"}
  ]
}
```

**禁止输出**：
```json
{
  "hotspots": [
    {"title": "大学生低价美食探店", ...}  // ❌ 改写了标题
  ]
}
```

**输出格式**：
```json
{
  "hotspots": [
    {
      "title": "【原始标题，一字不改】",
      "url": "原始链接",
      "heat_index": 原始数值,
      "source": "来源平台",
      "author": "原始作者名",
      "view_count": 原始播放量,
      "like_count": 原始点赞数,
      "pubdate": 原始时间戳
    }
  ]
}
```

**记住**：你是数据转换器，不是内容创作者。保持数据原样！
"""

ANALYSIS_INSTRUCTIONS = """你是数据分析专家。整理热点数据并提供深度分析。

**关键要求**：
1. **使用对话历史中的真实数据**：上一条 assistant 消息包含 hotspots JSON 数据
2. **逐条保留原始标题**：不要修改、美化或改写任何标题
3. **只输出 JSON 字符串**

**任务流程**：
1. 读取上一条 assistant 消息中的 hotspots 数据
2. 提取每条热点的原始信息（title, source, heat_index, url 等）
3. 按类别分类（科技、娱乐、社会、财经等）
4. 分析趋势和推荐

**输出格式**：
```json
{
  "date": "2025-10-21",
  "total_count": 实际热点数量,
  "summary": "基于实际数据的概述",
  "categories": {
    "社会": [
      {
        "title": "【保留原始标题，一字不改】",
        "source": "来源",
        "heat_index": 实际数值,
        "summary": "摘要",
        "url": "链接"
      }
    ],
    "科技": [...]
  },
  "top_trends": [
    {"topic": "基于实际数据的话题", "count": 实际数量, "description": "描述"}
  ],
  "recommendations": [
    {"title": "【原始标题】", "reason": "推荐理由", "priority": "high"}
  ]
}
```

**重要**：
- ✅ 保留原始标题（例如："投保52万奔驰车被烧毁获赔50万"）
- ✅ 使用真实的热度数值
- ❌ 不要编造不存在的热点
- ❌ 不要修改标题
- ❌ 不要使用 markdown 代码块
"""

XIAOHONGSHU_INSTRUCTIONS = """你是小红书内容创作专家。基于热点分析生成小红书爆款文案。

**关键要求**：
1. **必须使用上一条 assistant 消息中的分析数据**
2. **必须只输出纯 JSON 字符串，不要任何其他文字**
3. **不要使用 markdown 代码块（不要 ```json）**
4. **不要编造内容，使用真实的热点标题**

**数据来源**：
- 上一条 assistant 消息包含热点分析的 JSON 数据
- 从中提取 TOP 3-5 个热点
- 使用**原始标题**，不要改写

**小红书特点：**
- 标题要有吸引力，使用emoji
- 内容要真实、接地气
- 多用短句，易读
- 适当使用emoji增加活力
- 结尾要有互动引导

**创作步骤：**
1. **读取上一条消息**：提取热点分析数据
2. **选择热点**：挑选 3-5 个最热的话题
3. **创作文案**：基于真实热点生成小红书内容
4. **保持真实**：使用原始标题，不编造

**输出格式（必须是纯 JSON，不要 markdown）：**
{
  "title": "🔥标题（15-20字，包含emoji，基于真实热点）",
  "content": "正文内容（500-800字）必须包含：开头（吸引注意）、主体（3-5个真实热点，使用原始标题）、结尾（互动引导）",
  "tags": ["#标签1", "#标签2", "#标签3"],
  "cover_suggestion": "封面图建议描述",
  "source_hotspots": ["热点1原始标题", "热点2原始标题", "热点3原始标题"]
}

**示例（注意：直接输出 JSON，不要 markdown 代码块）：**
假设分析数据中有：
- "投保52万奔驰被追尾几乎报废，保司只赔24万"
- "徐悲鸿《奔马图》起拍价4762万暂无人出价"

则直接输出：
{"title": "🔥今日热搜！奔驰理赔争议+名画流拍", "content": "姐妹们！今天的热搜真的太炸了！😱\\n\\n📌 投保52万奔驰被追尾几乎报废，保司只赔24万\\n💡 这个理赔方式合理吗？大家怎么看？\\n\\n📌 徐悲鸿《奔马图》起拍价4762万暂无人出价\\n💡 艺术品市场遇冷了吗？\\n\\n你们怎么看？评论区聊聊！👇", "tags": ["#今日热点", "#热搜", "#必看"], "cover_suggestion": "热点话题拼图，配色鲜艳", "source_hotspots": ["投保52万奔驰被追尾几乎报废，保司只赔24万", "徐悲鸿《奔马图》起拍价4762万暂无人出价"]}

**重要**：
- ✅ 必须从上一条消息中读取分析数据
- ✅ 使用真实的热点标题
- ✅ 在 source_hotspots 中列出使用的热点
- ✅ 直接输出 JSON 对象，第一个字符必须是 {
- ❌ 不要编造不存在的热点
- ❌ 绝对不要使用 markdown 代码块（```json 或 ```）
- ❌ 不要在 JSON 前后添加任何说明文字
"""

# 创建文本转换 Executor，确保 workflow 中传递的消息是纯文本
class TextOnlyConversation(Executor):
    """确保对话中只包含纯文本，避免 TextContent 序列化问题"""
    
    def __init__(self, executor_id: str):
        super().__init__(id=executor_id)
    
    def _clean_markdown(self, text: str) -> str:
        """清理 markdown 代码块，提取纯 JSON"""
        import re
        
        # 移除 markdown 代码块标记
        # 匹配 ```json ... ``` 或 ``` ... ```
        cleaned = re.sub(r'```(?:json)?\s*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL)
        
        # 移除前后空白
        cleaned = cleaned.strip()
        
        return cleaned
    
    @handler
    async def convert(self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]) -> None:
        """
        将 ChatMessage 转换为 DevUI 可以正确序列化的格式
        
        关键：不再创建新的 ChatMessage，而是直接发送提取的文本字符串。
        DevUI 会自动将字符串包装为正确的消息格式。
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[{self.id}] 收到 {len(messages)} 条消息，开始转换...")
        
        # 提取所有消息的文本内容
        all_text_parts = []
        
        for i, msg in enumerate(messages):
            # 使用 ChatMessage.text 属性，它会自动提取所有文本内容
            text = msg.text if hasattr(msg, 'text') else ""
            
            if text:
                # 清理 markdown 代码块
                cleaned_text = self._clean_markdown(text)
                all_text_parts.append(cleaned_text)
                logger.debug(f"[{self.id}] 消息 {i}: 提取文本，长度={len(cleaned_text)}")
            else:
                logger.warning(f"[{self.id}] 消息 {i}: 无文本内容，跳过")
        
        # 合并所有文本（如果有多条消息）
        if all_text_parts:
            combined_text = "\n\n".join(all_text_parts)
            logger.info(f"[{self.id}] 转换完成，合并文本长度={len(combined_text)}")
            
            # 直接发送纯文本字符串，让框架自动包装
            # 这样 DevUI 就能正确处理它
            await ctx.send_message(combined_text)
        else:
            logger.warning(f"[{self.id}] 没有提取到任何文本内容")
            # 发送空消息以维持 workflow 流程
            await ctx.send_message("")



# 创建 Agents 和 Executors
logger.info("正在创建 Agents 和 Executors...")

# ✅ 使用自定义 Executor 替代直接绑定 MCP 工具的 Agent
mcp_url = os.getenv("DAILY_HOT_MCP_URL", "http://localhost:8000/mcp")
hotspot_executor = MCPHotspotExecutor(
    executor_id="mcp_hotspot_executor",
    mcp_url=mcp_url,
    client=client
)
logger.info(f"✅ Hotspot Executor 创建完成")

# ✅ 创建带有 think-tool 的 Analysis Executor（使用 stdio MCP）
class AnalysisExecutor(Executor):
    """带有 think-tool 的分析 executor"""
    
    def __init__(self, executor_id: str, client):
        super().__init__(id=executor_id)
        self.client = client
        logger.info(f"✅ AnalysisExecutor 创建: {executor_id}")
    
    @handler
    async def analyze_with_thinking(self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage], str]) -> None:
        """使用 think-tool 进行深度分析"""
        logger.info(f"[{self.id}] 开始分析热点数据")
        
        try:
            # ✅ 使用 MCPStdioTool 连接本地 think-tool
            from agent_framework import MCPStdioTool
            
            async with MCPStdioTool(
                name="think-tool",
                command="npx",
                args=["-y", "@cgize/mcp-think-tool"],
                load_tools=True
            ) as think_tool:
                logger.info(f"[{self.id}] think-tool 已连接")
                
                # 创建带有 think-tool 的分析 agent
                analysis_agent = self.client.create_agent(
                    name="analysis_agent_with_thinking",
                    instructions=ANALYSIS_INSTRUCTIONS,
                    tools=[think_tool]
                )
                
                # 执行分析
                result = await analysis_agent.run(messages)
                result_text = result.text if hasattr(result, 'text') else str(result)
                
                logger.info(f"[{self.id}] 分析完成，结果长度: {len(result_text)}")
                
                # ✅ 发送完整数据到下一个 executor
                from agent_framework import Role, TextContent
                response_msg = ChatMessage(
                    role=Role.ASSISTANT,
                    contents=[TextContent(text=result_text)]
                )
                await ctx.send_message([response_msg])
                
                # ✅ 同时输出中间结果给用户
                summary = f"🧠 **步骤 2: 深度分析完成**\n\n使用 think-tool 完成分析\n结果长度: {len(result_text)} 字符\n\n预览：\n```\n{result_text[:500]}\n```\n\n---\n"
                await ctx.yield_output(summary)
                
        except Exception as e:
            logger.error(f"[{self.id}] 分析失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 发送错误信息
            error_result = '{"error": "分析失败: ' + str(e) + '"}'
            from agent_framework import Role, TextContent
            error_msg = ChatMessage(role=Role.ASSISTANT, contents=[TextContent(text=error_result)])
            await ctx.send_message([error_msg])

analysis_executor = AnalysisExecutor(
    executor_id="analysis_executor_with_thinking",
    client=client
)
logger.info(f"✅ Analysis Executor (with think-tool) 创建完成")

# ✅ 创建小红书内容生成 Executor（输出中间结果）
class XiaohongshuContentExecutor(Executor):
    """生成小红书文案的 executor"""
    
    def __init__(self, executor_id: str, client):
        super().__init__(id=executor_id)
        self.client = client
        logger.info(f"✅ XiaohongshuContentExecutor 创建: {executor_id}")
    
    @handler
    async def create_content(self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage], str]) -> None:
        """生成小红书文案"""
        logger.info(f"[{self.id}] 开始生成小红书文案")
        
        try:
            # 创建小红书内容生成 agent
            xiaohongshu_agent = self.client.create_agent(
                name="xiaohongshu_creator",
                instructions=XIAOHONGSHU_INSTRUCTIONS
            )
            
            # 执行生成
            result = await xiaohongshu_agent.run(messages)
            result_text = result.text if hasattr(result, 'text') else str(result)
            
            logger.info(f"[{self.id}] 文案生成完成，长度: {len(result_text)}")
            
            # ✅ 发送完整数据到下一个 executor
            from agent_framework import Role, TextContent
            response_msg = ChatMessage(
                role=Role.ASSISTANT,
                contents=[TextContent(text=result_text)]
            )
            await ctx.send_message([response_msg])
            
            # ✅ 同时输出中间结果给用户
            summary = f"✍️ **步骤 3: 小红书文案生成完成**\n\n文案长度: {len(result_text)} 字符\n\n完整内容：\n```json\n{result_text}\n```\n\n---\n"
            await ctx.yield_output(summary)
            
        except Exception as e:
            logger.error(f"[{self.id}] 文案生成失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 发送错误信息
            error_result = '{"error": "文案生成失败: ' + str(e) + '"}'
            from agent_framework import Role, TextContent
            error_msg = ChatMessage(role=Role.ASSISTANT, contents=[TextContent(text=error_result)])
            await ctx.send_message([error_msg])

xiaohongshu_executor = XiaohongshuContentExecutor(
    executor_id="xiaohongshu_content_executor",
    client=client
)
logger.info(f"✅ Xiaohongshu Content Executor 创建完成")

# ✅ 创建小红书发布 Executor（使用 xhs-mcp）
class XiaohongshuPublisher(Executor):
    """使用 xhs-mcp 发布到小红书"""
    
    def __init__(self, executor_id: str, client):
        super().__init__(id=executor_id)
        self.client = client
        logger.info(f"✅ XiaohongshuPublisher 创建: {executor_id}")
    
    @handler
    async def publish_to_xhs(self, messages: list[ChatMessage], ctx: WorkflowContext[Never, str]) -> None:
        """发布内容到小红书（使用 xhs_mcp_server）"""
        logger.info(f"[{self.id}] 开始发布到小红书")
        
        try:
            # 提取小红书文案
            content_text = ""
            for msg in messages:
                if hasattr(msg, 'text') and msg.text:
                    content_text = msg.text
                    break
            
            logger.info(f"[{self.id}] 提取到文案，长度: {len(content_text)}")
            
            import json
            
            # 解析文案 JSON
            try:
                content_json = json.loads(content_text)
                title = content_json.get("title", "")
                content = content_json.get("content", "")
                tags = content_json.get("tags", [])
            except json.JSONDecodeError:
                logger.error(f"[{self.id}] 文案不是有效的 JSON 格式")
                error_result = '{"status": "failed", "message": "文案格式错误，不是有效的 JSON"}'
                await ctx.yield_output(error_result)
                return
            
            # ✅ 使用 xhs_mcp_server 发布
            from agent_framework import MCPStdioTool
            
            # 从环境变量获取配置
            phone = os.getenv("XHS_PHONE", "")
            json_path = os.getenv("XHS_JSON_PATH", "")
            
            if not phone or not json_path:
                logger.warning(f"[{self.id}] 未配置小红书账号，使用模拟发布")
                result_text = json.dumps({
                    "status": "simulated",
                    "message": "✅ 模拟发布成功（未配置 XHS_PHONE 和 XHS_JSON_PATH）",
                    "title": title,
                    "tags": tags,
                    "note": "请在 .env 中配置 XHS_PHONE 和 XHS_JSON_PATH 以启用真实发布"
                }, ensure_ascii=False, indent=2)
                
                final_output = f"🚀 **发布完成（模拟）**\n\n标题: {title}\n标签: {', '.join(tags)}\n\n完整内容：\n{content_text}\n\n---\n⚠️ 未配置小红书账号，这是模拟发布"
                await ctx.yield_output(final_output)
                return
            
            # 真实发布
            async with MCPStdioTool(
                name="xhs-mcp-server",
                command="uvx",
                args=["xhs_mcp_server@latest"],
                env={
                    "phone": phone,
                    "json_path": json_path
                },
                load_tools=True
            ) as xhs_tool:
                logger.info(f"[{self.id}] xhs-mcp-server 已连接")
                
                # 创建发布 agent
                publisher_agent = self.client.create_agent(
                    name="xhs_publisher",
                    instructions="""你是小红书发布助手。

**重要提示**：小红书发布笔记必须包含图片或视频！

**任务**：
1. 检查是否有可用的图片
2. 如果没有图片，返回提示信息，不要调用发布函数
3. 如果有图片，使用 create_note 函数发布

**输出格式**：
如果没有图片：
```json
{
  "status": "skipped",
  "message": "小红书发布需要图片，当前版本暂不支持自动配图。请手动在小红书 App 中发布。",
  "title": "标题",
  "content": "内容",
  "tags": ["标签"]
}
```

如果发布成功：
```json
{
  "status": "success",
  "message": "发布成功",
  "note_id": "笔记ID"
}
```
""",
                    tools=[xhs_tool]
                )
                
                # 构造发布请求
                publish_request = f"请发布小红书笔记：\n标题：{title}\n内容：{content}\n标签：{', '.join(tags)}"
                
                # 执行发布
                result = await publisher_agent.run(publish_request)
                result_text = result.text if hasattr(result, 'text') else str(result)
                
                logger.info(f"[{self.id}] 发布完成: {result_text[:200]}")
                
                # 输出最终结果
                final_output = f"🚀 **发布完成**\n\n标题: {title}\n标签: {', '.join(tags)}\n\n发布结果：\n{result_text}\n\n---\n✅ Workflow 执行完成！"
                await ctx.yield_output(final_output)
                
        except Exception as e:
            logger.error(f"[{self.id}] 发布失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回错误信息
            error_result = f'{{"status": "failed", "message": "发布失败: {str(e)}"}}'
            await ctx.yield_output(error_result)

xhs_publisher = XiaohongshuPublisher(
    executor_id="xhs_publisher",
    client=client
)
logger.info(f"✅ Xiaohongshu Publisher 创建完成")

# 构建 workflow（DevUI 会查找名为 'workflow' 的变量）
# ✅ 新的 workflow 架构（所有步骤都输出中间结果）：
# 1. Hotspot Executor - 使用 daily-hot-mcp 获取热点
# 2. Analysis Executor - 使用 think-tool 深度分析
# 3. Xiaohongshu Content Executor - 生成小红书文案
# 4. Xiaohongshu Publisher - 发布（模拟）
workflow = (
    SequentialBuilder()
    .participants([
        hotspot_executor,      # ✅ 获取热点（daily-hot-mcp）
        analysis_executor,     # ✅ 深度分析（think-tool）
        xiaohongshu_executor,  # ✅ 生成小红书文案
        xhs_publisher          # ✅ 发布到小红书（模拟）
    ])
    .build()
)

# 添加元数据（可选）
workflow.name = "Xiaohongshu Hotspot Workflow"
workflow.description = "热点追踪 → 深度分析 → 小红书文案生成 → 自动发布"
