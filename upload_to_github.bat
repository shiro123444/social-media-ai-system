@echo off
echo ========================================
echo 上传到 GitHub 仓库
echo ========================================
echo.

REM 初始化 Git 仓库（如果还没有）
if not exist .git (
    echo 初始化 Git 仓库...
    git init
    echo.
)

REM 添加所有文件
echo 添加文件到暂存区...
git add .
echo.

REM 提交更改
echo 提交更改...
git commit -m "feat: 新媒体运营 AI 系统 - 多智能体协作版本"
echo.

REM 设置远程仓库（如果还没有）
git remote remove origin 2>nul
echo 设置远程仓库...
git remote add origin https://github.com/shiro123444/social-media-ai-system.git
echo.

REM 设置主分支
echo 设置主分支...
git branch -M main
echo.

REM 推送到 GitHub
echo 推送到 GitHub...
git push -u origin main --force
echo.

echo ========================================
echo 上传完成！
echo 访问: https://github.com/shiro123444/social-media-ai-system
echo ========================================
pause