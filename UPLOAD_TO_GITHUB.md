# 📤 上传到 GitHub 指南

## 方式一：使用 Git 命令行（推荐）

### 1. 初始化 Git 仓库

```bash
# 进入项目目录
cd E:\Agent

# 初始化 Git 仓库
git init

# 添加所有文件到暂存区
git add .

# 提交到本地仓库
git commit -m "Initial commit: 新媒体运营 AI 系统"
```

### 2. 在 GitHub 创建仓库

1. 访问 [GitHub](https://github.com/)
2. 点击右上角的 "+" 按钮
3. 选择 "New repository"
4. 填写仓库信息：
   - Repository name: `social-media-ai-system`
   - Description: `基于 Microsoft Agent Framework 的智能新媒体运营系统`
   - 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"
5. 点击 "Create repository"

### 3. 关联远程仓库并推送

```bash
# 关联远程仓库（替换 your-username 为你的 GitHub 用户名）
git remote add origin https://github.com/your-username/social-media-ai-system.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 4. 验证上传

访问你的 GitHub 仓库页面，确认所有文件已成功上传。

---

## 方式二：使用 GitHub Desktop（图形界面）

### 1. 下载并安装 GitHub Desktop

访问 [GitHub Desktop](https://desktop.github.com/) 下载安装。

### 2. 添加本地仓库

1. 打开 GitHub Desktop
2. 点击 "File" -> "Add local repository"
3. 选择项目目录 `E:\Agent`
4. 如果提示未初始化，点击 "create a repository"

### 3. 提交更改

1. 在左侧查看更改的文件
2. 在底部输入提交信息：`Initial commit: 新媒体运营 AI 系统`
3. 点击 "Commit to main"

### 4. 发布到 GitHub

1. 点击顶部的 "Publish repository"
2. 填写仓库名称和描述
3. 选择 Public 或 Private
4. 点击 "Publish repository"

---

## 方式三：使用 VS Code（如果你使用 VS Code）

### 1. 打开源代码管理

1. 在 VS Code 中打开项目文件夹
2. 点击左侧的源代码管理图标（或按 Ctrl+Shift+G）

### 2. 初始化仓库

1. 点击 "Initialize Repository"
2. 输入提交信息：`Initial commit: 新媒体运营 AI 系统`
3. 点击 ✓ 提交

### 3. 发布到 GitHub

1. 点击 "Publish to GitHub"
2. 选择仓库名称和可见性
3. 点击 "Publish"

---

## 📋 上传前检查清单

确保以下文件已准备好：

- [x] `.gitignore` - 已创建，保护敏感信息
- [x] `README.md` - 已创建，项目说明文档
- [x] `.env.example` - 已创建，环境变量模板
- [x] `LICENSE` - 已创建，MIT 许可证
- [x] `requirements.txt` - 已创建，依赖列表
- [x] `.env` - **已被 .gitignore 忽略**（不会上传）

⚠️ **重要提示**：
- `.env` 文件包含敏感信息（API 密钥），已被 `.gitignore` 排除
- 只有 `.env.example` 会被上传，作为配置模板
- 确保不要将真实的 API 密钥上传到 GitHub

---

## 🔄 后续更新

当你修改代码后，使用以下命令更新 GitHub：

```bash
# 查看更改
git status

# 添加更改的文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到 GitHub
git push
```

---

## 🆘 常见问题

### Q1: 推送时要求输入用户名和密码？

**A**: GitHub 已不再支持密码认证，需要使用个人访问令牌（PAT）：

1. 访问 GitHub Settings -> Developer settings -> Personal access tokens
2. 生成新的 token
3. 使用 token 作为密码

或者配置 SSH 密钥：

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到 GitHub
# 复制 ~/.ssh/id_ed25519.pub 的内容到 GitHub Settings -> SSH keys
```

### Q2: 文件太大无法上传？

**A**: GitHub 单个文件限制 100MB，如果有大文件：

1. 添加到 `.gitignore`
2. 或使用 Git LFS（Large File Storage）

### Q3: 如何删除已上传的敏感信息？

**A**: 如果不小心上传了 `.env` 文件：

```bash
# 从 Git 历史中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
```

然后立即更换泄露的 API 密钥！

---

## 📞 需要帮助？

如果遇到问题，可以：

1. 查看 [GitHub 官方文档](https://docs.github.com/)
2. 在项目中创建 Issue
3. 搜索相关错误信息

---

**祝你上传顺利！** 🎉