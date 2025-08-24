#!/bin/bash
# Docker停止脚本

echo "🛑 停止VPS监控容器..."

# 停止容器
docker-compose down

# 清理未使用的镜像（可选）
read -p "是否清理未使用的镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理未使用的镜像..."
    docker image prune -f
fi

echo "✅ 容器已停止"