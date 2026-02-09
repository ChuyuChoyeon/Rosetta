FROM python:3.14.0

# 设置环境变量
# PYTHONDONTWRITEBYTECODE: 防止 Python 写入 .pyc 文件
# PYTHONUNBUFFERED: 确保日志直接输出到控制台
# UV_COMPILE_BYTECODE: uv 安装时编译字节码，加快启动
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    DJANGO_SETTINGS_MODULE=Rosetta.settings

# 设置工作目录
WORKDIR /app

# 安装系统依赖
# 1. curl/gnupg: 用于下载 Node.js
# 2. Node.js (v20): 用于 Tailwind CSS 构建
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 从官方镜像复制 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制项目依赖定义
# 注意：由于 uv.lock 未提交到版本控制，此处只复制 pyproject.toml
# 构建时将自动解析依赖并生成新的锁定文件
COPY pyproject.toml ./

# 安装 Python 依赖
# 移除 --frozen: 允许重新解析依赖
# --no-dev: 不安装开发依赖
RUN uv sync --no-dev

# 复制项目代码
COPY . .

# --- 构建阶段 ---

# 1. 安装 Tailwind 依赖
RUN uv run python manage.py tailwind install

# 2. 构建 Tailwind CSS
RUN uv run python manage.py tailwind build

# 3. 收集静态文件 (WhiteNoise 将在此步骤处理文件)
# 这一步会生成带有哈希指纹的静态文件到 STATIC_ROOT
RUN uv run python manage.py collectstatic --noinput

# --- 运行时配置 ---

# 暴露端口
EXPOSE 8000

# 启动命令
# 使用 Gunicorn + UvicornWorker
# 既拥有 Gunicorn 的进程管理能力，又拥有 Uvicorn 的异步高性能
# -k uvicorn.workers.UvicornWorker: 指定 Worker 类型
# Rosetta.asgi:application: 指向 ASGI 应用入口 (而非 WSGI)
CMD ["uv", "run", "gunicorn", "Rosetta.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
