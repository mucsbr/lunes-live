#!/bin/bash

# VPS监控启动脚本
# 用于启动VPS监控和自动拉起服务

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请先安装Python 3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 启动监控服务
echo "启动VPS监控服务..."
nohup python3 vps_monitor.py > logs/vps_monitor.log 2>&1 &
MONITOR_PID=$!

echo "VPS监控服务已启动，PID: $MONITOR_PID"
echo "日志文件: logs/vps_monitor.log"
echo "使用以下命令停止服务:"
echo "  kill $MONITOR_PID"
echo "或者使用停止脚本:"
echo "  ./stop_monitor.sh"

# 保存PID到文件
echo $MONITOR_PID > vps_monitor.pid