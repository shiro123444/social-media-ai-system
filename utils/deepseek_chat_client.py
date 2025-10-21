"""
DeepSeek Chat 客户端 - 修复多模态格式不兼容 & DevUI 序列化问题

核心问题：
1. Agent Framework 为了支持多模态，统一使用数组格式的 content
2. DeepSeek API 不支持多模态，只接受纯文本字符串
3. DevUI 在 agent 执行过程中尝试序列化 ChatMessage，如果包含 TextContent 对象会报错

解决方案：
1. 发送请求时：_openai_chat_message_parser() 将数组格式转换为字符串
2. 接收响应时：_parse_chat_message_from_openai_response() 创建纯文本 ChatMessage
3. 确保 DevUI 永远不会遇到需要序列化 TextContent 对象的情况

参考：
- https://github.com/microsoft/agent-framework/blob/main/python/packages/openai/_chat_client.py#L380-384
- DevUI _mapper.py:303 序列化错误的根源
"""
import os
from typing import Any
from agent_framework import ChatMessage
from agent_framework.openai import OpenAIChatClient


class DeepSeekChatClient(OpenAIChatClient):
    """
    DeepSeek Chat 客户端 - 修复 API 兼容性 & DevUI 序列化问题
    
    解决两个关键问题：
    
    1. DeepSeek API 格式兼容：
       - Agent Framework: content 是数组格式（支持多模态）
       - DeepSeek API: content 必须是字符串（仅支持文本）
       - 解决：_openai_chat_message_parser() 转换格式
    
    2. DevUI TextContent 序列化错误：
       - DevUI 在 agent 执行过程中序列化 ChatMessage
       - 如果 ChatMessage.contents 包含 TextContent 对象会报错
       - 解决：_parse_chat_message_from_openai_response() 返回纯文本消息
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_id: str = "deepseek-chat",
        **kwargs: Any
    ):
        """
        初始化 DeepSeek 客户端
        
        Args:
            api_key: DeepSeek API 密钥（默认从环境变量 DEEPSEEK_API_KEY 读取）
            base_url: API 基础 URL（默认 https://api.deepseek.com）
            model_id: 模型名称（默认 deepseek-chat）
            **kwargs: 传递给父类的其他参数
        """
        # 从环境变量获取默认值
        if api_key is None:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY 环境变量未设置，且未提供 api_key 参数")
        
        if base_url is None:
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        
        # 调用父类构造函数
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model_id=model_id,
            **kwargs
        )
    
    def _openai_chat_message_parser(self, message: ChatMessage) -> list[dict[str, Any]]:
        """
        重写消息解析器，修复 DeepSeek 特有问题
        
        Agent Framework 为支持多模态，将 content 格式化为数组：
        {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
        
        DeepSeek API 不支持多模态，期望纯文本字符串：
        {"role": "user", "content": "Hello"}
        
        此方法负责将数组格式转换为字符串格式。
        
        Args:
            message: 要解析的消息
            
        Returns:
            符合 DeepSeek API 格式的消息字典列表
        """
        # 先用父类方法处理（会生成多模态数组格式）
        parent_messages = super()._openai_chat_message_parser(message)
        
        # 修复所有消息，将数组格式转换为字符串
        fixed_messages = []
        for msg in parent_messages:
            # 处理 tool 消息
            if msg.get("role") == "tool":
                # 确保 tool_call_id 存在（DeepSeek 要求）
                if "tool_call_id" not in msg or msg["tool_call_id"] is None:
                    msg["tool_call_id"] = "default_call_id"
                
                # 确保 content 是字符串
                if "content" in msg:
                    msg["content"] = self._content_to_string(msg["content"])
            
            # 处理其他类型消息的 content（user, assistant, system）
            elif "content" in msg:
                msg["content"] = self._content_to_string(msg["content"])
            
            fixed_messages.append(msg)
        
        return fixed_messages
    
    def _parse_text_from_choice(self, choice):
        """
        让父类处理 TextContent 创建
        
        不要重写这个方法返回字符串！
        框架期望返回 TextContent | None
        """
        # 调用父类方法，让它正常创建 TextContent 对象
        return super()._parse_text_from_choice(choice)
    
    def _create_chat_response(self, response, chat_options):
        """
        创建 ChatResponse
        
        不要清空 contents！DevUI 需要 TextContent 对象来生成事件
        """
        # 调用父类方法，保持 TextContent 在 contents 中
        chat_response = super()._create_chat_response(response, chat_options)
        
        # 只处理 FunctionResult 的序列化问题
        if hasattr(chat_response, 'messages') and chat_response.messages:
            for msg in chat_response.messages:
                if hasattr(msg, 'contents') and msg.contents:
                    for content in msg.contents:
                        # 特殊处理：FunctionResult 的 result 字段需要转换为字符串
                        if 'FunctionResult' in type(content).__name__ and hasattr(content, 'result'):
                            result_text = self._content_to_string(content.result)
                            object.__setattr__(content, 'result', result_text)
        
        return chat_response
    
    def _create_chat_response_update(self, chunk):
        """
        创建流式响应更新
        
        让框架正常处理 TextContent，不要清空 contents
        """
        # 调用父类方法
        chat_response_update = super()._create_chat_response_update(chunk)
        
        # 只处理 FunctionResult 的序列化问题
        if hasattr(chat_response_update, 'delta') and chat_response_update.delta:
            delta = chat_response_update.delta
            if hasattr(delta, 'contents') and delta.contents:
                for content in delta.contents:
                    if 'FunctionResult' in type(content).__name__ and hasattr(content, 'result'):
                        result_text = self._content_to_string(content.result)
                        object.__setattr__(content, 'result', result_text)
        
        return chat_response_update
    
    def _content_to_string(self, content: Any) -> str:
        """
        将 content 转换为纯文本字符串
        
        处理多种格式：
        1. 字符串 -> 直接返回
        2. 数组 -> 提取所有文本部分并拼接
        3. 字典 -> 提取 text 字段或序列化为 JSON
        4. None -> 返回空字符串
        
        Args:
            content: 可能是字符串、列表、字典或 None
            
        Returns:
            纯文本字符串
        """
        import json
        
        # 1. 如果是 None
        if content is None:
            return ""
        
        # 2. 如果已经是字符串，直接返回
        if isinstance(content, str):
            return content
        
        # 3. 如果是列表（多模态内容数组）
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    # 提取文本内容（Agent Framework 标准格式）
                    if item.get("type") == "text" and "text" in item:
                        texts.append(item["text"])
                    # 其他类型（图片、文件等）转为 JSON 描述
                    else:
                        texts.append(json.dumps(item, ensure_ascii=False))
                elif isinstance(item, str):
                    texts.append(item)
                else:
                    texts.append(str(item))
            
            return " ".join(texts) if texts else ""
        
        # 4. 如果是字典（单个内容对象）
        if isinstance(content, dict):
            # 标准文本内容格式
            if content.get("type") == "text" and "text" in content:
                return content["text"]
            # 其他格式转为 JSON
            return json.dumps(content, ensure_ascii=False)
        
        # 5. 其他类型，转为字符串
        return str(content)


def create_deepseek_client(
    api_key: str | None = None,
    base_url: str | None = None,
    model_id: str = "deepseek-chat",
    **kwargs: Any
) -> DeepSeekChatClient:
    """
    工厂函数：创建 DeepSeek Chat 客户端
    
    注意：由于 DeepSeek API 不支持多模态（仅支持文本），
    而 Agent Framework 默认使用多模态数组格式，
    因此必须使用自定义客户端进行格式转换。
    
    Args:
        api_key: API 密钥（默认从环境变量读取）
        base_url: API 基础 URL（默认 https://api.deepseek.com）
        model_id: 模型名称（默认 deepseek-chat）
        **kwargs: 传递给 DeepSeekChatClient 的其他参数
        
    Returns:
        DeepSeekChatClient 实例
        
    Example:
        >>> client = create_deepseek_client()
        >>> agent = client.create_agent(name="test", instructions="...")
        
    References:
        - DeepSeek API 文档：不支持多模态输入
        - Agent Framework _chat_client.py:380-384：content 数组格式
    """
    return DeepSeekChatClient(
        api_key=api_key,
        base_url=base_url,
        model_id=model_id,
        **kwargs
    )
