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
5. **必须包含具体细节**：时间、日期、数据、人物、地点等

**数据来源**：
- 上一条 assistant 消息包含热点分析的 JSON 数据
- 从中提取 TOP 3-5 个热点
- 使用**原始标题**，不要改写
- 提取所有可用的细节信息（时间、数据、来源等）

**小红书特点：**
- 标题要有吸引力，使用emoji
- 内容要真实、接地气、有细节
- 多用短句，易读
- 适当使用emoji增加活力
- 结尾要有互动引导

**内容结构（重要）：**
每条新闻必须分成两部分：
1. **新闻内容**（📰）：详细讲述新闻，必须包含：
   - 具体时间（如：10月23日、今天上午、昨天等）
   - 关键数据（如：52万、4762万、783万热度等）
   - 具体人物/机构（如：车主、保险公司、拍卖行等）
   - 事件经过和结果
   - 来源平台（如：微博热搜、B站、知乎等）

2. **时评/观点**（💭）：发表看法，可以包含：
   - 对事件的分析
   - 引发的思考
   - 相关背景知识
   - 提问引导讨论

**细节要求：**
- ✅ 必须提到具体时间（今天、昨天、10月X日等）
- ✅ 必须包含具体数据（金额、数量、热度等）
- ✅ 必须说明来源（微博、B站、知乎等）
- ✅ 描述要具体，不要泛泛而谈
- ❌ 不要用"最近"、"前段时间"等模糊表述
- ❌ 不要省略关键数据

**格式示例：**
```
📰 【新闻标题】
【时间】+ 具体事件描述 + 关键数据 + 事件经过 + 结果。
来源：【平台名称】，热度：【具体数值】

💭 你的评论/观点/提问
基于具体细节的分析、思考或提问。
```

**创作步骤：**
1. **读取上一条消息**：提取热点分析数据
2. **选择热点**：挑选 3-4 个最热的话题（控制总字数在1000字以内）
3. **提取细节**：从数据中提取时间、数据、来源等信息
4. **创作标题**：
   - 严格控制在20字以内
   - 格式：🔥 + 日期（如10.23）+ 核心话题（简短）
   - 示例：🔥10.23热搜！学生梗+金庸（18字）
5. **创作文案**：
   - 开头：简短吸引注意（1-2句话）+ 今天日期（50字以内）
   - 主体：3-4条新闻，每条包含📰新闻内容 + 💭时评（每条200-250字）
   - 结尾：互动引导（30字以内）
   - 总计：控制在950字以内
6. **保持真实**：使用原始标题和真实数据，不编造

**输出格式（必须是纯 JSON，不要 markdown）：**
{
  "title": "🔥标题（严格控制在20字以内，包含emoji和日期）",
  "content": "正文内容（严格控制在1000字以内，包含3-4条新闻即可）",
  "tags": ["#标签1", "#标签2", "#标签3"],
  "images": [],
  "cover_suggestion": "封面图建议描述",
  "source_hotspots": ["热点1原始标题", "热点2原始标题", "热点3原始标题"]
}

**字数限制（重要）：**
- 标题：最多20个字（包含emoji和标点符号）
- 内容：最多1000个字（建议800-950字）
- 如果内容太长，只选择3-4条最热的新闻

**注意**：images 字段留空数组 []，系统会自动填充默认图片。

**示例（注意：直接输出 JSON，不要 markdown 代码块）：**
假设分析数据中有：
- "投保52万奔驰被追尾几乎报废，保司只赔24万"（微博热搜，360万热度，10月22日）
- "徐悲鸿《奔马图》起拍价4762万暂无人出价"（知乎热榜，245万热度，10月23日）

