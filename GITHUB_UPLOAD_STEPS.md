# 📤 上传到 GitHub 详细步骤

## 方式一：使用自动化脚本（推荐）

### 1. 直接运行批处理文件

```bash
upload_to_github.bat
```

这个脚本会自动完成所有步骤！

---

## 方式二：手动执行命令

### 步骤 1: 初始化 Git 仓库

```bash
git init
```

### 步骤 2: 添加所有文件

```bash
git add .
```

### 步骤 3: 提交到本地仓库

```bash
git commit -m "feat: 新媒体运营 AI 系统 - 多智能体协作版本"
```

### 步骤 4: 关联远程仓库

```bash
git remote add origin https://github.com/shiro123444/social-media-ai-system.git
```

### 步骤 5: 设置主分支

```bash
git branch -M main
```

### 步骤 6: 推送到 GitHub

```bash
git push -u origin main --force
```

**注意**: 使用 `--force` 会覆盖远程仓库的内容，请确保这是你想要的。

---

## 验证上传

访问你的仓库查看：
https://github.com/shiro123444/social-media-ai-system

---

## 后续更新

当你修改代码后，使用以下命令更新：

```bash
# 查看更改
git status

# 添加更改
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到 GitHub
git push
```

---

## 常见问题

### Q1: 提示需要登录？

**方式 1: 使用 Personal Access Token (推荐)**

1. 访问 GitHub Settings → Developer settings → Personal access tokens
2. 生成新的 token (勾选 `repo` 权限)
3. 使用 token 作为密码

**方式 2: 配置 Git 凭据**

```bash
git config --global user.name "shiro123444"
git config --global user.email "your_email@example.com"
```

### Q2: 推送失败？

如果远程仓库已有内容，先拉取：

```bash
git pull origin main --allow-unrelated-histories
git push origin main
```

### Q3: 想要删除某些文件？

编辑 `.gitignore` 文件，然后：

```bash
git rm --cached filename
git commit -m "Remove file"
git push
```

---

## 📁 将要上传的文件

✅ 核心代码
- `simple_demo.py` - 演示版本
- `deepseek_demo.py` - DeepSeek 版本
- `start_social_media_system.py` - 完整系统
- `realtime_news_system.py` - 实时新闻系统

✅ 文档
- `README.md` - 项目说明
- `MCP_INTEGRATION_GUIDE.md` - MCP 集成指南
- `REALTIME_QUICKSTART.md` - 快速启动指南
- `UPLOAD_TO_GITHUB.md` - 上传指南

✅ 配置文件
- `requirements.txt` - 依赖列表
- `.env.example` - 环境变量模板
- `.gitignore` - Git 忽略规则
- `LICENSE` - 开源许可证

✅ 规格文档
- `.kiro/specs/social-media-ai-system/requirements.md`
- `.kiro/specs/social-media-ai-system/design.md`
- `.kiro/specs/social-media-ai-system/tasks.md`

❌ 不会上传（已在 .gitignore 中）
- `.env` - 你的 API 密钥（安全）
- `__pycache__/` - Python 缓存
- `*.pyc` - 编译文件

---

## 🎉 上传成功后

1. 访问仓库: https://github.com/shiro123444/social-media-ai-system
2. 查看 README 是否正确显示
3. 检查所有文件是否都已上传
4. 可以分享给其他人了！

---

## 📝 提交信息规范

建议使用以下格式：

- `feat: 添加新功能`
- `fix: 修复bug`
- `docs: 更新文档`
- `style: 代码格式调整`
- `refactor: 代码重构`
- `test: 添加测试`
- `chore: 其他更改`

例如：
```bash
git commit -m "feat: 添加实时新闻抓取功能"
git commit -m "docs: 更新 README 文档"
git commit -m "fix: 修复工作流连接问题"
```

---

准备好了吗？运行 `upload_to_github.bat` 开始上传！🚀