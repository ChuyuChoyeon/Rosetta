# 使用官方 Python 3.14 镜像 (根据 pyproject.toml 中的要求)
# 如果 3.14 尚未发布或不稳定，建议回退到 3.12/3.13，但这里遵循 pyproject.toml 的 >=3.14
FROM python:3.14-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=Rosetta.settings

# 安装系统依赖 (如有需要，例如 psycopg2 的构建依赖)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装 Python 依赖
# 优先使用 requirements.txt (由 uv 生成)，如果没有则尝试 pip install .
RUN if [ -f "requirements.txt" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir .; \
    fi

# 授予启动脚本执行权限
RUN chmod +x start.sh

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["./start.sh"]
