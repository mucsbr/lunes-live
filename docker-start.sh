#!/bin/bash
# Docker启动脚本

echo "🚀 启动VPS监控容器..."

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，复制.env.example..."
    cp .env.example .env
    echo "✅ 请编辑.env文件并填入正确的配置信息"
    exit 1
fi

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 构建并启动容器
echo "🏗️  构建镜像..."
docker-compose build --no-cache

echo "🚀 启动容器..."
docker-compose up -d

# 显示容器状态
echo "📊 容器状态："
docker-compose ps

# 显示日志
echo "📋 容器日志："
docker-compose logs -f vps-monitor