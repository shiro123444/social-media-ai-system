"""
运行完整的小红书内容生产工作流
"""

import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    运行工作流
    """
    logger.info("=" * 80)
    logger.info("🚀 小红书内容生产工作流")
    logger.info("=" * 80)
    
    # 导入工作流
    from agents.social_media_workflow import workflow
    
    logger.info(f"✅ 工作流: {workflow.name}")
    logger.info(f"📝 描述: {workflow.description}")
    
    # 运行工作流
    query = "获取最新的AI技术热点，生成小红书文案并发布"
    
    logger.info(f"\n🔄 开始执行: {query}")
    logger.info("=" * 80)
    
    try:
        # 运行并等待完成
        result = await workflow.run(query)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ 工作流执行完成")
        logger.info("=" * 80)
        
        # 显示最终结果
        outputs = result.get_outputs()
        if outputs:
            logger.info(f"\n📤 工作流输出 ({len(outputs)} 条):")
            for i, output in enumerate(outputs, 1):
                logger.info(f"\n输出 {i}:\n{output}")
        
    except Exception as e:
        logger.error(f"\n❌ 执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
