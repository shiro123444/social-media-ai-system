"""
内容生成智能体测试
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import logging
from agents.content_agent import (
    Content,
    create_content_agent_async,
    parse_content_response,
    get_content_statistics,
    validate_all_contents,
    create_content_summary
)
from config.mcp_config_manager import MCPConfigManager
from utils.deepseek_adapter import DeepSeekChatClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_content_data_model():
    """测试内容数据模型"""
    logger.info("=" * 60)
    logger.info("测试 1: 内容数据模型")
    logger.info("=" * 60)
    
    # 测试微信公众号内容
    base_text = "随着人工智能技术的快速发展，内容创作领域正在经历一场深刻的变革。从文本生成到图像创作，从视频编辑到音乐制作，AI正在各个方面提升创作效率和质量。本文将深入探讨AI技术在内容创作中的应用，以及它给创作者带来的机遇和挑战。"
    wechat_content = Content(
        platform="wechat",
        title="AI技术如何改变内容创作",
        content=base_text * 10,  # 确保超过500字
        images=["image1.jpg", "image2.jpg", "image3.jpg"],
        hashtags=[],
        metadata={"word_count": 2500, "reading_time": "8分钟"}
    )
    
    is_valid, error_msg = wechat_content.validate()
    logger.info(f"微信公众号内容验证: {'✅ 通过' if is_valid else f'❌ 失败 - {error_msg}'}")
    logger.info(f"  平台: {wechat_content.get_platform_name()}")
    logger.info(f"  字数: {wechat_content.get_word_count()}")
    
    # 测试微博内容
    weibo_content = Content(
        platform="weibo",
        title=None,
        content="AI技术正在改变内容创作的方式，让创作更高效、更智能。#AI技术 #内容创作",
        images=["image1.jpg"],
        hashtags=["#AI技术", "#内容创作"],
        metadata={"word_count": 50}
    )
    
    is_valid, error_msg = weibo_content.validate()
    logger.info(f"微博内容验证: {'✅ 通过' if is_valid else f'❌ 失败 - {error_msg}'}")
    
    # 测试抖音内容
    douyin_content = Content(
        platform="douyin",
        title="60秒看懂AI内容创作",
        content="完整的视频脚本文案...",
        images=["scene1.jpg", "scene2.jpg"],
        hashtags=["#AI", "#内容创作"],
        metadata={
            "duration": "60秒",
            "scenes": [
                {"time": "0-5秒", "visual": "开场画面", "text": "你知道吗？"},
                {"time": "6-15秒", "visual": "核心内容", "text": "AI正在改变创作"}
            ]
        }
    )
    
    is_valid, error_msg = douyin_content.validate()
    logger.info(f"抖音内容验证: {'✅ 通过' if is_valid else f'❌ 失败 - {error_msg}'}")
    
    # 测试小红书内容
    xiaohongshu_content = Content(
        platform="xiaohongshu",
        title="📱 AI内容创作工具推荐",
        content="最近发现了几个超好用的AI内容创作工具，真的太方便了！" * 5,  # 确保超过50字
        images=["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"],
        hashtags=["#AI工具", "#内容创作", "#效率提升"],
        metadata={"word_count": 350, "style": "种草"}
    )
    
    is_valid, error_msg = xiaohongshu_content.validate()
    logger.info(f"小红书内容验证: {'✅ 通过' if is_valid else f'❌ 失败 - {error_msg}'}")
    
    # 测试统计功能
    contents = {
        "wechat": wechat_content,
        "weibo": weibo_content,
        "douyin": douyin_content,
        "xiaohongshu": xiaohongshu_content
    }
    
    stats = get_content_statistics(contents)
    logger.info(f"\n内容统计:")
    logger.info(f"  总平台数: {stats['total_platforms']}")
    logger.info(f"  总字数: {stats['total_words']}")
    logger.info(f"  总配图: {stats['total_images']}")
    logger.info(f"  总标签: {stats['total_hashtags']}")
    
    # 测试验证所有内容
    validation_results = validate_all_contents(contents)
    all_valid = all(result[0] for result in validation_results.values())
    logger.info(f"\n所有内容验证: {'✅ 全部通过' if all_valid else '❌ 部分失败'}")
    
    # 测试创建摘要
    summary = create_content_summary(contents)
    logger.info(f"\n{summary}")
    
    logger.info("\n✅ 数据模型测试完成\n")


async def test_content_agent_creation():
    """测试内容生成智能体创建"""
    logger.info("=" * 60)
    logger.info("测试 2: 内容生成智能体创建")
    logger.info("=" * 60)
    
    try:
        # 创建 DeepSeek 客户端
        deepseek_client = DeepSeekChatClient()
        
        # 创建内容生成智能体（不需要工具配置）
        logger.info("正在创建内容生成智能体（纯 LLM 模式）...")
        agent = await create_content_agent_async(deepseek_client)
        
        logger.info(f"✅ 内容生成智能体创建成功")
        logger.info(f"   Agent 名称: {agent.name}")
        logger.info(f"   模式: 纯 LLM 文本生成")
        
        logger.info("\n✅ 智能体创建测试完成\n")
        
    except Exception as e:
        logger.error(f"❌ 智能体创建测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


def test_parse_content_response():
    """测试解析内容响应"""
    logger.info("=" * 60)
    logger.info("测试 3: 解析内容响应")
    logger.info("=" * 60)
    
    # 模拟智能体响应
    mock_response = """
