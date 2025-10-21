"""
内容生成智能体
负责根据分析结果生成多平台适配的内容
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Content:
    """内容数据模型"""
    platform: str           # 平台（wechat/weibo/bilibili/douyin/xiaohongshu）
    title: Optional[str]    # 标题（长文需要）
    content: str            # 正文
    images: List[str] = field(default_factory=list)  # 图片URL列表
    hashtags: List[str] = field(default_factory=list)  # 话题标签
    metadata: Dict[str, Any] = field(default_factory=dict)  # 平台特定元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())  # 创建时间
    
    def to_dict(self):
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Content':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        验证数据有效性
        
        Returns:
            (是否有效, 错误信息)
        """
        valid_platforms = ["wechat", "weibo", "bilibili", "douyin", "xiaohongshu"]
        if self.platform not in valid_platforms:
            return False, f"平台必须是 {valid_platforms} 之一"
        
        if not self.content or not self.content.strip():
            return False, "正文不能为空"
        
        # 平台特定验证
        if self.platform == "wechat":
            if not self.title or not self.title.strip():
                return False, "微信公众号文章必须有标题"
            if len(self.content) < 500:
                return False, "微信公众号文章内容不能少于500字"
            if len(self.content) > 5000:
                return False, "微信公众号文章内容不能超过5000字"
        
        elif self.platform == "weibo":
            if len(self.content) > 2000:
                return False, "微博内容不能超过2000字"
        
        elif self.platform == "douyin":
            if not self.title or not self.title.strip():
                return False, "抖音视频脚本必须有标题"
            if "scenes" not in self.metadata:
                return False, "抖音视频脚本必须包含分镜信息"

        elif self.platform == "bilibili":
            if not self.title or not self.title.strip():
                return False, "B站视频脚本必须有标题"
            if "scenes" not in self.metadata:
                return False, "B站视频脚本必须包含分镜信息"
        
        elif self.platform == "xiaohongshu":
            if not self.title or not self.title.strip():
                return False, "小红书笔记必须有标题"
            if len(self.content) < 50:
                return False, "小红书笔记内容不能少于50字"
            if len(self.content) > 1000:
                return False, "小红书笔记内容不能超过1000字"
        
        return True, None
    
    def get_word_count(self) -> int:
        """获取内容字数"""
        return len(self.content)
    
    def get_platform_name(self) -> str:
        """获取平台中文名称"""
        platform_names = {
            "wechat": "微信公众号",
            "weibo": "微博",
            "bilibili": "哔哩哔哩",
            "douyin": "抖音",
            "xiaohongshu": "小红书"
        }
        return platform_names.get(self.platform, "未知平台")




