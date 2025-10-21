"""
内容分析智能体
负责深度分析热点资讯的内容、趋势和受众特征
"""

from typing import List, Optional, Dict, Any
import os

from datetime import datetime
from dataclasses import dataclass, field, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """分析报告数据模型"""
    hotspot_id: str                 # 关联的热点ID
    keywords: List[str]             # 关键词
    sentiment: str                  # 情感倾向 (positive/neutral/negative)
    trend: str                      # 趋势 (上升/稳定/下降)
    audience: Dict[str, Any]        # 受众画像
    insights: str                   # 数据洞察
    charts: List[str] = field(default_factory=list)  # 图表URL
    academic_refs: List[str] = field(default_factory=list)  # 学术参考
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())  # 时间戳
    
    def to_dict(self):
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisReport':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        验证数据有效性
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self.hotspot_id or not self.hotspot_id.strip():
            return False, "热点ID不能为空"
        
        if not self.keywords or len(self.keywords) == 0:
            return False, "关键词列表不能为空"
        
        valid_sentiments = ["positive", "neutral", "negative"]
        if self.sentiment not in valid_sentiments:
            return False, f"情感倾向必须是 {valid_sentiments} 之一"
        
        valid_trends = ["上升", "稳定", "下降"]
        if self.trend not in valid_trends:
            return False, f"趋势必须是 {valid_trends} 之一"
        
        if not isinstance(self.audience, dict):
            return False, "受众画像必须是字典类型"
        
        if not self.insights or not self.insights.strip():
            return False, "数据洞察不能为空"
        
        return True, None