```json
{
  "contents": {
    "wechat": {
      "platform": "wechat",
      "title": "AI技术如何改变内容创作",
      "content": "随着人工智能技术的快速发展，内容创作领域正在经历一场深刻的变革。从文本生成到图像创作，从视频编辑到音乐制作，AI正在各个方面提升创作效率和质量。本文将深入探讨AI技术在内容创作中的应用，以及它给创作者带来的机遇和挑战。\\n\\n一、AI文本生成技术\\n\\nAI文本生成技术已经相当成熟，可以帮助创作者快速生成高质量的文章、报告和创意文案。这些工具不仅能够理解上下文，还能根据特定风格和语气进行创作。\\n\\n二、AI图像创作\\n\\n从DALL-E到Midjourney，AI图像生成工具让每个人都能成为艺术家。只需输入文字描述，就能生成令人惊叹的视觉作品。\\n\\n三、未来展望\\n\\nAI技术将继续发展，为内容创作带来更多可能性。创作者需要学会与AI协作，发挥各自优势，创造出更优秀的作品。",
      "images": ["ai_text_generation.jpg", "ai_image_creation.jpg", "future_outlook.jpg"],
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
      "content": "AI技术正在改变内容创作的方式！从文本到图像，从视频到音乐，AI让创作更高效、更智能。未来，创作者需要学会与AI协作，发挥各自优势。#AI技术 #内容创作 #人工智能",
      "images": ["weibo_cover.jpg"],
      "hashtags": ["#AI技术", "#内容创作", "#人工智能"],
      "metadata": {
        "word_count": 80
      },
      "timestamp": "2025-10-19T10:00:00"
    }
  }
}
```
"""
    
    contents = parse_content_response(mock_response)
    
    if contents:
        logger.info(f"✅ 成功解析 {len(contents)} 个平台的内容")
        for platform, content in contents.items():
            logger.info(f"\n平台: {content.get_platform_name()}")
            logger.info(f"  标题: {content.title}")
            logger.info(f"  字数: {content.get_word_count()}")
            logger.info(f"  配图: {len(content.images)} 张")
            logger.info(f"  标签: {len(content.hashtags)} 个")
    else:
        logger.error("❌ 解析失败")
    
    logger.info("\n✅ 解析测试完成\n")


def main():
    """主测试函数"""
    logger.info("\n" + "=" * 60)
    logger.info("开始测试内容生成智能体")
    logger.info("=" * 60 + "\n")
    
    # 测试 1: 数据模型
    test_content_data_model()
    
    # 测试 2: 智能体创建（异步）
    asyncio.run(test_content_agent_creation())
    
    # 测试 3: 解析响应
    test_parse_content_response()
    
    logger.info("=" * 60)
    logger.info("所有测试完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
