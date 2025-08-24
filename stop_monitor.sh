#!/bin/bash

# VPS监控停止脚本
# 用于停止VPS监控和自动拉起服务

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查PID文件
if [ -f "vps_monitor.pid" ]; then
    MONITOR_PID=$(cat vps_monitor.pid)
    
    # 检查进程是否还在运行
    if ps -p $MONITOR_PID > /dev/null 2>&1; then
        echo "停止VPS监控服务，PID: $MONITOR_PID"
        kill $MONITOR_PID
        
        # 等待进程结束
        sleep 2
        
        # 检查是否已经停止
        if ps -p $MONITOR_PID > /dev/null 2>&1; then
            echo "强制停止进程..."
            kill -9 $MONITOR_PID
        fi
        
        echo "VPS监控服务已停止"
    else
        echo "进程 $MONITOR_PID 不在运行"
    fi
    
    # 删除PID文件
    rm -f vps_monitor.pid
else
    echo "未找到PID文件，尝试通过进程名停止..."
    # 查找并停止所有vps_monitor.py进程
    pkill -f "python3 vps_monitor.py"
    echo "已停止所有vps_monitor.py进程"
fi