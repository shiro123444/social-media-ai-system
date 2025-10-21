# 设计文档 - 基于 MCP 的多智能体热点资讯分析系统

## 概述

本系统采用 Microsoft Agent Framework 构建，使用标准的 stdio MCP 服务器作为工具提供者，通过 JSON 配置文件管理所有 MCP 服务。系统包含 5 个专业智能体，通过 WorkflowBuilder 编排协作流程，使用 DeepSeek API 作为 LLM 后端，提供 DevUI 可视化界面。

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  DevUI Web   │  │  CLI 接口    │  │  API 接口    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    工作流编排层                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           WorkflowBuilder (顺序/并行/条件)            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     智能体层                                 │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │热点  │→ │内容  │→ │内容  │→ │内容  │→ │发布  │        │
│  │获取  │  │分析  │  │生成  │  │审核  │  │管理  │        │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP 工具层                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │RSS Reader│ │Exa Search│ │Fetch     │ │Word Doc  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Chart Gen │ │Browserbase│ │OKPPT     │ │Semantic  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   基础设施层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │DeepSeek API  │  │配置管理      │  │日志系统      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```


## 核心组件设计

### 1. MCP 配置管理器 (MCPConfigManager)

**职责：** 加载和管理所有 MCP 服务器配置

**设计：**
```python
class MCPConfigManager:
    """MCP 配置管理器"""
    
    def __init__(self, config_path: str = "config/mcp_servers.json"):
        self.config_path = config_path
        self.servers = {}
        
    def load_config(self) -> Dict[str, MCPServerConfig]:
        """从 JSON 文件加载 MCP 服务器配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        for name, server_config in config['mcpServers'].items():
            if server_config.get('isActive', True):
                self.servers[name] = MCPServerConfig(
                    name=server_config['name'],
                    type=server_config['type'],  # stdio
                    command=server_config['command'],
                    args=server_config['args'],
                    env=server_config.get('env', {})
                )
        return self.servers
    
    def get_tools_for_agent(self, agent_name: str) -> List[str]:
        """获取指定智能体可用的 MCP 工具列表"""
        # 根据智能体名称返回对应的 MCP 工具
        pass
```

**配置文件格式：**
```json
{
  "mcpServers": {
    "rss-reader": {
      "isActive": true,
      "name": "rss-reader",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "rss-reader-mcp"]
    },
    "exa": {
      "isActive": true,
      "name": "exa",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@smithery/cli@latest", "run", "exa"]
    }
  }
}
```


### 2. 智能体设计

#### 2.1 热点获取智能体 (HotspotAgent)

**职责：** 从多个来源获取热点资讯并进行初步筛选

**MCP 工具：**
- `mcp_rss-reader`: 获取 RSS 新闻源
- `mcp_exa_web_search_exa`: 搜索热点话题热度
- `mcp_sSojaYGl4gu83ycBRTn1r_fetch`: 获取详细内容

**实现：**
```python
def create_hotspot_agent(chat_client, mcp_tools: List[str]) -> ChatAgent:
    """创建热点获取智能体"""
    return ChatAgent(
        name="热点获取智能体",
        chat_client=chat_client,
        instructions="""你是热点资讯分析专家。

工作流程：
1. 使用 RSS Reader 获取多个新闻源的最新资讯
2. 使用 Exa Search 验证话题热度和传播范围
3. 使用 Fetch 获取高热度话题的详细内容
4. 输出结构化的热点列表

输出格式：
{
  "hotspots": [
    {
      "title": "话题标题",
      "source": "来源",
      "heat_index": 95,
      "summary": "摘要",
      "url": "链接"
    }
  ]
}""",
        tools=mcp_tools  # 从 MCP 配置管理器获取
    )
```

#### 2.2 内容分析智能体 (AnalysisAgent)

**职责：** 深度分析热点内容，提供数据支持的洞察

**MCP 工具：**
- `mcp_mcpsemanticscholar`: 搜索学术背景
- `mcp_mcp_server_chart_generate_*`: 生成数据图表
- `mcp_LIFw3vNPhS4KRORHku5hV_capture_thought`: 结构化推理

**实现：**
```python
def create_analysis_agent(chat_client, mcp_tools: List[str]) -> ChatAgent:
    """创建内容分析智能体"""
    return ChatAgent(
        name="内容分析智能体",
        chat_client=chat_client,
        instructions="""你是数据分析专家。

