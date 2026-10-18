#!/bin/bash
# 学术中译英质量保障平台 - 一键启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 项目目录：$SCRIPT_DIR"

# ============================================================
# 启动后端
# ============================================================

echo ""
echo "🚀 启动后端服务..."
cd "$SCRIPT_DIR/backend"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ 已激活 Python 虚拟环境"
else
    echo "⚠️  未找到虚拟环境，请先运行："
    echo "   cd backend && python3 -m venv .venv && source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 后台启动 uvicorn
PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
echo "✅ 后端启动成功 (PID: $BACKEND_PID)"
echo "   📖 API 文档：http://127.0.0.1:8000/docs"

# ============================================================
# 启动前端
# ============================================================

echo ""
echo "🎨 启动前端服务..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端启动成功 (PID: $FRONTEND_PID)"

echo ""
echo "============================================"
echo "🎉 平台启动完成！"
echo "   前端地址：http://localhost:5173"
echo "   后端地址：http://127.0.0.1:8000"
echo "   API 文档：http://127.0.0.1:8000/docs"
echo "============================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待并在退出时清理
trap "echo '正在停止...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
