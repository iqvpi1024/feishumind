# FeishuMind Docker 镜像
#
# 多阶段构建，优化镜像大小和安全性

# 阶段 1: 构建阶段
FROM python:3.12-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到临时目录
RUN pip install --no-cache-dir --user -r requirements.txt

# 阶段 2: 运行阶段
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# 创建非 root 用户
RUN useradd -m -u 1000 feishumind

# 设置工作目录
WORKDIR /app

# 从构建阶段复制 Python 包
COPY --from=builder /root/.local /root/.local

# 复制项目文件
COPY src/ ./src/
COPY data/ ./data/
COPY pyproject.toml .

# 创建必要的目录
RUN mkdir -p logs data/memory && \
    chown -R feishumind:feishumind /app

# 切换到非 root 用户
USER feishumind

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
