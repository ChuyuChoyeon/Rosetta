#!/bin/bash
set -e

# 设置环境变量
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

echo "Starting deployment script..."

# 检查是否安装了 python
if ! command -v python3 &> /dev/null; then
    echo "Python3 could not be found, please install it first."
    exit 1
fi

# 安装依赖
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
else
    echo "requirements.txt not found. Attempting to install from pyproject.toml..."
    pip install --no-cache-dir .
fi

# 收集静态文件
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# 应用数据库迁移
echo "Applying database migrations..."
python3 manage.py migrate

# 启动 uvicorn
echo "Starting Uvicorn server..."
# 使用 uvicorn 启动 ASGI 应用
# --host 0.0.0.0: 允许外部访问
# --port 8000: 监听 8000 端口
# --workers 4: 启动 4 个工作进程 (根据 CPU 核心数调整)
exec uvicorn Rosetta.asgi:application --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
