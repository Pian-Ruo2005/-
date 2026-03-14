#!/bin/bash
# 一键启动本地服务器，打开前端页面

PORT=8080
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 正在启动本地服务器..."
echo "   地址: http://localhost:$PORT"
echo "   按 Ctrl+C 停止服务"
echo ""

# 自动打开浏览器
if command -v open &>/dev/null; then
  open "http://localhost:$PORT" &   # macOS
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:$PORT" &  # Linux
fi

# 启动 Python HTTP 服务器
if command -v python3 &>/dev/null; then
  python3 -m http.server "$PORT" --directory "$DIR"
elif command -v python &>/dev/null; then
  cd "$DIR" && python -m SimpleHTTPServer "$PORT"
else
  echo "❌ 未找到 Python，请先安装 Python 或使用方法一（直接双击 index.html）"
  exit 1
fi
