# 🔧 MCP 工具集成指南 - 实时热点新闻系统

## 概述

本指南展示如何为每个智能体配置专属的 MCP 工具，实现真实的实时热点新闻获取和分析。

## 🎯 多智能体 + MCP 架构

```
┌─────────────────────────────────────────────────────────┐
│           中央协调器 (Orchestrator)                      │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 新闻抓取智能体 │  │ 社交媒体智能体 │  │ 搜索趋势智能体 │
│              │  │              │  │              │
│ MCP: Fetch   │  │ MCP: Twitter │  │ MCP: Brave   │
│ MCP: RSS     │  │ MCP: Reddit  │  │ MCP: Google  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                  ┌──────────────┐
                  │ 内容生成智能体 │
                  │              │
                  │ MCP: OpenAI  │
                  └──────────────┘
```

## 📦 可用的 MCP 服务器

### 1. Fetch MCP Server (网页抓取)
```bash
# 安装
uvx mcp-server-fetch

# 功能
- 获取网页内容
- 解析 HTML
- 提取文本信息
```

### 2. Brave Search MCP (搜索引擎)
```bash
# 安装
npm install -g @modelcontextprotocol/server-brave-search

# 功能
- 实时网络搜索
- 新闻搜索
- 趋势话题
```

### 3. RSS Feed MCP (RSS 订阅)
```bash
# 自定义 MCP 服务器
# 功能
- 订阅新闻源
- 解析 RSS/Atom
- 定时更新
```

### 4. Twitter/X MCP (社交媒体)
```bash
# 功能
- 获取热门推文
- 话题趋势
- 用户动态
```

## 🔨 实现步骤

### 步骤 1: 配置 MCP 服务器

创建 `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "disabled": false
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your_brave_api_key"
      },
      "disabled": false
    },
    "filesystem": {
      "command": "uvx",
      "args": ["mcp-server-filesystem", "E:/Agent/news_cache"],
      "disabled": false
    }
  }
}
```

### 步骤 2: 创建专属智能体

每个智能体使用不同的 MCP 工具：

```python
from agent_framework import ChatAgent, MCPStdioTool
from agent_framework.openai import OpenAIChatClient

# 智能体 1: 新闻抓取 (使用 Fetch MCP)
async with MCPStdioTool(
    name="fetch",
    command="uvx",
    args=["mcp-server-fetch"]
) as fetch_tool:
    news_crawler = ChatAgent(
        name="新闻抓取智能体",
        chat_client=OpenAIChatClient(),
        instructions="从新闻网站抓取最新资讯",
        tools=[fetch_tool]
    )

# 智能体 2: 搜索趋势 (使用 Brave Search MCP)
async with MCPStdioTool(
    name="brave-search",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-brave-search"]
) as search_tool:
    trend_analyzer = ChatAgent(
        name="搜索趋势智能体",
        chat_client=OpenAIChatClient(),
        instructions="分析搜索引擎热点趋势",
        tools=[search_tool]
    )
```

### 步骤 3: 工作流编排

```python
from agent_framework import WorkflowBuilder

workflow = (WorkflowBuilder()
    .set_start_executor(news_crawler)
    .add_edge(news_crawler, trend_analyzer)
    .add_edge(trend_analyzer, content_generator)
    .build())

# 运行工作流
results = await workflow.run("获取今日科技领域热点")
```

## 🌐 实时新闻源配置

### 国内新闻源
```python
NEWS_SOURCES = {
    "综合": [
        "https://news.sina.com.cn/",
        "https://news.163.com/",
        "https://www.thepaper.cn/"
    ],
    "科技": [
        "https://www.36kr.com/",
        "https://www.ithome.com/",
        "https://www.geekpark.net/"
    ],
    "财经": [
        "https://finance.sina.com.cn/",
        "https://www.yicai.com/",
        "https://wallstreetcn.com/"
    ]
}
```

### RSS 订阅源
```python
RSS_FEEDS = {
    "科技": [
        "https://www.36kr.com/feed",
        "https://sspai.com/feed",
        "https://www.geekpark.net/rss"
    ],
    "新闻": [
        "https://www.thepaper.cn/rss.jsp",
        "https://news.163.com/special/00011K6L/rss_newstop.xml"
    ]
}
```

## 🔑 API 密钥配置

在 `.env` 文件中添加：

```env
# Brave Search API
BRAVE_API_KEY=your_brave_api_key_here

# Twitter API (可选)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret

# 微博 API (可选)
WEIBO_APP_KEY=your_weibo_app_key
WEIBO_APP_SECRET=your_weibo_app_secret
```

## 📊 数据流程

```
1. 新闻抓取智能体 (Fetch MCP)
   ↓ 获取原始新闻内容
   
2. 搜索趋势智能体 (Brave Search MCP)
   ↓ 分析搜索热度和趋势
   
3. 社交媒体智能体 (Twitter/Weibo MCP)
   ↓ 获取社交媒体讨论热度
   
4. 数据聚合智能体
   ↓ 整合多源数据，计算热度指数
   
5. 内容生成智能体
   ↓ 基于热点生成多平台内容
   
6. 发布管理智能体
   ↓ 自动发布到各平台
```

## 🚀 快速开始

### 1. 安装 MCP 工具
```bash
# 安装 uv (Python 包管理器)
pip install uv

# 安装 Fetch MCP
uvx mcp-server-fetch

# 安装 Brave Search MCP (需要 Node.js)
npm install -g @modelcontextprotocol/server-brave-search
```

### 2. 配置 API 密钥
```bash
# 获取 Brave Search API Key
# 访问: https://brave.com/search/api/

# 配置到 .env 文件
echo "BRAVE_API_KEY=your_key_here" >> .env
```

### 3. 运行系统
```bash
python realtime_news_system.py
```

## 💡 高级功能

### 定时任务
```python
import schedule
import time

def fetch_news_job():
    """每小时抓取一次新闻"""
    asyncio.run(workflow.run("获取最新热点"))

schedule.every(1).hours.do(fetch_news_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 热度计算算法
```python
def calculate_hotness(news_item):
    """计算新闻热度指数"""
    score = 0
    
    # 搜索量权重 (40%)
    score += news_item['search_volume'] * 0.4
    
    # 社交媒体讨论量 (30%)
    score += news_item['social_mentions'] * 0.3
    
    # 新闻源权威性 (20%)
    score += news_item['source_authority'] * 0.2
    
    # 时效性 (10%)
    score += news_item['recency_score'] * 0.1
    
    return score
```

## 🔍 调试技巧

### 查看 MCP 工具调用
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看工具调用
agent.run("获取新闻", debug=True)
```

### 测试单个 MCP 服务器
```bash
# 测试 Fetch MCP
uvx mcp-server-fetch

# 测试 Brave Search MCP
npx -y @modelcontextprotocol/server-brave-search
```

## 📚 参考资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [Agent Framework MCP 集成](https://github.com/microsoft/agent-framework)
- [Brave Search API](https://brave.com/search/api/)
- [RSS Feed 规范](https://www.rssboard.org/rss-specification)

## ⚠️ 注意事项

1. **API 限制**: 注意各 API 的调用频率限制
2. **数据合规**: 遵守网站的 robots.txt 和使用条款
3. **缓存策略**: 实现合理的缓存避免重复请求
4. **错误处理**: 添加重试机制和降级方案

---

准备好开始构建实时热点新闻系统了吗？🚀