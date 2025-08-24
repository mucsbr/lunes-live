FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

设置阿里云APT源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY vps_monitor.py .
COPY start_monitor.sh .
COPY stop_monitor.sh .

# 设置脚本可执行权限
RUN chmod +x start_monitor.sh stop_monitor.sh

# 创建日志目录
RUN mkdir -p /app/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口（如果需要）
EXPOSE 8080

# 启动命令
CMD ["python", "vps_monitor.py"]