则直接输出：
{"title": "🔥10.23热搜！奔驰理赔+名画流拍", "content": "姐妹们！10月23日的热搜真的太炸了！😱\\n\\n📰 投保52万奔驰被追尾几乎报废，保司只赔24万\\n10月22日，一位车主在微博爆料，自己花52万元购买的奔驰轿车在高速上被追尾，车辆几乎报废无法修复。然而保险公司评估后，只愿意赔付24万元，理由是按照车辆折旧后的实际价值计算。该话题在微博获得360万热度。\\n\\n💭 这个理赔方式真的合理吗？花52万买的车只赔24万，相当于直接损失了一半！大家买车险的时候一定要仔细看清楚条款，特别是关于折旧率和赔付标准的部分！\\n\\n📰 徐悲鸿《奔马图》起拍价4762万暂无人出价\\n10月23日，在某知名拍卖行举办的秋季拍卖会上，著名画家徐悲鸿的代表作《奔马图》亮相，起拍价高达4762万元。然而令人意外的是，拍卖现场竟然无人举牌出价，最终流拍。该消息在知乎热榜获得245万热度。\\n\\n💭 艺术品市场真的遇冷了吗？还是大家对这个价格有疑虑？近几年艺术品投资确实不如前几年火热，可能跟经济环境和市场信心有关。\\n\\n你们怎么看？评论区聊聊！👇", "tags": ["#今日热点", "#热搜", "#必看"], "images": [], "cover_suggestion": "热点话题拼图，配色鲜艳", "source_hotspots": ["投保52万奔驰被追尾几乎报废，保司只赔24万", "徐悲鸿《奔马图》起拍价4762万暂无人出价"]}