工作流程：
1. 接收热点资讯列表
2. 使用 Semantic Scholar 搜索相关学术背景
3. 提取关键词、主题和情感倾向
4. 使用 Chart Generator 生成趋势图表
5. 使用 Structured Thinking 进行深度推理

输出格式：
{
  "analysis": {
    "keywords": ["关键词1", "关键词2"],
    "sentiment": "positive/neutral/negative",
    "trend": "上升/稳定/下降",
    "audience": "目标受众画像",
    "insights": "数据洞察",
    "charts": ["图表URL1", "图表URL2"]
  }
}""",
        tools=mcp_tools
    )
```


#### 2.3 内容生成智能体 (ContentAgent)

**职责：** 根据分析结果生成多平台适配的内容

**MCP 工具：**
- `mcp_word_document_server_*`: 创建专业文档
- `mcp_okppt_*`: 生成配图方案
- `mcp_mcp_browserbase_*`: 搜索参考图片

**实现：**
```python
def create_content_agent(chat_client, mcp_tools: List[str]) -> ChatAgent:
    """创建内容生成智能体"""
    return ChatAgent(
        name="内容生成智能体",
        chat_client=chat_client,
        instructions="""你是专业内容创作者。

支持的平台：
- 微信公众号：2000-3000字，深度内容
- 微博：140字以内，话题标签
- 抖音：60秒视频脚本，分镜设计
- 小红书：200-500字，配图方案

工作流程：
1. 接收分析报告
2. 根据平台特点生成不同风格的内容
3. 使用 Word Document 创建长文
4. 使用 OKPPT 生成配图方案
5. 使用 Browserbase 搜索参考图片

输出格式：
{
  "contents": {
    "wechat": {
      "title": "标题",
      "content": "正文",
      "images": ["图片方案"]
    },
    "weibo": {
      "text": "微博文案",
      "hashtags": ["#话题1", "#话题2"]
    }
  }
}""",
        tools=mcp_tools
    )
```

#### 2.4 内容审核智能体 (ReviewAgent)

**职责：** 检查内容质量、合规性和品牌一致性

**MCP 工具：**
- 主要使用 LLM 能力进行审核
- 可选：使用外部审核 API

**实现：**
```python
def create_review_agent(chat_client) -> ChatAgent:
    """创建内容审核智能体"""
    return ChatAgent(
        name="内容审核智能体",
        chat_client=chat_client,
        instructions="""你是内容审核专家。

审核维度：
1. 语言风格：专业性、可读性、语法正确性
2. 情感倾向：积极、中性、消极
3. 品牌调性：是否符合品牌形象
4. 合规性：敏感词、违规内容、法律风险

审核流程：
1. 检查语言质量和逻辑连贯性
2. 检测敏感词和违规内容
3. 评估品牌一致性
4. 为内容打分（0-100）

输出格式：
{
  "review": {
    "passed": true/false,
    "score": 85,
    "issues": [
      {
        "type": "语法错误",
        "location": "第3段",
        "suggestion": "修改建议"
      }
    ],
    "recommendation": "通过/修改后通过/不通过"
  }
}""",
        tools=[]  # 主要使用 LLM 能力
    )
```


#### 2.5 发布管理智能体 (PublishAgent)

**职责：** 管理内容发布计划和状态

**MCP 工具：**
- `mcp_mcp_server_chart_generate_*`: 可视化发布时间表
- `mcp_mcp_browserbase_*`: 访问平台后台
- `mcp_desktop_commander_*`: 执行发布操作

**实现：**
```python
def create_publish_agent(chat_client, mcp_tools: List[str]) -> ChatAgent:
    """创建发布管理智能体"""
    return ChatAgent(
        name="发布管理智能体",
        chat_client=chat_client,
        instructions="""你是发布管理专家。

