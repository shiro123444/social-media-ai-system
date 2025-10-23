# 小红书发布配置指南

本文档说明如何配置小红书自动发布功能（使用 xiaohongshu-mcp）。

## 前置要求

1. **Chrome 浏览器**：确保已安装 Chrome 浏览器
2. **Windows 系统**：xiaohongshu-mcp 目前支持 Windows（也有 macOS/Linux 版本）

## 配置步骤

### 1. 下载 xiaohongshu-mcp

访问 [xiaohongshu-mcp Releases](https://github.com/xpzouying/xiaohongshu-mcp/releases) 下载最新版本：

**Windows 用户下载：**
- `xiaohongshu-login-windows-amd64.exe` - 登录工具
- `xiaohongshu-mcp-windows-amd64.exe` - MCP 服务

**macOS 用户下载：**
- `xiaohongshu-login-darwin-amd64` - 登录工具（Intel）
- `xiaohongshu-login-darwin-arm64` - 登录工具（Apple Silicon）
- `xiaohongshu-mcp-darwin-amd64` - MCP 服务（Intel）
- `xiaohongshu-mcp-darwin-arm64` - MCP 服务（Apple Silicon）

**Linux 用户下载：**
- `xiaohongshu-login-linux-amd64` - 登录工具
- `xiaohongshu-mcp-linux-amd64` - MCP 服务

将下载的文件放到项目根目录或任意目录。

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```env
# xiaohongshu-mcp 服务地址（默认端口 18060）
XIAOHONGSHU_MCP_URL=http://localhost:18060/mcp

# 默认图片路径（如果文案中没有提供图片，将使用此默认图片）
# Windows 示例（使用绝对路径）：
XHS_DEFAULT_IMAGES=C:\Users\YourName\Pictures\default.jpg

# macOS/Linux 示例：
# XHS_DEFAULT_IMAGES=/Users/YourName/Pictures/default.jpg

# 支持多个图片，用逗号分隔：
# XHS_DEFAULT_IMAGES=C:\Users\YourName\Pictures\image1.jpg,C:\Users\YourName\Pictures\image2.jpg
```

**重要**：
- 图片路径必须是**绝对路径**
- 支持 JPG、PNG 等常见格式
- 可以配置多个图片，用逗号分隔

### 3. 登录小红书账号

**Windows:**
```powershell
# 运行登录工具
.\xiaohongshu-login-windows-amd64.exe
```

**macOS/Linux:**
```bash
# 添加执行权限
chmod +x xiaohongshu-login-darwin-arm64

# 运行登录工具
./xiaohongshu-login-darwin-arm64
```

登录工具会：
1. 打开 Chrome 浏览器
2. 自动跳转到小红书登录页面
3. 手动扫码或输入验证码登录
4. 登录成功后，Cookie 会自动保存

**登录成功标志：**
```
登录成功！Cookie 已保存
```

### 4. 启动 MCP 服务

**Windows:**
```powershell
# 启动 MCP 服务（默认端口 18060）
.\xiaohongshu-mcp-windows-amd64.exe
```

**macOS/Linux:**
```bash
# 添加执行权限
chmod +x xiaohongshu-mcp-darwin-arm64

# 启动 MCP 服务
./xiaohongshu-mcp-darwin-arm64
```

服务启动成功会显示：
```
time="2025-10-23T10:00:00+08:00" level=info msg="MCP 服务启动成功"
time="2025-10-23T10:00:00+08:00" level=info msg="监听地址: :18060"
```

**保持此终端窗口打开**，MCP 服务需要持续运行。

### 5. 验证配置

检查 MCP 服务是否正常运行：

```powershell
# Windows
curl http://localhost:18060/mcp

# macOS/Linux
curl http://localhost:18060/mcp
```

如果返回 JSON 数据，说明服务正常运行。

## 使用 Workflow

### 启动流程

1. **启动 MCP 服务**（如果还没启动）：
   ```powershell
   # Windows
   .\xiaohongshu-mcp-windows-amd64.exe
   ```

2. **运行 Workflow**：
   ```bash
   python test_devui_final.py
   ```

3. **访问 DevUI**：
   打开浏览器访问 http://localhost:9000

4. **输入查询**：
   ```
   获取今日热点并发布到小红书
   ```

### Workflow 执行流程

Workflow 会自动完成以下步骤：

1. **📊 获取热点数据**
   - 使用 daily-hot-mcp 获取微博、B站、知乎等平台的热点
   - 提取热点标题、热度、来源等信息

2. **🧠 深度分析**
   - 使用 think-tool 进行深度分析
   - 按类别分类热点（科技、娱乐、社会等）
   - 提取关键信息和趋势

3. **✍️ 生成小红书文案**
   - 选择 3-4 个最热的话题
   - 生成符合小红书风格的文案
   - 每条新闻包含：📰 新闻内容 + 💭 时评观点
   - 自动添加默认图片（如果配置了 `XHS_DEFAULT_IMAGES`）
   - 控制标题在 20 字以内，内容在 1000 字以内

4. **🚀 自动发布到小红书**
   - 使用 xiaohongshu-mcp 发布笔记
   - 自动上传图片
   - 添加标签
   - 发布成功后返回结果

### 文案格式示例

生成的小红书文案格式：

```
标题：🔥10.23热搜！学生梗+金庸

内容：
姐妹们！10月23日的热搜真的太炸了！😱

📰 学生满口「包的包的」、「666」等网络梗，这将带来哪些深远影响？
10月22日，一篇关于学生语言习惯的文章在知乎引发热议，获得797万热度。
文章指出，现在的学生在日常交流中大量使用网络梗，如「包的包的」、「666」等，
这种现象引发了教育界的担忧。

💭 这个现象确实值得关注！网络梗虽然有趣，但过度使用可能会影响学生的
正式表达能力。学校和家长需要引导孩子在不同场合使用合适的语言。

📰 金庸小说有哪些情节是成年后才能看懂的？
10月23日，这个话题在知乎热榜获得428万热度。网友们纷纷分享自己重读
金庸小说后的新感悟，发现了很多年少时没有理解的深层含义。

💭 经典就是经典！成年后重读金庸，才发现那些看似简单的情节背后，
藏着多少人生哲理和社会洞察。你们有重读过金庸吗？

你们怎么看？评论区聊聊！👇

标签：#今日热点 #知乎热榜 #深度思考
```

## 内容特点

### 1. 详细的新闻描述
- ✅ 包含具体时间（10月23日、今天等）
- ✅ 包含具体数据（797万热度、428万热度等）
- ✅ 包含来源平台（知乎、微博、B站等）
- ✅ 详细描述事件经过

### 2. 有观点的时评
- ✅ 每条新闻后都有独立的评论
- ✅ 评论有观点、有分析
- ✅ 引导读者思考和讨论

### 3. 符合小红书规范
- ✅ 标题不超过 20 字
- ✅ 内容不超过 1000 字
- ✅ 使用 emoji 增加活力
- ✅ 结尾有互动引导

## 注意事项

### 1. 安全与合规
- ⚠️ **仅限研究用途**：此工具仅供学习研究，禁止用于商业目的
- ⚠️ **Cookie 安全**：妥善保管 Cookie，不要泄露
- ⚠️ **内容审核**：发布前请确保内容符合平台规范
- ⚠️ **发布频率**：避免频繁发布，以免被平台限制

### 2. 图片要求
- 必须提供图片（本地路径或配置默认图片）
- 支持 JPG、PNG 等常见格式
- 建议图片尺寸：1080x1080 或 1080x1440

### 3. 字数限制
- 标题：最多 20 个字（包含 emoji）
- 内容：最多 1000 个字
- 超出部分会被自动截断

## 故障排除

### 1. MCP 服务连接失败

**错误**：`Connection refused` 或 `Cannot connect to MCP`

**解决**：
- 检查 MCP 服务是否正在运行
- 检查端口 18060 是否被占用
- 检查 `.env` 中的 `XIAOHONGSHU_MCP_URL` 配置

### 2. Cookie 过期

**错误**：`登录失败` 或 `Cookie 无效`

**解决**：
- 重新运行登录工具：`.\xiaohongshu-login-windows-amd64.exe`
- 手动登录小红书账号
- 重启 MCP 服务

### 3. 图片上传失败

**错误**：`图片上传失败` 或 `找不到图片`

**解决**：
- 检查图片路径是否正确（必须是绝对路径）
- 检查图片文件是否存在
- 检查图片格式是否支持（JPG、PNG）
- 检查 `.env` 中的 `XHS_DEFAULT_IMAGES` 配置

### 4. 发布跳过

**提示**：`⚠️ 发布跳过：小红书发布需要图片`

**解决**：
- 在 `.env` 中配置 `XHS_DEFAULT_IMAGES`
- 或在生成文案时提供图片路径

### 5. 标题或内容被截断

**警告**：`标题超过 20 字，将被截断` 或 `内容超过 1000 字，将被截断`

**说明**：
- 这是正常现象，小红书有字数限制
- Workflow 会自动截断超出部分
- 建议优化 Agent 指令，生成更简洁的内容

### 6. 发布成功但看不到笔记

**情况**：日志显示发布成功，但小红书 App 中看不到

**解决**：
- 等待 1-2 分钟，刷新小红书 App
- 检查草稿箱，笔记可能在审核中
- 检查是否被平台限流或审核

## 高级配置

### 自定义 MCP 端口

如果端口 18060 被占用，可以修改：

```powershell
# 启动 MCP 服务时指定端口
.\xiaohongshu-mcp-windows-amd64.exe -port 18061
```

然后更新 `.env`：
```env
XIAOHONGSHU_MCP_URL=http://localhost:18061/mcp
```

### 配置多个默认图片

在 `.env` 中配置多个图片，系统会随机选择：

```env
XHS_DEFAULT_IMAGES=C:\Users\YourName\Pictures\image1.jpg,C:\Users\YourName\Pictures\image2.jpg,C:\Users\YourName\Pictures\image3.jpg
```

### 日志查看

MCP 服务的日志会实时显示在终端：

```
time="2025-10-23T11:43:38+08:00" level=info msg="MCP: 发布内容"
time="2025-10-23T11:43:38+08:00" level=info msg="发布内容 - 标题: 🔥10.22热搜！学生网络梗+金庸深度+, 图片数量: 1"
time="2025-10-23T11:43:53+08:00" level=info msg="发布内容: title=..., images=1, tags=[...]"
```

## 相关链接

- [xiaohongshu-mcp GitHub](https://github.com/xpzouying/xiaohongshu-mcp)
- [daily-hot-mcp GitHub](https://github.com/your-repo/daily-hot-mcp)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Agent Framework](https://github.com/microsoft/agent-framework)

## 常见问题 (FAQ)

### Q: 可以同时发布到多个小红书账号吗？

A: 目前不支持。每次只能登录一个账号。如需切换账号，需要重新运行登录工具。

### Q: 发布的笔记可以定时发布吗？

A: 目前不支持定时发布。笔记会立即发布。

### Q: 可以修改已发布的笔记吗？

A: 不支持。需要手动在小红书 App 中修改。

### Q: 支持发布视频吗？

A: 目前只支持图文笔记，不支持视频。

### Q: 为什么有时候发布很慢？

A: 这是正常现象。xiaohongshu-mcp 使用浏览器自动化，需要等待页面加载、图片上传等，通常需要 30-60 秒。
