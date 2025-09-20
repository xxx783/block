# 使用官方Python运行时作为父镜像
FROM python:3.8-slim-buster

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt到工作目录
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制当前目录的所有内容到工作目录
COPY . .

# 创建instance目录用于存放SQLite数据库
RUN mkdir -p instance

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SECRET_KEY=your-secret-key-here

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["python", "app.py"]