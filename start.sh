#!/bin/bash
set -e

# 环境变量设置
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

echo "🚀 正在启动部署脚本..."

# 安装依赖
if [ -f "requirements.txt" ]; then
    echo "📦 正在安装依赖 (requirements.txt)..."
    pip install --break-system-packages --no-cache-dir -r requirements.txt
else
    echo "⚠️ 未找到 requirements.txt，跳过依赖安装。"
fi

# 收集静态文件
echo "🎨 正在收集静态文件..."
python manage.py collectstatic --noinput

# 应用数据库迁移
echo "🗄️ 正在应用数据库迁移..."
python manage.py migrate

# 构建搜索索引 (django-watson)
echo "🔍 正在构建搜索索引..."
python manage.py buildwatson

# 启动服务器
echo "🔥 正在启动 Uvicorn 服务器..."

exec uvicorn Rosetta.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --proxy-headers \
    --log-level info
