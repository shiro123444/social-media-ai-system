# 快速开始 - 小红书内容生产工作流

## 🚀 一键运行

### 方式 1：命令行运行（推荐）

```bash
cd social-media-ai-system
python run_workflow.py
```

**特点**：
- ✅ 快速执行，直接看结果
- ✅ 完整的日志输出
- ✅ 适合生产环境

### 方式 2：DevUI 可视化（推荐演示）

```bash
cd social-media-ai-system
python run_devui.py
```

然后在浏览器打开：http://localhost:9000

**特点**：
- ✅ 可视化工作流执行过程
- ✅ 实时查看每个步骤的输出
- ✅ 适合演示和调试

## 📋 运行前检查

### 1. 环境变量配置

确保 `.env` 文件包含：

```bash
# DeepSeek API
DEEPSEEK_API_KEY=your_api_key_here

# 小红书图片（必须）
XHS_DEFAULT_IMAGES=D:\Pictures\image1.jpg,D:\Pictures\image2.jpg

# MCP 服务地址
XIAOHONGSHU_MCP_URL=http://localhost:18060/mcp
DAILY_HOT_MCP_URL=http://localhost:8000/mcp
```

### 2. MCP 服务运行

确保以下服务正在运行：

```bash
# 检查 daily-hot-mcp (端口 8000)
curl http://localhost:8000/mcp

# 检查 xiaohongshu-mcp (端口 18060)
curl http://localhost:18060/mcp
```

### 3. 图片文件存在

确保 `XHS_DEFAULT_IMAGES` 中的图片文件真实存在。

## 🎯 工作流说明

### 执行流程

```
🔥 热点获取 → 📊 内容分析 → ✍️ 内容生成 → 📤 小红书发布
    ↓              ↓              ↓              ↓
 MCP工具        Think工具      纯LLM模式     MCP工具
 获取热点        深度分析      生成文案      发布内容
```

### 步骤详解

1. **热点获取**
   - 使用 daily-hot-mcp 获取最新热点
   - 支持多个热点源（微博、知乎、IT之家等）
   - 返回热点标题、热度、来源等信息

2. **内容分析**
   - 使用 think-tool 进行深度分析
   - 提取关键词、分析情感倾向
   - 识别目标受众、预测趋势

3. **内容生成**
   - 纯 LLM 模式，不依赖外部工具
   - 根据分析结果生成小红书文案
   - 包含标题、正文、标签、配图建议

4. **小红书发布**
   - 使用 xiaohongshu-mcp 服务发布内容
   - 支持本地图片路径和网络图片
   - 自动处理标题长度和内容格式

## 📊 预期输出

### 命令行输出示例

```
🚀 小红书内容生产工作流
✅ 工作流: Xiaohongshu Hotspot Workflow
📝 描述: 热点追踪 → 深度分析 → 小红书文案生成 → 自动发布

🔄 开始执行: 获取最新的AI技术热点，生成小红书文案并发布

[步骤 1] 热点获取完成 - 获取了 10 个热点
[步骤 2] 内容分析完成 - 提取了 5 个关键词
[步骤 3] 文案生成完成 - 生成了 800 字文案
[步骤 4] 发布完成 - 成功发布到小红书

✅ 工作流执行完成
```

### DevUI 界面

- 左侧：工作流结构图
- 中央：执行进度和状态
- 右侧：每个步骤的详细输出
- 底部：执行日志

## ⚠️ 常见问题

### 1. MCP 服务连接失败

**错误**：`连接 MCP 服务失败`

**解决**：
```bash
# 检查服务状态
curl http://localhost:8000/mcp
curl http://localhost:18060/mcp

# 重启服务
```

### 2. 图片上传失败

**错误**：`图片路径无效`

**解决**：
- 检查图片文件是否存在
- 使用绝对路径
- 确保图片格式为 JPG/PNG
- 检查图片大小（建议 < 5MB）

### 3. API 调用失败

**错误**：`DEEPSEEK_API_KEY 无效`

**解决**：
- 检查 API Key 是否正确
- 确认账户余额充足
- 检查网络连接

### 4. DevUI 端口被占用

**错误**：`端口 9000 被占用`

**解决**：
```bash
# Windows
netstat -ano | findstr :9000
taskkill /PID <进程ID> /F

# 或修改端口
# 在 run_devui.py 中修改 port=9000 为其他端口
```

## 🎓 进阶使用

### 自定义查询

修改 `run_workflow.py` 中的查询：

```python
query = "获取最新的AI技术热点，生成小红书文案并发布"

# 改为：
query = "获取科技新闻热点，生成专业的技术分析文章"
```

### 批量运行

```python
topics = ["AI技术", "科技新闻", "互联网趋势"]
for topic in topics:
    query = f"获取{topic}相关热点，生成小红书文案"
    result = await workflow.run(query)
```

### 定时任务

使用 Windows 任务计划程序或 cron 定时运行：

```bash
# 每天 9:00 运行
# 在任务计划程序中添加：
# 程序：python
# 参数：D:\agent\social-media-ai-system\run_workflow.py
# 起始于：D:\agent\social-media-ai-system
```

## 📚 相关文档

- [完整工作流指南](docs/COMPLETE_WORKFLOW_GUIDE.md)
- [小红书发布修复说明](docs/XIAOHONGSHU_PUBLISH_FIX.md)
- [MCP 配置指南](docs/MCP_CONFIGURATION.md)

## 🆘 获取帮助

如遇到问题，请提供：

1. 完整的错误日志
2. 环境配置信息（`.env` 文件内容，隐藏敏感信息）
3. 复现步骤
4. 预期行为和实际行为

## 🎉 成功案例

工作流成功运行后，你将看到：

1. ✅ 热点数据成功获取
2. ✅ 内容分析报告生成
3. ✅ 小红书文案创作完成
4. ✅ 内容成功发布到小红书

**恭喜！你已经成功运行了完整的 AI 内容生产工作流！** 🎊
