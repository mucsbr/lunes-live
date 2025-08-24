#!/bin/bash

# 测试运行脚本
# 用于运行VPS监控系统的单元测试

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
pip install -r test-requirements.txt

# 运行测试
echo "运行测试..."

# 运行所有测试
if [ "$1" = "--all" ] || [ -z "$1" ]; then
    echo "运行所有测试..."
    python -m pytest tests/ -v
    
# 运行特定测试文件
elif [ "$1" = "--file" ] && [ -n "$2" ]; then
    echo "运行测试文件: $2"
    python -m pytest tests/$2 -v
    
# 运行特定测试类或方法
elif [ "$1" = "--test" ] && [ -n "$2" ]; then
    echo "运行特定测试: $2"
    python -m pytest tests/ -v -k "$2"
    
# 显示测试覆盖率
elif [ "$1" = "--coverage" ]; then
    echo "运行测试覆盖率分析..."
    pip install pytest-cov
    python -m pytest tests/ --cov=vps_monitor --cov-report=html --cov-report=term
    
# 显示帮助
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "使用方法:"
    echo "  ./run_tests.sh              运行所有测试"
    echo "  ./run_tests.sh --all        运行所有测试"
    echo "  ./run_tests.sh --file FILE  运行特定测试文件"
    echo "  ./run_tests.sh --test NAME  运行特定测试类或方法"
    echo "  ./run_tests.sh --coverage   显示测试覆盖率"
    echo "  ./run_tests.sh --help       显示帮助"
    echo ""
    echo "示例:"
    echo "  ./run_tests.sh --file test_vps_monitor.py"
    echo "  ./run_tests.sh --test TestVPSMonitor"
    echo "  ./run_tests.sh --test test_login_success"
    
else
    echo "未知参数: $1"
    echo "使用 ./run_tests.sh --help 查看帮助"
    exit 1
fi

echo "测试完成"