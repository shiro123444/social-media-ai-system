# 🎯 新媒体运营 AI 系统

基于 Microsoft Agent Framework 构建的智能新媒体运营助手，支持热点发现、内容生成、多平台适配等功能。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Agent Framework](https://img.shields.io/badge/Agent%20Framework-1.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 核心功能

- 🔥 **热点发现与分析** - 自动获取和分析网络热点话题
- ✍️ **多平台内容生成** - 支持微信、微博、抖音、小红书等平台
- 🎨 **智能配图建议** - AI 驱动的视觉设计方案
- 📊 **内容风格分析** - 专业的内容质量评估
- 🤖 **多智能体协作** - 6个专业智能体分工合作
- 🌐 **可视化界面** - 基于 DevUI 的友好交互界面

## 🏗️ 系统架构

```
新媒体运营 AI 系统
├── 热点抓取智能体 - 发现和分析热点
├── 内容生成智能体 - 创作多平台内容
├── 风格控制智能体 - 确保品牌一致性
├── 配图智能体 - 提供视觉设计方案
├── 发布管理智能体 - 管理多平台发布
└── 数据分析智能体 - 分析内容表现
```

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- pip 包管理器

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/shiro123444/social-media-ai-system.git
cd social-media-ai-system
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**

复制 `.env.example` 并重命名为 `.env`，然后配置你的 API 密钥：

```env
# 使用 DeepSeek API (推荐)
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 或使用 OpenAI API
# OPENAI_API_KEY=your_openai_api_key_here
```

### 运行方式

#### 方式 1: 演示版（无需 API 密钥）

```bash
python simple_demo.py
```

适合快速体验功能，使用模拟数据。

#### 方式 2: DeepSeek 版本（推荐）

```bash
python deepseek_demo.py
```

使用 DeepSeek API，获得真实 AI 能力。性价比高，中文优化好。

#### 方式 3: 完整系统

```bash
python start_social_media_system.py
```

运行完整的多智能体协作系统。

## 📖 使用指南

### 1. 启动 DevUI 界面

运行任一脚本后，浏览器会自动打开 `http://localhost:8080`

### 2. 与 AI 助手交互

在界面中输入问题，例如：

- "获取科技领域的热点话题"
- "为人工智能话题生成微信文章大纲"
- "创作一条关于新能源汽车的微博"
- "生成60秒短视频脚本"
- "分析这段内容的风格特点"
- "推荐小红书平台的配图方案"

### 3. 查看智能体工具

系统会自动调用相应的工具函数来完成任务。

## 🎨 支持的平台

| 平台 | 内容类型 | 特点 |
|------|---------|------|
| 微信公众号 | 长文章 | 2000-3000字，深度内容 |
| 微博 | 短文 | 140字以内，话题标签 |
| 抖音/快手 | 短视频脚本 | 15-60秒，分镜设计 |
| 小红书 | 图文笔记 | 200-500字，配图方案 |
| B站 | 视频内容 | 长视频脚本，弹幕互动 |

## 📁 项目结构

```
social-media-ai-system/
├── .kiro/
│   └── specs/
│       └── social-media-ai-system/
│           ├── requirements.md      # 需求文档
│           ├── design.md           # 设计文档
│           └── tasks.md            # 任务清单
├── simple_demo.py                  # 演示版本
├── deepseek_demo.py               # DeepSeek 版本
├── start_social_media_system.py   # 完整系统
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量模板
├── .gitignore                     # Git 忽略文件
└── README.md                      # 项目文档
```

## 🔧 技术栈

- **核心框架**: Microsoft Agent Framework
- **AI 模型**: DeepSeek / OpenAI GPT-4
- **开发语言**: Python 3.10+
- **用户界面**: Agent Framework DevUI
- **异步处理**: asyncio

## 💡 核心特性

### 多智能体协作

系统采用多智能体架构，每个智能体专注于特定任务：

```python
# 热点抓取智能体
hotspot_agent = ChatAgent(
    name="热点抓取智能体",
    instructions="分析网络热点和趋势...",
    tools=[get_trending_topics, analyze_hotspot]
)

# 内容生成智能体
content_agent = ChatAgent(
    name="内容生成智能体",
    instructions="创作多平台内容...",
    tools=[generate_article, generate_post]
)
```

### 工作流编排

使用 WorkflowBuilder 构建智能体协作流程：

```python
workflow = (WorkflowBuilder()
    .set_start_executor(hotspot_agent)
    .add_edge(hotspot_agent, content_agent)
    .add_edge(content_agent, style_agent)
    .build())
```

## 📊 性能指标

- ⚡ 热点信息获取延迟: < 30分钟
- 🚀 内容生成时间: < 2分钟
- 💪 并发处理能力: 100+ 任务
- 📈 响应时间: < 3秒

## 🛠️ 开发计划

查看 `.kiro/specs/social-media-ai-system/tasks.md` 了解详细的开发任务清单。

### 已完成 ✅

- [x] 项目基础架构
- [x] 智能体设计和实现
- [x] DevUI 界面集成
- [x] DeepSeek API 支持

### 进行中 🚧

- [ ] 真实平台 API 集成
- [ ] 数据库存储功能
- [ ] 用户认证系统

### 计划中 📋

- [ ] 自动发布功能
- [ ] 数据分析报告
- [ ] 移动端适配

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) - 核心框架
- [DeepSeek](https://www.deepseek.com/) - AI 模型支持
- [OpenAI](https://openai.com/) - GPT 模型

## 📧 联系方式

- 项目主页: [GitHub](https://github.com/shiro123444/social-media-ai-system)
- 问题反馈: [Issues](https://github.com/shiro123444/social-media-ai-system/issues)

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star ⭐️

---

**注意**: 本项目仅供学习和研究使用，请遵守各平台的使用条款和相关法律法