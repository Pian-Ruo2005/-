@echo off
chcp 65001 >nul
title 小韩的空间 - 本地服务器

echo 🚀 正在启动本地服务器...
echo    地址: http://localhost:8080
echo    关闭此窗口可停止服务
echo.

cd /d "%~dp0"

:: 自动在浏览器中打开
start "" http://localhost:8080

:: 优先使用 Python 3，其次 Python 2
where python >nul 2>&1
if %errorlevel% == 0 (
  python -m http.server 8080
) else (
  echo ❌ 未找到 Python，请先安装 Python。
  echo    下载地址: https://www.python.org/downloads/
  pause
)
