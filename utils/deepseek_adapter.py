"""
DeepSeek API 适配器 
解决 Agent Framework 的 content 数组格式与 DeepSeek API 字符串格式的兼容性问题

核心问题：
- Agent Framework 为支持多模态，将 content 格式化为数组：[{"type": "text", "text": "..."}]
- DeepSeek API 期望简单的字符串格式：content="..."
- 解决方案：覆盖 _openai_content_parser 方法，对纯文本返回字符串而不是字典

参考：microsoft/agent-framework 官方文档
"""
import os
import logging
from typing import Any
from dotenv import load_dotenv
from agent_framework.openai import OpenAIChatClient
from agent_framework._types import TextContent

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)


class DeepSeekChatClient(OpenAIChatClient):
    """
    DeepSeek 适配客户端
    
    关键修复：
    1. 覆盖 _openai_content_parser，纯文本返回字符串
    2. 保持其他功能完全兼容 Agent Framework
    """
    
    def _openai_content_parser(self, content) -> Any:
        """
        🔑 关键方法：修复 content 格式
        
        Agent Framework 默认行为：
        - TextContent -> {"type": "text", "text": "..."}
        
        DeepSeek 需要：
        - TextContent -> "..." (纯字符串)
        
        Args:
            content: 消息内容对象
            
        Returns:
            DeepSeek 兼容的格式
        """
        # 对于纯文本内容，直接返回字符串
        if isinstance(content, TextContent):
            return content.text
        
        # 其他类型（FunctionCall、图片等）使用父类方法
        return super()._openai_content_parser(content)
    
    def _openai_chat_message_parser(self, message):
        """
        覆盖消息解析方法，确保 content 为字符串而不是数组
        
        Agent Framework 默认行为：
        - args["content"] = [] 
        - args["content"].append(parsed_content)
        
        DeepSeek 需要：
        - 如果只有一个 TextContent，args["content"] = "string"
        - 如果有多个内容或非文本，使用数组（如果 DeepSeek 不支持则报错）
        
        Args:
            message: ChatMessage 对象
            
        Returns:
            DeepSeek 兼容的消息列表
        """
        # 调用父类方法获取标准 OpenAI 格式
        parsed_messages = super()._openai_chat_message_parser(message)
        
        # 修复每条消息的 content 字段
        for msg in parsed_messages:
            if "content" in msg and isinstance(msg["content"], list):
                content_list = msg["content"]
                
                # 如果只有一个文本元素，转换为字符串
                if len(content_list) == 1:
                    item = content_list[0]
                    if isinstance(item, dict) and item.get("type") == "text":
                        msg["content"] = item.get("text", "")
                    elif isinstance(item, str):
                        msg["content"] = item
                
                # 如果是空数组，转换为空字符串
                elif len(content_list) == 0:
                    msg["content"] = ""
                
                # 如果有多个元素，尝试合并文本
                else:
                    text_parts = []
                    for item in content_list:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    
                    if text_parts:
                        msg["content"] = " ".join(text_parts)
                    # 如果有非文本内容（如图片），保留数组
                    # DeepSeek 可能不支持，但至少格式正确
        
        return parsed_messages


def create_deepseek_client(debug: bool = False, **kwargs) -> DeepSeekChatClient:
    """
    创建 DeepSeek 客户端（高效简洁版）
    
    Args:
        debug: 是否启用调试日志
        **kwargs: 传递给 OpenAIChatClient 的其他参数
        
    Returns:
        DeepSeekChatClient 实例
        
    使用示例：
        ```python
        from utils.deepseek_adapter import create_deepseek_client
        from agent_framework import ChatAgent
        
        # 创建客户端
        client = create_deepseek_client()
        
        # 创建智能体
        agent = ChatAgent(
            chat_client=client,
            name="助手",
            instructions="你是一个有用的助手"
        )
        
        # 运行
        result = await agent.run("你好")
        ```
    """
    # 从环境变量获取配置
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model_id = os.getenv("DEEPSEEK_MODEL_ID", "deepseek-chat")
    
    if not api_key:
        raise ValueError(
            "未找到 DEEPSEEK_API_KEY 环境变量。\n"
            "请在 .env 文件中配置: DEEPSEEK_API_KEY=sk-xxx"
        )
    
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"创建 DeepSeek 客户端: {base_url} / {model_id}")
    
    # 创建客户端
    return DeepSeekChatClient(
        api_key=api_key,
        base_url=base_url,
        model_id=model_id,
        **kwargs
    )


# 向后兼容的别名
DeepSeekAPIError = Exception
DeepSeekRateLimitError = Exception
DeepSeekConnectionError = Exception
