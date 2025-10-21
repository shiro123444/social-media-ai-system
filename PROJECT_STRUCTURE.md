# 项目结构说明

## 目录结构

```
social-media-ai-system/
├── agents/                          # 智能体模块
│   ├── social_media_workflow/       # 主工作流（DevUI 使用）
│   │   └── __init__.py             # 三个 Executor 的实现
│   ├── hotspot_agent.py            # 热点获取智能体（旧版）
│   ├── analysis_agent.py           # 分析智能体（旧版）
│   └── content_agent.py            # 内容生成智能体（旧版）
│
├── config/                          # 配置文件
│   ├── mcp_servers.json            # MCP 服务器配置
│   ├── platform_guidelines.json    # 各平台内容规范
│   ├── style_presets.json          # 内容风格预设
│   └── workflow_config.py          # 工作流配置
│
├── daily-hot-mcp/                   # Daily Hot MCP 服务器
│   ├── daily_hot_mcp/              # 核心代码
│   │   ├── __init__.py
│   │   ├── server.py               # MCP 服务器实现
│   │   ├── tools/                  # 各平台热榜工具
│   │   └── utils/                  # 工具函数
│   ├── requirements.txt
│   └── README.md
│
├── utils/                           # 工具模块
│   ├── deepseek_chat_client.py     # DeepSeek API 适配器
│   ├── mcp_tool_pool.py            # MCP 工具池管理
│   └── publishers/                 # 发布工具（未完成）
│
├── docs/                            # 文档
│   └── XIAOHONGSHU_SETUP.md        # 小红书配置指南
│
├── examples/                        # 示例代码
│   └── quick_start.py              # 快速开始示例
│
├── tests/                           # 测试代码
│   ├── test_hotspot_agent.py       # 热点获取测试
│   ├── test_content_agent.py       # 内容生成测试
│   └── test_rss_only.py            # RSS 测试
│
├── chromedriver/                    # ChromeDriver 驱动
│   └── win64-141.0.7390.108/       # Chrome 141 版本驱动
│
├── xhs_cookies/                     # 小红书 Cookie 存储
│   └── xiaohongshu_cookies.json
│
├── .env                            # 环境变量配置（不提交）
├── .env.example                    # 环境变量示例
├── .gitignore                      # Git 忽略文件
├── requirements.txt                # Python 依赖
├── test_devui_final.py             # DevUI 启动脚本
├── start_devui.ps1                 # PowerShell 启动脚本
├── README.md                       # 项目说明
├── Learn.md                        # 开发经验总结
└── 新设备部署指南.md               # 部署指南
```

## 核心文件说明

### 工作流实现

**agents/social_media_workflow/__init__.py**
- 包含三个 Executor：
  - `MCPHotspotExecutor` - 调用 Daily Hot MCP 获取热点
  - `ThinkToolAnalysisExecutor` - 使用 think-tool 深度分析
  - `XiaohongshuContentExecutor` - 生成小红书文案
- 使用 `SequentialBuilder` 编排工作流
- 约 600 行代码

### 配置文件

**config/platform_guidelines.json**
- 定义各平台的内容规范
- 包括字数要求、格式要求、风格特点

**config/style_presets.json**
- 定义不同的内容风格
- 包括资讯、科普、轻松、营销等

**config/mcp_servers.json**
- MCP 服务器配置
- 目前只有 Daily Hot MCP

### 工具模块

**utils/deepseek_chat_client.py**
- DeepSeek API 适配器
- 解决多模态消息兼容性问题
- 处理 TextContent 序列化问题

**utils/mcp_tool_pool.py**
- MCP 工具池管理
- 处理工具生命周期

## 启动方式

### 方式 1: PowerShell 脚本（推荐）

```powershell
.\start_devui.ps1
```

### 方式 2: Python 脚本

```bash
python test_devui_final.py
```

### 方式 3: 手动启动

```bash
# 终端 1: 启动 MCP 服务器
cd daily-hot-mcp
python -m daily_hot_mcp

# 终端 2: 启动 DevUI
python -c "from agent_framework import DevUI; DevUI().run(port=9000)"
```

## 开发说明

### 修改工作流

编辑 `agents/social_media_workflow/__init__.py`，修改三个 Executor 的实现。

### 添加新平台

1. 在 `config/platform_guidelines.json` 添加平台配置
2. 在 `XiaohongshuContentExecutor` 中添加生成逻辑

### 调试技巧

- 查看 DevUI 的实时日志
- 使用 `logger.info()` 输出调试信息
- 检查 `output/` 目录的输出文件

## 注意事项

1. **不要提交 .env 文件** - 包含 API Key
2. **不要提交 xhs_cookies/** - 包含登录信息
3. **chromedriver 需要匹配 Chrome 版本** - 版本不匹配会报错
4. **MCP 服务器必须先启动** - 否则工作流会失败

## 已知问题

1. **小红书自动发布** - 页面元素找不到，建议手动发布
2. **DeepSeek API 限流** - 频繁调用可能被限流
3. **内容质量** - AI 生成的内容需要人工审核

## 后续计划

- [ ] 支持更多平台（抖音、快手）
- [ ] 添加图片推荐功能
- [ ] 优化内容生成质量
- [ ] 支持定时任务
- [ ] 添加内容审核功能
