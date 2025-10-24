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
HOTSPOT_INSTRUCTIONS = """调用MCP工具获取热点数据，原样返回JSON格式。

输出格式：
```json
{
  "hotspots": [
    {"title": "原始标题", "url": "链接", "heat_index": 数值, "source": "平台"}
  ]
}
```

要求：保持原始数据不变，不要改写标题。"""

ANALYSIS_INSTRUCTIONS = """分析热点数据，按类别整理并输出JSON。

从上一条消息提取hotspots数据，按类别分类（科技/娱乐/社会/财经），保持原始标题不变。

输出格式：
```json
{
  "date": "日期",
  "categories": {"社会": [{"title": "原标题", "source": "来源", "heat_index": 数值}]},
  "top_trends": [{"topic": "话题", "count": 数量}],
  "recommendations": [{"title": "原标题", "reason": "理由"}]
}
```"""

XIAOHONGSHU_INSTRUCTIONS = """基于上一条消息的热点分析，生成小红书文案。

要求：
- 标题：20字内，含emoji和日期（如🔥10.23热搜！）
- 内容：选3-4个热点，每个包含📰新闻+💭评论，总计1000字内
- 格式：纯JSON，不要markdown代码块
- 真实：使用原始标题和数据，不编造

输出格式：
{"title": "标题", "content": "正文", "tags": ["#标签"], "images": [], "cover_suggestion": "描述", "source_hotspots": ["原标题"]}"""

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
            
            # ✅ 自动添加默认图片（如果文案中没有图片）
            import json
            try:
                content_json = json.loads(result_text)
                images = content_json.get("images", [])
                
                # 如果没有图片，使用默认图片
                if not images:
                    default_images_str = os.getenv("XHS_DEFAULT_IMAGES", "")
                    if default_images_str:
                        images = [img.strip() for img in default_images_str.split(",") if img.strip()]
                        content_json["images"] = images
                        result_text = json.dumps(content_json, ensure_ascii=False)
                        logger.info(f"[{self.id}] 已添加默认图片: {images}")
                    else:
                        logger.warning(f"[{self.id}] 未配置默认图片 (XHS_DEFAULT_IMAGES)")
            except json.JSONDecodeError:
                logger.warning(f"[{self.id}] 文案不是有效的 JSON，跳过图片处理")
            
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
            
            # ✅ 自动添加默认图片
            import json
            try:
                content_json = json.loads(result_text)
                images = content_json.get("images", [])
                
                if not images:
                    default_images_str = os.getenv("XHS_DEFAULT_IMAGES", "")
                    if default_images_str:
                        images = [img.strip() for img in default_images_str.split(",") if img.strip()]
                        content_json["images"] = images
                        result_text = json.dumps(content_json, ensure_ascii=False)
                        logger.info(f"[{self.id}] 已添加默认图片: {images}")
                
                # 创建内容预览
                title = content_json.get("title", "")
                content = content_json.get("content", "")
                tags = content_json.get("tags", [])
                
            except json.JSONDecodeError:
                logger.warning(f"[{self.id}] 文案不是有效的 JSON，跳过图片处理")
            
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

xiaohongshu_executor = XiaohongshuContentExecutor(
    executor_id="xiaohongshu_content_executor",
    client=client
)
logger.info(f"✅ Xiaohongshu Content Executor 创建完成")