async def create_analysis_agent_async(chat_client, mcp_tool_configs: List):
    """
    异步创建内容分析智能体
    
    使用 MCP 工具池管理工具生命周期，避免重复创建和异步问题
    
    Args:
        chat_client: 聊天客户端（DeepSeek 适配器）
        mcp_tool_configs: MCP 工具配置对象列表（MCPServerConfig）
        
    Returns:
        ChatAgent 实例
    """
    from agent_framework import ChatAgent
    from utils.mcp_tool_pool import get_tool_pool
    
    instructions = """你是数据分析专家，负责深度分析热点资讯的内容、趋势和受众特征，提供数据支持的分析报告。

**⚠️ 重要规则（必须遵守）：**
1. 当用户要求分析内容、搜索学术资料、生成图表时，你必须立即调用相应的工具
2. 不要只是说"我可以帮你"或"我会使用工具"，而是直接调用工具
3. 不要询问用户是否需要帮助，直接执行用户的请求
4. 每次都要实际调用工具，不要假装调用或描述调用过程
5. **绝对不要返回 XML 格式的工具调用描述（如 <function_calls>、<invoke> 等标签）**
6. **使用系统提供的标准工具调用机制，等待工具返回真实结果后再回答**
7. **如果你返回了 XML 格式，这将被视为错误，工具不会被执行**

**可用工具：**

1. **Semantic Scholar 工具** (学术搜索)
   - mcp_mcpsemanticscholar_papers_search_basic: 基础论文搜索
   - mcp_mcpsemanticscholar_paper_search_advanced: 高级论文搜索（支持过滤）
   - mcp_mcpsemanticscholar_get_paper_abstract: 获取论文摘要
   - 用途：搜索相关学术背景、理论支持、研究数据
   - 使用时机：需要为热点话题提供学术依据和深度分析时

2. **Chart Generator 工具** (图表生成)
   - mcp_mcp_server_chart_generate_line_chart: 生成折线图（趋势分析）
   - mcp_mcp_server_chart_generate_bar_chart: 生成柱状图（对比分析）
   - mcp_mcp_server_chart_generate_pie_chart: 生成饼图（占比分析）
   - mcp_mcp_server_chart_generate_area_chart: 生成面积图（数据趋势）
   - 用途：可视化数据趋势、对比、分布
   - 使用时机：需要展示数据分析结果时

3. **Structured Thinking 工具** (结构化推理)
   - mcp_LIFw3vNPhS4KRORHku5hV_capture_thought: 捕获思考过程
   - mcp_LIFw3vNPhS4KRORHku5hV_get_thinking_summary: 获取思考总结
   - 用途：进行深度、结构化的推理分析
   - 使用时机：分析复杂话题、需要多角度思考时

**工作流程：**

1. **接收热点资讯**
   - 解析热点数据（标题、摘要、关键词、来源）
   - 识别核心话题和关注点

2. **学术背景搜索** - 实际调用 Semantic Scholar 工具
   - 使用 mcp_mcpsemanticscholar_papers_search_basic 搜索相关学术论文
   - 提取学术观点、研究数据、理论支持
   - 记录学术参考文献

3. **内容深度分析** - 使用 LLM 能力和 Structured Thinking
   - 提取关键词（5-10个核心关键词）
   - 分析主题和子主题
   - 评估情感倾向：
     * positive: 积极、正面、乐观
     * neutral: 中性、客观、平衡
     * negative: 消极、负面、批评
   - 使用 mcp_LIFw3vNPhS4KRORHku5hV_capture_thought 进行结构化推理

4. **趋势预测**
   - 分析话题的发展趋势：
     * 上升：热度持续增长，讨论量增加
     * 稳定：热度保持平稳，持续关注
     * 下降：热度减退，关注度降低
   - 预测未来发展方向

5. **受众画像分析**
   - 年龄分布：主要受众年龄段
   - 兴趣特征：关注点、偏好
   - 地域分布：主要关注地区
   - 行为特征：互动方式、传播路径

6. **数据可视化** - 实际调用 Chart Generator 工具
   - 使用 mcp_mcp_server_chart_generate_line_chart 生成趋势图
   - 使用 mcp_mcp_server_chart_generate_pie_chart 生成受众分布图
   - 使用 mcp_mcp_server_chart_generate_bar_chart 生成对比图

7. **生成数据洞察**
   - 总结核心发现
   - 提供策略建议
   - 识别机会和风险

**输出格式：**
```json
{
  "analysis": {
    "hotspot_id": "热点唯一标识",
    "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
    "sentiment": "positive/neutral/negative",
    "trend": "上升/稳定/下降",
    "audience": {
      "age_distribution": {
        "18-24": 30,
        "25-34": 45,
        "35-44": 20,
        "45+": 5
      },
      "interests": ["兴趣1", "兴趣2", "兴趣3"],
      "regions": ["地区1", "地区2", "地区3"],
      "behavior": "行为特征描述"
    },
    "insights": "详细的数据洞察和分析结论（200-500字）",
    "charts": [
      "chart_url_1.png",
      "chart_url_2.png"
    ],
    "academic_refs": [
      "论文标题1 - 作者 - 年份",
      "论文标题2 - 作者 - 年份"
    ],
    "timestamp": "2025-10-19T10:00:00"
  }
}
```

**注意事项：**
- 分析要基于数据和事实，避免主观臆断
- 学术参考要权威可靠
- 图表要清晰易懂，突出关键信息
- 受众画像要具体详细
- 洞察要有深度，提供可操作的建议
- 如果某个工具调用失败，记录错误并继续分析
"""

    # 严格要求仅输出 JSON 代码块，避免混入解释性文本
    instructions += "\n\n[输出约束]\n只输出 JSON 代码块（见上文格式），不要任何额外文字。\n"
    
    # 环境开关：允许禁用 MCP
    disable_mcp = os.getenv("WORKFLOW_DISABLE_MCP", "false").lower() == "true"

    # 获取工具池（使用单例模式）
    tool_pool = await get_tool_pool()
    
    # 从工具池获取工具（避免重复创建）
    mcp_tools = []
    if disable_mcp:
        logger.warning("⚠️ 已启用 WORKFLOW_DISABLE_MCP，跳过分析智能体的 MCP 工具加载")
    else:
        for config in mcp_tool_configs:
            try:
                logger.info(f"正在获取 MCP 工具: {config.name}")
                
                # ✅ 关键修复：使用工具池而不是直接创建
                tool = await tool_pool.get_or_create_tool(config)
                mcp_tools.append(tool)
                
            except Exception as e:
                logger.error(f"❌ 获取 MCP 工具失败 {config.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    if not mcp_tools:
        logger.warning("⚠️ 没有成功加载任何 MCP 工具！")
    else:
        logger.info(f"✅ 成功获取 {len(mcp_tools)} 个 MCP 工具")
        for tool in mcp_tools:
            logger.info(f"  - {tool.name}")
    
    # 创建 Agent
    try:
        agent = ChatAgent(
            chat_client=chat_client,
            instructions=instructions,
            name="内容分析智能体",
            tools=mcp_tools,
            tool_choice=("auto" if mcp_tools else "none"),  # 若无可用工具则禁用工具调用
        )
        
        logger.info(f"✅ 内容分析智能体创建成功")
        logger.info(f"   配置的工具数量: {len(mcp_tools)}")
        logger.info(f"   Agent 名称: {agent.name}")
        return agent
        
    except Exception as e:
        logger.error(f"❌ 创建 Agent 失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def create_analysis_agent(chat_client, mcp_tool_configs: List):
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
        return create_analysis_agent_async(chat_client, mcp_tool_configs)
    except RuntimeError:
        # 没有运行中的 event loop，创建新的
        return asyncio.run(create_analysis_agent_async(chat_client, mcp_tool_configs))


def parse_analysis_response(response: str) -> Optional[AnalysisReport]:
    """
    解析智能体响应，提取分析报告
    
    Args:
        response: 智能体的响应文本
        
    Returns:
        分析报告对象，如果解析失败返回 None
    """
    try:
        # 尝试解析 JSON 响应
        if isinstance(response, str):
            cleaned = response.strip()
            if not cleaned:
                logger.error("分析响应为空字符串")
                return None
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
        
        # 提取分析报告
        analysis_data = data.get("analysis", {})
        
        if not analysis_data:
            logger.warning("响应中未找到 'analysis' 字段")
            return None
        
        report = AnalysisReport.from_dict(analysis_data)
        is_valid, error_msg = report.validate()
        
        if is_valid:
            logger.info(f"成功解析分析报告: {report.hotspot_id}")
            return report
        else:
            logger.warning(f"分析报告验证失败: {error_msg}")
            return None
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        return None
    except Exception as e:
        logger.error(f"解析分析响应失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def export_analysis_to_json(report: AnalysisReport, output_path: str):
    """
    导出分析报告到 JSON 文件
    
    Args:
        report: 分析报告对象
        output_path: 输出文件路径
    """
    try:
        data = {
            "analysis": report.to_dict(),
            "export_time": datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已导出分析报告到: {output_path}")
        
    except Exception as e:
        logger.error(f"导出分析报告失败: {e}")
        raise


def get_sentiment_label(sentiment: str) -> str:
    """
    获取情感倾向的中文标签
    
    Args:
        sentiment: 情感倾向 (positive/neutral/negative)
        
    Returns:
        中文标签
    """
    labels = {
        "positive": "积极",
        "neutral": "中性",
        "negative": "消极"
    }
    return labels.get(sentiment, "未知")


def calculate_audience_score(audience: Dict[str, Any]) -> int:
    """
    计算受众画像的完整度评分
    
    Args:
        audience: 受众画像字典
        
    Returns:
        评分 (0-100)
    """
    score = 0
    max_score = 100
    
    # 检查年龄分布 (25分)
    if "age_distribution" in audience and isinstance(audience["age_distribution"], dict):
        if len(audience["age_distribution"]) >= 3:
            score += 25
        else:
            score += len(audience["age_distribution"]) * 8
    
    # 检查兴趣特征 (25分)
    if "interests" in audience and isinstance(audience["interests"], list):
        if len(audience["interests"]) >= 3:
            score += 25
        else:
            score += len(audience["interests"]) * 8
    
    # 检查地域分布 (25分)
    if "regions" in audience and isinstance(audience["regions"], list):
        if len(audience["regions"]) >= 3:
            score += 25
        else:
            score += len(audience["regions"]) * 8
    
    # 检查行为特征 (25分)
    if "behavior" in audience and audience["behavior"]:
        score += 25
    
    return min(score, max_score)