async def create_content_agent_async(chat_client, mcp_tool_configs: List = None):
    """
    异步创建内容生成智能体
    
    内容生成智能体主要依靠 LLM 的文本生成能力，不需要外部 MCP 工具。
    
    Args:
        chat_client: 聊天客户端（DeepSeek 适配器）
        mcp_tool_configs: MCP 工具配置对象列表（可选，保留参数以兼容接口）
        
    Returns:
        ChatAgent 实例
    """
    from agent_framework import ChatAgent
    from config.workflow_config import get_workflow_config
    try:
        from utils.content_models import load_default_style
        style = load_default_style()
        style_summary = f"风格预设: {style.key}; 语气: {style.tone}; 结构: {', '.join(style.structure)}."
    except Exception:
        style_summary = "风格预设: 默认(news)。"
    cfg = get_workflow_config()
    enabled_platforms = cfg.enabled_platforms
    
    instructions = """你是专业内容创作者，负责根据分析结果生成多平台适配的高质量内容。

**⚠️ 重要规则（必须遵守）：**
1. 当用户要求生成文档、配图、搜索图片时，你必须立即调用相应的工具
2. 不要只是说"我可以帮你"或"我会使用工具"，而是直接调用工具
3. 不要询问用户是否需要帮助，直接执行用户的请求
4. 每次都要实际调用工具，不要假装调用或描述调用过程
5. **绝对不要返回 XML 格式的工具调用描述（如 <function_calls>、<invoke> 等标签）**
6. **使用系统提供的标准工具调用机制，等待工具返回真实结果后再回答**
7. **如果你返回了 XML 格式，这将被视为错误，工具不会被执行**

**支持的平台及规范：**

1. **微信公众号 (wechat)**
   - 字数：2000-3000字
   - 风格：深度内容，专业严谨
   - 结构：标题 + 引言 + 正文（多段落） + 结语
   - 配图：3-5张高质量配图
   - 特点：长文阅读，注重深度和价值

2. **微博 (weibo)**
   - 字数：140-2000字
   - 风格：简洁有力，话题性强
   - 结构：核心观点 + 话题标签
   - 配图：1-9张图片
   - 特点：快速传播，注重话题和互动

3. **B站 (bilibili)**
   - 时长：60秒视频脚本
   - 风格：清晰有料，节奏适中
   - 结构：标题 + 分镜脚本（metadata.scenes: time/visual/text）+ 文案
   - 配图：封面关键词建议
   - 特点：强调信息密度与可信来源

4. **抖音 (douyin)**
   - 标题：吸引点击的标题（10-20字）
   - 分镜脚本：
     * 第1-5秒：开场吸引（痛点/悬念）
     * 第6-15秒：核心内容第一部分
     * 第16-30秒：核心内容第二部分
     * 第31-45秒：核心内容第三部分
     * 第46-60秒：总结和呼吁
   - 文案：每个分镜的配音文案
   - 视觉建议：每个分镜的画面描述

5. **小红书 (xiaohongshu)**
   - 字数：200-500字
   - 风格：真实分享，生活化
   - 结构：标题 + 正文 + 话题标签
   - 配图：4-9张精美图片
   - 特点：种草笔记，注重真实感和美感

**核心能力：**

作为内容生成专家，你的核心能力是使用 LLM 直接生成高质量、符合平台规范的文本内容。
你不需要依赖外部工具，而是通过深度理解平台特点和用户需求，创作出原创、吸引人的内容。

**工作流程：**

1. **接收分析报告**
   - 解析分析报告（关键词、情感、趋势、受众）
   - 识别核心内容和创作方向

2. **确定创作策略**
   - 根据平台特点选择合适的风格和结构
   - 根据受众画像调整语言和表达方式
   - 根据情感倾向确定内容基调

3. **生成内容**
   
   **微信公众号：**
   - 标题：吸引人的标题（15-30字）
   - 引言：引出话题，激发兴趣（100-200字）
   - 正文：
     * 第一部分：背景介绍和现状分析（500-800字）
     * 第二部分：深度分析和数据支持（800-1200字）
     * 第三部分：趋势预测和建议（400-600字）
   - 结语：总结和呼吁（100-200字）
   - 配图建议：为文章提供3-5张配图的详细描述
   
   **微博：**
   - 核心观点：一句话总结（20-50字）
   - 展开说明：简要阐述（50-100字）
   - 话题标签：3-5个相关话题
   - 配图建议：1-3张吸引眼球的图片描述
   
   **抖音：**
   - 标题：吸引点击的标题（10-20字）
   - 分镜脚本：
     * 第1-5秒：开场吸引（痛点/悬念）
     * 第6-15秒：核心内容第一部分
     * 第16-30秒：核心内容第二部分
     * 第31-45秒：核心内容第三部分
     * 第46-60秒：总结和呼吁
   - 文案：每个分镜的配音文案
   - 视觉建议：每个分镜的画面描述
   
   **小红书：**
   - 标题：emoji + 吸引人的标题（15-25字）
   - 正文：
     * 开头：引出话题（50-100字）
     * 中间：核心内容（100-300字）
     * 结尾：总结和互动（50-100字）
   - 话题标签：5-8个相关话题
   - 配图建议：4-6张精美配图的详细描述

4. **质量检查**
   - 检查字数是否符合平台规范
   - 检查内容是否符合平台风格
   - 检查是否包含必要的元素（标题、标签等）
   - 确保内容原创、有价值、吸引人

**输出格式：**
```json
{
  "contents": {
    "wechat": {
      "platform": "wechat",
      "title": "文章标题",
      "content": "完整的文章正文（2000-3000字）",
      "images": [
        "配图1描述或URL",
        "配图2描述或URL",
        "配图3描述或URL"
      ],
      "hashtags": [],
      "metadata": {
        "word_count": 2500,
        "reading_time": "8分钟"
      },
      "timestamp": "2025-10-19T10:00:00"
    },
    "weibo": {
      "platform": "weibo",
      "title": null,
      "content": "微博文案（140-2000字）",
      "images": [
        "配图1描述或URL"
      ],
      "hashtags": ["#话题1", "#话题2", "#话题3"],
      "metadata": {
        "word_count": 150
      },
      "timestamp": "2025-10-19T10:00:00"
    },
    "douyin": {
      "platform": "douyin",
      "title": "视频标题",
      "content": "完整的视频脚本文案",
      "images": [
        "分镜1示意图",
        "分镜2示意图"
      ],
      "hashtags": ["#话题1", "#话题2"],
      "metadata": {
        "duration": "60秒",
        "scenes": [
          {
            "time": "0-5秒",
            "visual": "画面描述",
            "text": "配音文案"
          },
          {
            "time": "6-15秒",
            "visual": "画面描述",
            "text": "配音文案"
          }
        ]
      },
      "timestamp": "2025-10-19T10:00:00"
    },
    "xiaohongshu": {
      "platform": "xiaohongshu",
      "title": "📱 笔记标题",
      "content": "小红书笔记正文（200-500字）",
      "images": [
        "配图1描述",
        "配图2描述",
        "配图3描述",
        "配图4描述"
      ],
      "hashtags": ["#话题1", "#话题2", "#话题3", "#话题4"],
      "metadata": {
        "word_count": 350,
        "style": "种草/测评/分享"
      },
      "timestamp": "2025-10-19T10:00:00"
    }
  }
}
```

**注意事项：**
- 内容要原创，避免抄袭
- 语言要符合平台用户习惯
- 标题要吸引人但不夸张
- 配图要与内容相关
- 话题标签要准确相关
- 遵守平台内容规范
- 如果某个工具调用失败，记录错误并继续生成其他平台内容
"""
    # 动态附加：启用平台与风格要求（不在代码中硬编码）
    instructions += f"\n\n[动态配置]\n仅生成以下平台: {', '.join(enabled_platforms)}。{style_summary}\n严格输出 JSON，键为 contents，子键为各平台标识（如 wechat/weibo/bilibili）。\n"
    
    # 内容生成智能体不需要 MCP 工具，主要依靠 LLM 能力
    logger.info("内容生成智能体使用纯 LLM 模式，不依赖外部工具")
    
    # 创建 Agent（不使用工具）
    try:
        agent = ChatAgent(
            chat_client=chat_client,
            instructions=instructions,
            name="内容生成智能体",
            tools=[],  # 不使用外部工具
        )
        
        logger.info(f"✅ 内容生成智能体创建成功")
        logger.info(f"   模式: 纯 LLM 文本生成")
        logger.info(f"   Agent 名称: {agent.name}")
        return agent
        
    except Exception as e:
        logger.error(f"❌ 创建 Agent 失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def create_content_agent(chat_client, mcp_tool_configs: List = None):
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
        return create_content_agent_async(chat_client, mcp_tool_configs)
    except RuntimeError:
        # 没有运行中的 event loop，创建新的
        return asyncio.run(create_content_agent_async(chat_client, mcp_tool_configs))




def parse_content_response(response: str) -> Dict[str, Content]:
    """
    解析智能体响应，提取内容列表
    
    Args:
        response: 智能体的响应文本
        
    Returns:
        平台到内容对象的映射字典
    """
    try:
        # 尝试解析 JSON 响应
        if isinstance(response, str):
            cleaned = response.strip()
            if not cleaned:
                logger.error("内容响应为空字符串")
                return {}
            # 查找 JSON 代码块
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
            
            data = json.loads(json_str)
        else:
            data = response
        
        # 提取内容列表
        contents_data = data.get("contents", {})
        contents = {}
        
        for platform, content_data in contents_data.items():
            try:
                content = Content.from_dict(content_data)
                is_valid, error_msg = content.validate()
                
                if is_valid:
                    contents[platform] = content
                else:
                    logger.warning(f"平台 {platform} 的内容验证失败: {error_msg}")
                    
            except Exception as e:
                logger.error(f"解析平台 {platform} 的内容失败: {e}")
                continue
        
        logger.info(f"成功解析 {len(contents)} 个平台的内容")
        return contents
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        return {}
    except Exception as e:
        logger.error(f"解析内容响应失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def export_contents_to_json(contents: Dict[str, Content], output_path: str):
    """
    导出内容列表到 JSON 文件
    
    Args:
        contents: 平台到内容对象的映射字典
        output_path: 输出文件路径
    """
    try:
        data = {
            "contents": {platform: content.to_dict() for platform, content in contents.items()},
            "total_platforms": len(contents),
            "export_time": datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已导出 {len(contents)} 个平台的内容到: {output_path}")
        
    except Exception as e:
        logger.error(f"导出内容失败: {e}")
        raise


def get_content_by_platform(contents: Dict[str, Content], platform: str) -> Optional[Content]:
    """
    按平台获取内容
    
    Args:
        contents: 平台到内容对象的映射字典
        platform: 平台名称
        
    Returns:
        内容对象，如果不存在返回 None
    """
    return contents.get(platform)


def filter_contents_by_word_count(
    contents: Dict[str, Content], 
    min_words: int = 0, 
    max_words: int = float('inf')
) -> Dict[str, Content]:
    """
    按字数过滤内容
    
    Args:
        contents: 平台到内容对象的映射字典
        min_words: 最小字数
        max_words: 最大字数
        
    Returns:
        过滤后的内容字典
    """
    filtered = {
        platform: content 
        for platform, content in contents.items() 
        if min_words <= content.get_word_count() <= max_words
    }
    logger.info(f"过滤后保留 {len(filtered)}/{len(contents)} 个平台的内容（字数 {min_words}-{max_words}）")
    return filtered


def get_content_statistics(contents: Dict[str, Content]) -> Dict[str, Any]:
    """
    获取内容统计信息
    
    Args:
        contents: 平台到内容对象的映射字典
        
    Returns:
        统计信息字典
    """
    stats = {
        "total_platforms": len(contents),
        "platforms": list(contents.keys()),
        "total_words": sum(content.get_word_count() for content in contents.values()),
        "total_images": sum(len(content.images) for content in contents.values()),
        "total_hashtags": sum(len(content.hashtags) for content in contents.values()),
        "by_platform": {}
    }
    
    for platform, content in contents.items():
        stats["by_platform"][platform] = {
            "platform_name": content.get_platform_name(),
            "word_count": content.get_word_count(),
            "image_count": len(content.images),
            "hashtag_count": len(content.hashtags),
            "has_title": content.title is not None
        }
    
    return stats


def validate_all_contents(contents: Dict[str, Content]) -> Dict[str, tuple[bool, Optional[str]]]:
    """
    验证所有内容
    
    Args:
        contents: 平台到内容对象的映射字典
        
    Returns:
        平台到验证结果的映射字典
    """
    results = {}
    for platform, content in contents.items():
        is_valid, error_msg = content.validate()
        results[platform] = (is_valid, error_msg)
        
        if not is_valid:
            logger.warning(f"平台 {platform} 的内容验证失败: {error_msg}")
        else:
            logger.info(f"平台 {platform} 的内容验证通过")
    
    return results


def create_content_summary(contents: Dict[str, Content]) -> str:
    """
    创建内容摘要
    
    Args:
        contents: 平台到内容对象的映射字典
        
    Returns:
        摘要文本
    """
    stats = get_content_statistics(contents)
    
    summary = f"""
内容生成摘要
============

总计: {stats['total_platforms']} 个平台
总字数: {stats['total_words']} 字
总配图: {stats['total_images']} 张
总标签: {stats['total_hashtags']} 个

平台详情:
"""
    
    for platform, platform_stats in stats["by_platform"].items():
        summary += f"""
- {platform_stats['platform_name']}:
  * 字数: {platform_stats['word_count']}
  * 配图: {platform_stats['image_count']} 张
  * 标签: {platform_stats['hashtag_count']} 个
  * 标题: {'有' if platform_stats['has_title'] else '无'}
"""
    
    return summary