工作流程：
1. 接收审核通过的内容
2. 根据平台特点和时间策略制定发布计划
3. 使用 Chart Generator 可视化发布时间表
4. 使用 Browserbase 访问平台后台
5. 记录发布状态和结果

发布策略：
- 微信公众号：工作日 8:00-9:00 或 18:00-19:00
- 微博：全天候，高峰期 12:00-13:00, 20:00-22:00
- 抖音：晚上 19:00-22:00
- 小红书：周末 10:00-12:00, 15:00-17:00

输出格式：
{
  "publish_plan": {
    "wechat": {
      "scheduled_time": "2025-10-19 08:00:00",
      "status": "scheduled/published/failed"
    },
    "weibo": {
      "scheduled_time": "2025-10-19 12:00:00",
      "status": "scheduled"
    }
  }
}""",
        tools=mcp_tools
    )
```

### 3. 工作流编排设计

#### 3.1 顺序工作流 (Sequential Workflow)

**适用场景：** 完整的内容生产流程

**流程：**
```
热点获取 → 内容分析 → 内容生成 → 内容审核 → 发布管理
```

**实现：**
```python
def create_sequential_workflow(chat_client, mcp_config) -> WorkflowBuilder:
    """创建顺序工作流"""
    # 创建智能体
    hotspot_agent = create_hotspot_agent(
        chat_client, 
        mcp_config.get_tools_for_agent("hotspot")
    )
    analysis_agent = create_analysis_agent(
        chat_client,
        mcp_config.get_tools_for_agent("analysis")
    )
    content_agent = create_content_agent(
        chat_client,
        mcp_config.get_tools_for_agent("content")
    )
    review_agent = create_review_agent(chat_client)
    publish_agent = create_publish_agent(
        chat_client,
        mcp_config.get_tools_for_agent("publish")
    )
    
    # 构建工作流
    workflow = (WorkflowBuilder()
        .set_start_executor(hotspot_agent)
        .add_edge(hotspot_agent, analysis_agent)
        .add_edge(analysis_agent, content_agent)
        .add_edge(content_agent, review_agent)
        .add_edge(review_agent, publish_agent)
        .build())
    
    return workflow
```


#### 3.2 并行工作流 (Parallel Workflow)

**适用场景：** 多平台同时生成内容

**流程：**
```
热点获取 → 内容分析 → ┌→ 微信内容生成 ┐
                      ├→ 微博内容生成 ├→ 内容审核 → 发布管理
                      └→ 抖音内容生成 ┘
```

**实现：**
```python
def create_parallel_workflow(chat_client, mcp_config) -> WorkflowBuilder:
    """创建并行工作流"""
    hotspot_agent = create_hotspot_agent(
        chat_client,
        mcp_config.get_tools_for_agent("hotspot")
    )
    analysis_agent = create_analysis_agent(
        chat_client,
        mcp_config.get_tools_for_agent("analysis")
    )
    
    # 创建多个平台专用的内容生成智能体
    wechat_agent = ChatAgent(
        name="微信内容生成",
        chat_client=chat_client,
        instructions="专注生成微信公众号文章...",
        tools=mcp_config.get_tools_for_agent("content")
    )
    
    weibo_agent = ChatAgent(
        name="微博内容生成",
        chat_client=chat_client,
        instructions="专注生成微博短文...",
        tools=[]
    )
    
    douyin_agent = ChatAgent(
        name="抖音内容生成",
        chat_client=chat_client,
        instructions="专注生成抖音视频脚本...",
        tools=[]
    )
    
    review_agent = create_review_agent(chat_client)
    publish_agent = create_publish_agent(
        chat_client,
        mcp_config.get_tools_for_agent("publish")
    )
    
    # 构建并行工作流
    workflow = (WorkflowBuilder()
        .set_start_executor(hotspot_agent)
        .add_edge(hotspot_agent, analysis_agent)
        .add_edge(analysis_agent, wechat_agent)
        .add_edge(analysis_agent, weibo_agent)
        .add_edge(analysis_agent, douyin_agent)
        .add_edge(wechat_agent, review_agent)
        .add_edge(weibo_agent, review_agent)
        .add_edge(douyin_agent, review_agent)
        .add_edge(review_agent, publish_agent)
        .build())
    
    return workflow
```

#### 3.3 条件工作流 (Conditional Workflow)

**适用场景：** 根据审核结果决定下一步

**流程：**
```
热点获取 → 内容分析 → 内容生成 → 内容审核 ┬→ [通过] → 发布管理
                                        └→ [不通过] → 内容生成（重新生成）
```

**实现：**
```python
def create_conditional_workflow(chat_client, mcp_config) -> WorkflowBuilder:
    """创建条件工作流"""
    # 创建智能体
    hotspot_agent = create_hotspot_agent(
        chat_client,
        mcp_config.get_tools_for_agent("hotspot")
    )
    analysis_agent = create_analysis_agent(
        chat_client,
        mcp_config.get_tools_for_agent("analysis")
    )
    content_agent = create_content_agent(
        chat_client,
        mcp_config.get_tools_for_agent("content")
    )
    review_agent = create_review_agent(chat_client)
    publish_agent = create_publish_agent(
        chat_client,
        mcp_config.get_tools_for_agent("publish")
    )
    
    # 定义条件函数
    def review_passed(context) -> bool:
        """检查审核是否通过"""
        review_result = context.get_last_output()
        return review_result.get("review", {}).get("passed", False)
    
    # 构建条件工作流
    workflow = (WorkflowBuilder()
        .set_start_executor(hotspot_agent)
        .add_edge(hotspot_agent, analysis_agent)
        .add_edge(analysis_agent, content_agent)
        .add_edge(content_agent, review_agent)
        .add_edge(review_agent, publish_agent, condition=review_passed)
        .add_edge(review_agent, content_agent, condition=lambda ctx: not review_passed(ctx))
        .build())
    
    return workflow
```


## 数据模型

### 热点资讯模型
```python
@dataclass
class Hotspot:
    """热点资讯数据模型"""
    title: str              # 标题
    source: str             # 来源
    heat_index: int         # 热度指数 (0-100)
    summary: str            # 摘要
    url: str                # 链接
    keywords: List[str]     # 关键词
    timestamp: datetime     # 时间戳
    category: str           # 分类（科技/财经/娱乐等）
```

### 分析报告模型
```python
@dataclass
class AnalysisReport:
    """分析报告数据模型"""
    hotspot_id: str                 # 关联的热点ID
    keywords: List[str]             # 关键词
    sentiment: str                  # 情感倾向
    trend: str                      # 趋势
    audience: Dict[str, Any]        # 受众画像
    insights: str                   # 数据洞察
    charts: List[str]               # 图表URL
    academic_refs: List[str]        # 学术参考
    timestamp: datetime             # 时间戳
```

### 内容模型
```python
@dataclass
class Content:
    """内容数据模型"""
    platform: str           # 平台（wechat/weibo/douyin等）
    title: Optional[str]    # 标题（长文需要）
    content: str            # 正文
    images: List[str]       # 图片URL列表
    hashtags: List[str]     # 话题标签
    metadata: Dict[str, Any]  # 平台特定元数据
    timestamp: datetime     # 创建时间
```

### 审核结果模型
```python
@dataclass
class ReviewResult:
    """审核结果数据模型"""
    content_id: str         # 关联的内容ID
    passed: bool            # 是否通过
    score: int              # 评分 (0-100)
    issues: List[Dict[str, str]]  # 问题列表
    recommendation: str     # 建议（通过/修改后通过/不通过）
    reviewer: str           # 审核者
    timestamp: datetime     # 审核时间
```

### 发布计划模型
```python
@dataclass
class PublishPlan:
    """发布计划数据模型"""
    content_id: str         # 关联的内容ID
    platform: str           # 发布平台
    scheduled_time: datetime  # 计划发布时间
    status: str             # 状态（scheduled/published/failed）
    result: Optional[Dict[str, Any]]  # 发布结果
    retry_count: int        # 重试次数
    timestamp: datetime     # 创建时间
```


## 错误处理

### MCP 服务器连接错误
```python
class MCPConnectionError(Exception):
    """MCP 服务器连接错误"""
    pass

def handle_mcp_connection_error(error: MCPConnectionError, max_retries: int = 3):
    """处理 MCP 连接错误"""
    for attempt in range(max_retries):
        try:
            # 重试连接
            reconnect_mcp_server()
            return
        except MCPConnectionError:
            if attempt == max_retries - 1:
                logger.error(f"MCP 服务器连接失败，已重试 {max_retries} 次")
                raise
            time.sleep(2 ** attempt)  # 指数退避
```

### 智能体执行错误
```python
class AgentExecutionError(Exception):
    """智能体执行错误"""
    pass

async def safe_agent_run(agent: ChatAgent, input_data: str) -> Any:
    """安全执行智能体"""
    try:
        result = await agent.run(input_data)
        return result
    except Exception as e:
        logger.error(f"智能体 {agent.name} 执行失败: {e}")
        # 记录错误上下文
        log_agent_error(agent.name, input_data, str(e))
        raise AgentExecutionError(f"智能体执行失败: {e}")
```

### 工作流执行错误
```python
async def safe_workflow_run(workflow, input_data: str) -> Any:
    """安全执行工作流"""
    try:
        events = await workflow.run(input_data)
        return events
    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        # 保存工作流状态用于恢复
        save_workflow_state(workflow, input_data)
        raise
```

## 测试策略

### 单元测试
- 测试每个智能体的独立功能
- 测试 MCP 配置管理器的加载和解析
- 测试数据模型的序列化和反序列化

### 集成测试
- 测试智能体与 MCP 工具的集成
- 测试工作流的端到端执行
- 测试错误处理和重试机制

### 性能测试
- 测试并发工作流的性能
- 测试 MCP 工具调用的延迟
- 测试系统在高负载下的稳定性

### 测试工具
```python
# 模拟 MCP 工具响应
class MockMCPTool:
    def __init__(self, name: str, response: Any):
        self.name = name
        self.response = response
    
    async def call(self, *args, **kwargs):
        return self.response

# 测试智能体
async def test_hotspot_agent():
    mock_rss = MockMCPTool("rss-reader", {"items": [...]})
    mock_exa = MockMCPTool("exa", {"results": [...]})
    
    agent = create_hotspot_agent(
        chat_client=MockChatClient(),
        mcp_tools=[mock_rss, mock_exa]
    )
    
    result = await agent.run("获取科技热点")
    assert "hotspots" in result
```


## 部署架构

### 开发环境
```
本地开发机
├── Python 3.10+
├── Node.js (用于 npx 命令)
├── uv/uvx (用于 Python MCP 工具)
├── DeepSeek API Key
└── MCP 服务器配置文件
```

### 生产环境
```
服务器
├── Docker 容器
│   ├── 应用容器（Python + Agent Framework）
│   ├── MCP 工具容器（独立运行）
│   └── DevUI 容器（可选）
├── 配置管理
│   ├── 环境变量（API Keys）
│   └── MCP 配置文件
└── 日志和监控
    ├── 应用日志
    ├── MCP 工具日志
    └── 性能监控
```

### Docker 部署
```dockerfile
# Dockerfile
FROM python:3.10-slim

# 安装 Node.js（用于 npx）
RUN apt-get update && apt-get install -y nodejs npm

# 安装 uv
RUN pip install uv

# 复制应用代码
COPY . /app
WORKDIR /app

# 安装 Python 依赖
RUN pip install -r requirements.txt

# 启动应用
CMD ["python", "main.py"]
```

## 监控和日志

### 日志系统
```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
def setup_logging():
    logger = logging.getLogger("mcp_multi_agent")
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        "logs/system.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s - %(message)s')
    )
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### 性能监控
```python
import time
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} 执行时间: {duration:.2f}秒")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败 (耗时 {duration:.2f}秒): {e}")
            raise
    return wrapper

@monitor_performance
async def run_workflow(workflow, input_data):
    """执行工作流并监控性能"""
    return await workflow.run(input_data)
```


## 安全考虑

### API 密钥管理
```python
import os
from dotenv import load_dotenv

def load_secure_config():
    """安全加载配置"""
    load_dotenv()
    
    # 验证必需的环境变量
    required_vars = [
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"缺少必需的环境变量: {', '.join(missing_vars)}")
    
    return {
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY"),
        "deepseek_base_url": os.getenv("DEEPSEEK_BASE_URL"),
        "deepseek_model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    }
```

### 内容安全
```python
class ContentSafetyChecker:
    """内容安全检查器"""
    
    SENSITIVE_WORDS = [
        # 敏感词列表
    ]
    
    def check_content(self, content: str) -> Dict[str, Any]:
        """检查内容安全性"""
        issues = []
        
        # 检查敏感词
        for word in self.SENSITIVE_WORDS:
            if word in content:
                issues.append({
                    "type": "sensitive_word",
                    "word": word,
                    "severity": "high"
                })
        
        # 检查内容长度
        if len(content) > 10000:
            issues.append({
                "type": "content_too_long",
                "severity": "medium"
            })
        
        return {
            "safe": len(issues) == 0,
            "issues": issues
        }
```

### 访问控制
```python
class AccessControl:
    """访问控制"""
    
    def __init__(self):
        self.allowed_ips = os.getenv("ALLOWED_IPS", "").split(",")
    
    def check_access(self, ip: str) -> bool:
        """检查访问权限"""
        if not self.allowed_ips:
            return True  # 未配置则允许所有
        return ip in self.allowed_ips
```

## 扩展性设计

### 添加新智能体
```python
def create_custom_agent(
    name: str,
    instructions: str,
    mcp_tools: List[str],
    chat_client
) -> ChatAgent:
    """创建自定义智能体"""
    return ChatAgent(
        name=name,
        chat_client=chat_client,
        instructions=instructions,
        tools=mcp_tools
    )

# 使用示例
seo_agent = create_custom_agent(
    name="SEO优化智能体",
    instructions="你是SEO专家，负责优化内容的搜索引擎排名...",
    mcp_tools=["mcp_exa_web_search_exa"],
    chat_client=client
)
```

### 添加新 MCP 工具
```json
{
  "mcpServers": {
    "new-tool": {
      "isActive": true,
      "name": "new-tool",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "new-mcp-tool"],
      "env": {
        "API_KEY": "${NEW_TOOL_API_KEY}"
      }
    }
  }
}
```

### 添加新工作流模式
```python
def create_custom_workflow(agents: List[ChatAgent]) -> WorkflowBuilder:
    """创建自定义工作流"""
    builder = WorkflowBuilder()
    
    # 设置起点
    builder.set_start_executor(agents[0])
    
    # 添加边
    for i in range(len(agents) - 1):
        builder.add_edge(agents[i], agents[i + 1])
    
    return builder.build()
```

## 性能优化

### 缓存机制
```python
from functools import lru_cache
import hashlib

class ResultCache:
    """结果缓存"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
    
    def get_cache_key(self, input_data: str) -> str:
        """生成缓存键"""
        return hashlib.md5(input_data.encode()).hexdigest()
    
    def get(self, input_data: str) -> Optional[Any]:
        """获取缓存"""
        key = self.get_cache_key(input_data)
        return self.cache.get(key)
    
    def set(self, input_data: str, result: Any):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 删除最旧的缓存
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self.get_cache_key(input_data)
        self.cache[key] = result
```

### 并发控制
```python
import asyncio
from asyncio import Semaphore

class ConcurrencyController:
    """并发控制器"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = Semaphore(max_concurrent)
    
    async def run_with_limit(self, coro):
        """限制并发执行"""
        async with self.semaphore:
            return await coro
```

## 总结

本设计文档详细描述了基于 MCP 的多智能体热点资讯分析系统的架构、组件、数据模型、错误处理、测试策略、部署方案和安全考虑。系统采用模块化设计，易于扩展和维护，通过标准的 stdio MCP 服务器提供工具支持，使用 Agent Framework 的 WorkflowBuilder 编排智能体协作流程。