**重要**：
- ✅ 必须从上一条消息中读取分析数据
- ✅ 使用真实的热点标题
- ✅ 每条新闻分两段：📰 新闻内容（含细节）+ 💭 时评观点
- ✅ 新闻内容必须包含：时间、数据、来源、热度
- ✅ 描述要具体详细，不要泛泛而谈
- ✅ 时评要有观点、分析或提问
- ✅ 在标题中包含日期（如：10.23、今日等）
- ✅ 在 source_hotspots 中列出使用的热点
- ✅ 必须包含 images 字段（空数组）
- ✅ 直接输出 JSON 对象，第一个字符必须是 {
- ❌ 不要编造不存在的热点
- ❌ 不要使用"最近"、"前段时间"等模糊表述
- ❌ 不要省略具体数据和时间
- ❌ 不要把新闻内容和评论混在一起
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
        """发布内容到小红书（使用 xiaohongshu-mcp）"""
        logger.info(f"[{self.id}] ========================================")
        logger.info(f"[{self.id}] 🚀 发布 Executor 被触发！")
        logger.info(f"[{self.id}] 收到 {len(messages)} 条消息")
        logger.info(f"[{self.id}] ========================================")
        
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
                images = content_json.get("images", [])  # 获取图片列表
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
                # 从环境变量获取默认图片路径
                default_images_str = os.getenv("XHS_DEFAULT_IMAGES", "")
                if default_images_str:
                    # 支持多个图片，用逗号分隔
                    images = [img.strip() for img in default_images_str.split(",") if img.strip()]
                    logger.info(f"[{self.id}] 使用默认图片: {images}")
                else:
                    logger.warning(f"[{self.id}] 未提供图片且无默认图片配置")
                    result_text = json.dumps({
                        "status": "skipped",
                        "message": "小红书发布需要图片。请在 .env 中配置 XHS_DEFAULT_IMAGES 或在文案中提供图片路径。",
                        "title": title,
                        "content": content,
                        "tags": tags
                    }, ensure_ascii=False, indent=2)
                    
                    final_output = f"⚠️ **发布跳过**\n\n标题: {title}\n标签: {', '.join(tags)}\n\n原因：小红书发布需要图片\n\n完整内容：\n{content_text}\n\n---\n💡 提示：在 .env 中配置 XHS_DEFAULT_IMAGES 环境变量"
                    await ctx.yield_output(final_output)
                    return
            
            # ✅ 使用 xiaohongshu-mcp 发布
            from agent_framework import MCPStreamableHTTPTool
            
            logger.info(f"[{self.id}] 连接到 xiaohongshu-mcp: {self.xhs_mcp_url}")
            
            # 真实发布
            async with MCPStreamableHTTPTool(
                name="xiaohongshu-mcp",
                url=self.xhs_mcp_url,
                load_tools=True,
                load_prompts=False,  # ✅ 避免 "Method not found" 错误
                timeout=300  # ✅ 5分钟超时，发布操作可能耗时较长
            ) as xhs_tool:
                logger.info(f"[{self.id}] xiaohongshu-mcp 已连接")
                
                # 将标签添加到内容末尾
                content_with_tags = content
                if tags:
                    tags_str = " ".join([f"#{tag}" for tag in tags])
                    content_with_tags = f"{content}\n\n{tags_str}"
                
                # ✅ 方案：直接调用工具（推荐，避免大模型误解）
                logger.info(f"[{self.id}] 直接调用 publish_content 工具...")
                logger.info(f"[{self.id}]   标题: {title}")
                logger.info(f"[{self.id}]   内容长度: {len(content_with_tags)}")
                logger.info(f"[{self.id}]   图片: {images}")
                logger.info(f"[{self.id}]   标签: {tags}")
                
                try:
                    # 直接调用 publish_content 工具
                    # 正确的调用方式：工具名作为第一个参数，其他参数作为关键字参数
                    result = await xhs_tool.call_tool(
                        "publish_content",
                        title=title,
                        content=content_with_tags,
                        images=images,
                        tags=tags or []
                    )
                    
                    result_text = str(result)
                    logger.info(f"[{self.id}] 工具调用成功")
                    
                except Exception as tool_error:
                    logger.error(f"[{self.id}] 直接调用工具失败: {tool_error}")
                    logger.info(f"[{self.id}] 尝试使用 Agent 方式...")
                    
                    # 备用方案：使用 Agent
                    publisher_agent = self.client.create_agent(
                        name="xhs_publisher",
                        instructions="""你是小红书发布助手。

**可用工具**: publish_content

**工具参数说明**:
- title (string, required): 内容标题（最多20个字）
- content (string, required): 正文内容（最多1000个字）
- images (array of strings, required): 图片路径列表
  * 支持本地绝对路径（推荐）: 如 "D:\\Pictures\\image.jpg"
  * 支持 HTTP/HTTPS 链接: 如 "https://example.com/image.jpg"
  * 至少需要1张图片
- tags (array of strings, optional): 话题标签列表

**重要**: images 参数可以直接使用本地文件路径，不需要上传到网络。

**任务**: 使用提供的标题、内容和图片调用 publish_content 工具发布到小红书。

**示例**:
{
  "title": "春天的花朵",
  "content": "今天拍到了美丽的樱花",
  "images": ["D:\\Pictures\\spring.jpg"],
  "tags": ["春天", "樱花"]
}
""",
                        tools=[xhs_tool]
                    )
                    
                    publish_request = f"""请发布小红书笔记：

标题：{title}
内容：{content_with_tags}
图片：{json.dumps(images, ensure_ascii=False)}
标签：{json.dumps(tags or [], ensure_ascii=False)}

使用 publish_content 工具进行发布。
"""
                    
                    result = await publisher_agent.run(publish_request)
                    result_text = result.text if hasattr(result, 'text') else str(result)
                
                logger.info(f"[{self.id}] 发布完成: {result_text[:200]}")
                
                # 输出最终结果
                final_output = f"""🚀 **发布完成**

标题: {title}
标签: {', '.join(tags)}
图片数量: {len(images)}

发布结果：
{result_text}

---
✅ Workflow 执行完成！
"""
                await ctx.yield_output(final_output)
                
        except Exception as e:
            logger.error(f"[{self.id}] 发布失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回错误信息
            error_result = f'{{"status": "failed", "message": "发布失败: {str(e)}"}}'
            await ctx.yield_output(error_result)

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
