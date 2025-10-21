# 启动 DevUI 的脚本，自动设置 ChromeDriver 路径

# 设置 ChromeDriver 路径
$chromeDriverPath = "E:\social-media-ai-system\chromedriver\win64-141.0.7390.108\chromedriver-win64"
$env:PATH = "$chromeDriverPath;$env:PATH"

Write-Host "✅ ChromeDriver 路径已设置" -ForegroundColor Green

# 验证 ChromeDriver
$version = chromedriver --version 2>&1
Write-Host "✅ ChromeDriver 版本: $version" -ForegroundColor Green

Write-Host ""
Write-Host "启动 DevUI..." -ForegroundColor Cyan
Write-Host ""

python test_devui_final.py
