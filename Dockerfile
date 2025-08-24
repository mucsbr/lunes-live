FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

#设置阿里云APT源
RUN \
    # 1. 直接覆盖主源文件
    printf "deb https://mirrors.aliyun.com/debian/ trixie main\ndeb https://mirrors.aliyun.com/debian-security trixie-security main\ndeb https://mirrors.aliyun.com/debian/ trixie-updates main\n" > /etc/apt/sources.list && \
    # 2. 删除所有额外的源配置
    rm -rf /etc/apt/sources.list.d/* 2>/dev/null || true && \
    # 3. 更新包列表
    apt-get update

# 安装系统依赖
RUN apt-get install -y \
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
