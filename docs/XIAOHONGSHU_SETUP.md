# 小红书发布配置指南

本文档说明如何配置小红书自动发布功能。

## 前置要求

1. **Chrome 浏览器**：确保已安装 Chrome 浏览器
2. **Node.js**：用于运行 ChromeDriver 安装工具
3. **Python uv**：用于运行 xhs_mcp_server

## 配置步骤

### 1. 安装 ChromeDriver

查找你的 Chrome 浏览器版本：
- 打开 Chrome
- 访问 `chrome://version/`
- 记下版本号（例如：`134.0.6998.166`）

安装对应版本的 ChromeDriver：

```bash
npx @puppeteer/browsers install chromedriver@134.0.6998.166
```

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```env
# 小红书手机号
XHS_PHONE=13800138000

# Cookie 存储路径（使用绝对路径）
# Windows 示例：
XHS_JSON_PATH=C:\Users\YourName\xhs_cookies

# macOS/Linux 示例：
# XHS_JSON_PATH=/Users/YourName/xhs_cookies
```

### 3. 登录小红书账号

运行登录命令（使用你的实际配置）：

**Windows (PowerShell):**
```powershell
# 方式 1：设置环境变量后运行
$env:phone="13800138000"
$env:json_path="C:\Users\YourName\xhs_cookies"
uvx --from xhs_mcp_server@latest login

# 方式 2：一行命令（推荐）
$env:phone="13800138000"; $env:json_path="C:\Users\YourName\xhs_cookies"; uvx --from xhs_mcp_server@latest login
```

**macOS/Linux:**
```bash
env phone=13800138000 json_path=/Users/YourName/xhs_cookies uvx --from xhs_mcp_server@latest login
```

终端会显示：
```
无效的 cookies，已清理
请输入验证码:
```

在终端输入接收到的验证码并回车。

### 4. 验证登录

再次运行登录命令验证：

```bash
# Windows
$env:phone="13800138000"; $env:json_path="C:\Users\YourName\xhs_cookies"; uvx --from xhs_mcp_server@latest login

# macOS/Linux
env phone=13800138000 json_path=/Users/YourName/xhs_cookies uvx --from xhs_mcp_server@latest login
```

成功会显示：
```
使用 cookies 登录成功
```

### 5. 测试发布（可选）

使用 MCP Inspector 测试：

```bash
npx @modelcontextprotocol/inspector \
  -e phone=13800138000 \
  -e json_path=/Users/YourName/xhs_cookies \
  uvx xhs_mcp_server@latest
```

在 Inspector 中可以测试发布功能。

## 使用 Workflow

配置完成后，运行 workflow：

```bash
python test_devui_final.py
```

访问 http://localhost:9000，输入查询如"获取今日热点并发布到小红书"。

Workflow 会：
1. 📊 获取热点数据
2. 🧠 使用 think-tool 深度分析
3. ✍️ 生成小红书文案
4. 🚀 自动发布到小红书

## 注意事项

1. **仅限研究用途**：此工具仅供学习研究，禁止用于商业目的
2. **Cookie 安全**：妥善保管 cookie 文件，不要泄露
3. **发布频率**：避免频繁发布，以免被平台限制
4. **内容审核**：发布前请确保内容符合平台规范

## 故障排除

### ChromeDriver 版本不匹配

错误：`ChromeDriver version mismatch`

解决：重新安装匹配的 ChromeDriver 版本

### Cookie 过期

错误：`无效的 cookies`

解决：重新运行登录命令

### 发布超时

警告：`Error Request timed out`

说明：这是正常现象，笔记通常仍会成功发布。检查小红书 App 确认。

## 相关链接

- [xhs_mcp_server GitHub](https://github.com/your-repo/xhs_mcp_server)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Agent Framework](https://github.com/microsoft/agent-framework)
