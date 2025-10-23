# 小红书发布问题修复说明

## 修复日期
2025-10-20

## 问题描述

小红书发布功能总是因为图片问题失败，主要原因：
1. 缺少 `load_prompts=False` 参数导致 "Method not found" 错误
2. Agent Instructions 不够详细，LLM 误解工具能力
3. 没有超时配置，发布操作可能超时
4. 依赖 Agent 理解，而非直接调用工具

## 修复内容

### 1. 添加关键参数

```python
async with MCPStreamableHTTPTool(
    name="xiaohongshu-mcp",
    url=self.xhs_mcp_url,
    load_tools=True,
    load_prompts=False,  # ✅ 避免 "Method not found" 错误
    timeout=300  # ✅ 5分钟超时，发布操作可能耗时较长
) as xhs_tool:
```

**为什么需要这些参数？**
- `load_prompts=False`: xiaohongshu-mcp 服务不支持 prompts 方法，必须禁用
- `timeout=300`: 发布操作包括图片上传，可能耗时较长，默认超时太短

### 2. 直接调用工具（主要方案）

```python
# ✅ 直接调用 publish_content 工具
result = await xhs_tool.call_tool("publish_content", {
    "title": title,
    "content": content_with_tags,
    "images": images,
    "tags": tags or []
})
```

**优势**：
- 避免 LLM 误解工具参数
- 更快、更可靠
- 减少 token 消耗
- 确保参数格式正确

### 3. Agent 作为备用方案

如果直接调用失败，会自动切换到 Agent 方式，并使用增强的 Instructions：

```python
instructions="""你是小红书发布助手。

**可用工具**: publish_content

**工具参数说明**:
- title (string, required): 内容标题（最多20个字）
- content (string, required): 正文内容（最多1000个字）
- images (array of strings, required): 图片路径列表
  * 支持本地绝对路径（推荐）: 如 "D:\\Pictures\\image.jpg"
  * 支持 HTTP/HTTPS 链接: 如 "https://example.com/image.jpg"
  * 至少需要1张图片
- tags (array of strings, optional): 话题标签列表

**重要**: images 参数可以直接使用本地文件路径，不需要上传到网络。
"""
```

**改进点**：
- 明确说明图片支持本地路径
- 详细的参数类型和限制
- 提供具体示例
- 强调关键信息

## 图片路径配置

### 方式 1：环境变量（推荐）

在 `.env` 文件中配置默认图片：

```bash
# 单张图片
XHS_DEFAULT_IMAGES=D:\Pictures\default.jpg

# 多张图片（逗号分隔）
XHS_DEFAULT_IMAGES=D:\Pictures\img1.jpg,D:\Pictures\img2.jpg,D:\Pictures\img3.jpg
```

### 方式 2：在文案中提供

内容生成智能体可以在 JSON 中包含图片路径：

```json
{
  "title": "标题",
  "content": "内容",
  "images": [
    "D:\\Pictures\\image1.jpg",
    "D:\\Pictures\\image2.jpg"
  ],
  "tags": ["标签1", "标签2"]
}
```

## 支持的图片格式

1. **本地绝对路径**（推荐）
   - Windows: `D:\\Pictures\\image.jpg`
   - Linux/Mac: `/home/user/pictures/image.jpg`
   - 优势：不需要网络，速度快

2. **HTTP/HTTPS 链接**
   - `https://example.com/image.jpg`
   - 优势：可以使用网络图片

## 使用流程

### 1. 确保 xiaohongshu-mcp 服务运行

```bash
# 检查服务是否运行
curl http://localhost:18060/mcp

# 如果没有运行，启动服务
# （具体启动命令取决于你的 xiaohongshu-mcp 配置）
```

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# 小红书 MCP 服务地址
XIAOHONGSHU_MCP_URL=http://localhost:18060/mcp

# 默认图片路径（可选）
XHS_DEFAULT_IMAGES=D:\Pictures\default1.jpg,D:\Pictures\default2.jpg
```

### 3. 确保已登录小红书

使用 `xiaohongshu-login` 工具完成登录（只需一次）

### 4. 运行工作流

```bash
python test_devui_final.py
```

## 日志说明

修复后的代码会输出详细日志：

```
[xhs_publisher] 直接调用 publish_content 工具...
[xhs_publisher]   标题: 测试标题
[xhs_publisher]   内容长度: 150
[xhs_publisher]   图片: ['D:\\Pictures\\test.jpg']
[xhs_publisher]   标签: ['测试', '小红书']
[xhs_publisher] 工具调用成功
```

如果直接调用失败，会看到：

```
[xhs_publisher] 直接调用工具失败: xxx
[xhs_publisher] 尝试使用 Agent 方式...
```

## 常见问题

### Q1: 仍然提示 "Method not found"
**A**: 确保添加了 `load_prompts=False` 参数

### Q2: 图片上传失败
**A**: 检查：
- 图片路径是否正确（使用绝对路径）
- 图片文件是否存在
- 图片格式是否支持（JPG、PNG）
- 图片大小是否合理（不要太大）

### Q3: 超时错误
**A**: 
- 检查网络连接
- 增加 `timeout` 参数值
- 减少图片数量或大小

### Q4: 标题或内容被截断
**A**: 
- 标题限制：20个字（使用 `runewidth.StringWidth()` 计算，中文占2个单位）
- 内容限制：1000个字
- 代码会自动截断超长内容

## 技术细节

### 为什么使用 runewidth？

小红书使用 `runewidth.StringWidth()` 计算字符宽度：
- 英文字符：1个单位
- 中文字符：2个单位
- 标题限制：40个单位（约20个中文字）

### 工具调用流程

1. **直接调用**（主要方案）
   ```
   XiaohongshuPublisher -> MCPStreamableHTTPTool.call_tool() -> xiaohongshu-mcp
   ```

2. **Agent 调用**（备用方案）
   ```
   XiaohongshuPublisher -> Agent -> MCPStreamableHTTPTool -> xiaohongshu-mcp
   ```

## 测试建议

1. **先测试连接**
   ```bash
   curl http://localhost:18060/mcp
   ```

2. **使用简单内容测试**
   - 短标题（10字以内）
   - 短内容（100字以内）
   - 1张小图片

3. **逐步增加复杂度**
   - 增加内容长度
   - 增加图片数量
   - 添加更多标签

## 修改的文件

- `agents/social_media_workflow/__init__.py` - XiaohongshuPublisher 类

## 相关文档

- [xiaohongshu-mcp 文档](https://github.com/xpzouying/xiaohongshu-mcp)
- [Agent Framework MCP 工具文档](https://github.com/microsoft/agent-framework)

## 总结

通过以下改进，小红书发布功能现在更加稳定可靠：

✅ 添加 `load_prompts=False` 避免错误
✅ 添加 `timeout=300` 处理长时间操作
✅ 直接调用工具，避免 LLM 误解
✅ 增强 Instructions，提供详细说明
✅ 支持本地图片路径
✅ 详细的日志输出
✅ 自动降级到 Agent 方式