# ✅ 创建小红书发布 Executor（使用 xiaohongshu-mcp）
class XiaohongshuPublisher(Executor):
    """使用 xiaohongshu-mcp 发布到小红书"""
    
    def __init__(self, executor_id: str, client, xhs_mcp_url: str = "http://localhost:18060/mcp"):
        super().__init__(id=executor_id)
        self.client = client
        self.xhs_mcp_url = xhs_mcp_url
        logger.info(f"✅ XiaohongshuPublisher 创建: {executor_id}, MCP URL: {xhs_mcp_url}")
    
    @handler
    async def publish_to_xhs(self, messages: list[ChatMessage], ctx: WorkflowContext[Never, str]) -> None:
        """发布内容到小红书（使用 xiaohongshu-mcp）- 带重试机制"""
        logger.info(f"[{self.id}] ========================================")
        logger.info(f"[{self.id}] 🚀 发布 Executor 被触发！")
        logger.info(f"[{self.id}] 收到 {len(messages)} 条消息")
        logger.info(f"[{self.id}] ========================================")
        
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
            images = content_json.get("images", [])
            
            # ✅ 限制标签数量（减少 DOM 操作，提高成功率）
            if len(tags) > 2:
                logger.warning(f"[{self.id}] 标签过多 ({len(tags)}个)，限制为2个以提高成功率")
                tags = tags[:2]
                
        except json.JSONDecodeError:
            logger.error(f"[{self.id}] 文案不是有效的 JSON 格式")
            error_result = '{"status": "failed", "message": "文案格式错误，不是有效的 JSON"}'
            await ctx.yield_output(error_result)
            return
        
        # 检查标题和内容长度（小红书限制）
        if len(title) > 20:
            logger.warning(f"[{self.id}] 标题超过 20 字，将被截断")
            title = title[:20]
        
        if len(content) > 1000:
            logger.warning(f"[{self.id}] 内容超过 1000 字，将被截断")
            content = content[:1000]
        
        # 检查是否有图片，如果没有则使用默认图片
        if not images:
            default_images_str = os.getenv("XHS_DEFAULT_IMAGES", "")
            if default_images_str:
                images = [img.strip() for img in default_images_str.split(",") if img.strip()]
                logger.info(f"[{self.id}] 使用默认图片: {images}")
            else:
                logger.warning(f"[{self.id}] 未提供图片且无默认图片配置")
                final_output = f"⚠️ **发布跳过**\n\n标题: {title}\n标签: {', '.join(tags)}\n\n原因：小红书发布需要图片\n\n---\n💡 提示：在 .env 中配置 XHS_DEFAULT_IMAGES 环境变量"
                await ctx.yield_output(final_output)
                return
        
        # 重试配置
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"[{self.id}] 🔄 重试 {attempt}/{max_retries-1}...")
                    await ctx.yield_output(f"⚠️ 发布失败，正在重试 ({attempt}/{max_retries-1})...\n")
                    import asyncio
                    await asyncio.sleep(retry_delay)
                
                # ✅ 使用 xiaohongshu-mcp 发布
                from agent_framework import MCPStreamableHTTPTool
                
                logger.info(f"[{self.id}] 连接到 xiaohongshu-mcp: {self.xhs_mcp_url}")
                
                async with MCPStreamableHTTPTool(
                    name="xiaohongshu-mcp",
                    url=self.xhs_mcp_url,
                    load_tools=True,
                    load_prompts=False,
                    timeout=300
                ) as xhs_tool:
                    logger.info(f"[{self.id}] xiaohongshu-mcp 已连接")
                    
                    # 将标签添加到内容末尾
                    content_with_tags = content
                    if tags:
                        tags_str = " ".join([f"#{tag}" for tag in tags])
                        content_with_tags = f"{content}\n\n{tags_str}"
                    
                    logger.info(f"[{self.id}] 直接调用 publish_content 工具...")
                    logger.info(f"[{self.id}]   标题: {title}")
                    logger.info(f"[{self.id}]   内容长度: {len(content_with_tags)}")
                    logger.info(f"[{self.id}]   图片: {images}")
                    logger.info(f"[{self.id}]   标签数量: {len(tags)} (限制为2个)")
                    
                    # 直接调用 publish_content 工具
                    result = await xhs_tool.call_tool(
                        "publish_content",
                        title=title,
                        content=content_with_tags,
                        images=images,
                        tags=tags or []
                    )
                    
                    result_text = str(result)
                    logger.info(f"[{self.id}] ✅ 工具调用成功")
                    
                    # 输出最终结果
                    final_output = f"""🚀 **发布完成**

标题: {title}
标签: {', '.join(tags)} (限制为{len(tags)}个)
图片数量: {len(images)}

发布结果：
{result_text}

---
✅ Workflow 执行完成！
"""
                    await ctx.yield_output(final_output)
                    
                    # ✅ 发布成功，跳出重试循环
                    return
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[{self.id}] 尝试 {attempt + 1} 失败: {error_msg}")
                
                # 检查是否是 DOM 分离错误（标签输入问题）
                is_dom_error = "Node is detached" in error_msg or "detached from document" in error_msg
                
                if is_dom_error:
                    logger.warning(f"[{self.id}] 检测到 DOM 分离错误（标签输入问题）")
                
                # 如果还有重试机会，继续重试
                if attempt < max_retries - 1:
                    logger.info(f"[{self.id}] 将在 {retry_delay} 秒后重试...")
                    continue
                else:
                    # 所有重试都失败了
                    logger.error(f"[{self.id}] 所有重试均失败")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # 返回详细错误信息
                    error_result = f"""❌ **发布失败**

标题: {title}
标签: {', '.join(tags)}

错误信息：
{error_msg}

重试次数: {max_retries}

---
💡 故障排除建议：
1. 检查 xiaohongshu-mcp 服务是否正常运行
2. 检查浏览器是否已登录小红书
3. 尝试减少标签数量（当前已限制为2个）
4. 查看 xiaohongshu-mcp 日志获取详细错误信息
5. 考虑向 xiaohongshu-mcp 项目提交 issue

这是 xiaohongshu-mcp 的浏览器自动化问题，不是工作流代码问题。
"""
                    await ctx.yield_output(error_result)
                    return

# 从环境变量获取 xiaohongshu-mcp URL（默认 localhost:18060）
xhs_mcp_url = os.getenv("XIAOHONGSHU_MCP_URL", "http://localhost:18060/mcp")

xhs_publisher = XiaohongshuPublisher(
    executor_id="xhs_publisher",
    client=client,
    xhs_mcp_url=xhs_mcp_url
)
logger.info(f"✅ Xiaohongshu Publisher 创建完成")

# 构建 workflow（DevUI 会查找名为 'workflow' 的变量）
# ✅ 新的 workflow 架构（所有步骤都输出中间结果）：
# 1. Hotspot Executor - 使用 daily-hot-mcp 获取热点
# 2. Analysis Executor - 使用 think-tool 深度分析
# 3. Xiaohongshu Content Executor - 生成小红书文案
# 4. Xiaohongshu Publisher - 发布到小红书
workflow = (
    SequentialBuilder()
    .participants([
        hotspot_executor,      # ✅ 获取热点（daily-hot-mcp）
        analysis_executor,     # ✅ 深度分析（think-tool）
        xiaohongshu_executor,  # ✅ 生成小红书文案
        xhs_publisher          # ✅ 发布到小红书
    ])
    .build()
)

# 添加元数据（可选）
workflow.name = "Xiaohongshu Hotspot Workflow"
workflow.description = "热点追踪 → 深度分析 → 小红书文案生成 → 自动发布"
