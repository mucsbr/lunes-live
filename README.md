# VPS监控和自动拉起系统

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://www.docker.com/)

一个用于监控Pterodactyl面板中VPS状态并自动拉起关闭机器的系统。

## ✨ 主要功能

- 🔐 **自动登录认证** - 支持Laravel Sanctum认证流程
- 📡 **实时监控** - WebSocket实时监控服务器状态
- 🔄 **自动恢复** - 检测到服务器关闭时自动启动
- 🔗 **SSHX链接提取** - 自动提取并通知SSHX远程访问链接
- 📱 **钉钉通知** - 支持钉钉机器人通知（可选）
- 🐳 **Docker支持** - 完整的Docker部署方案
- 📊 **重试机制** - 智能重试和错误恢复
- 📝 **完整日志** - 详细的操作日志记录

## 🚀 快速开始

### 方式一：Docker部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/vps-monitor.git
cd vps-monitor

# 2. 配置环境变量
cp .env.example .env
nano .env

# 3. 启动服务
./docker-start.sh
```

### 方式二：本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
nano .env

# 3. 运行监控
python3 vps_monitor.py
```

## ⚙️ 配置说明

### 环境变量配置

创建 `.env` 文件并配置以下参数：

```bash
# Pterodactyl面板配置
PANEL_URL=https://your-panel.com
SERVER_ID=your-server-id
SERVER_UUID=your-server-uuid
NODE_HOST=node.your-panel.com
WS_PORT=8080

# 认证配置
USERNAME=your-username
PASSWORD=your-password

# 监控配置
CHECK_INTERVAL=30
MAX_RETRIES=3

# 钉钉通知配置（可选）
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your-token
```

### 配置参数说明

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `PANEL_URL` | Pterodactyl面板地址 | ✅ | - |
| `SERVER_ID` | 服务器ID | ✅ | - |
| `SERVER_UUID` | 服务器UUID | ✅ | - |
| `NODE_HOST` | 节点主机名 | ✅ | - |
| `WS_PORT` | WebSocket端口 | ❌ | 8080 |
| `USERNAME` | 登录用户名 | ✅ | - |
| `PASSWORD` | 登录密码 | ✅ | - |
| `CHECK_INTERVAL` | 检查间隔（秒） | ❌ | 30 |
| `MAX_RETRIES` | 最大重试次数 | ❌ | 3 |
| `DINGTALK_WEBHOOK_URL` | 钉钉webhook地址 | ❌ | - |

## 📋 系统要求

- Python 3.11+
- Pterodactyl面板
- 服务器具有WebSocket支持
- （可选）Docker和Docker Compose

## 🔧 详细配置

### 获取Pterodactyl配置信息

1. **服务器ID和UUID**：
   - 登录Pterodactyl面板
   - 进入服务器详情页
   - 查看URL或页面源代码获取

2. **节点主机名**：
   - 在服务器设置中查看节点信息
   - 通常格式为 `node1.yourdomain.com`

3. **WebSocket端口**：
   - 默认为8080
   - 可在节点配置中确认

### 钉钉机器人配置（可选）

1. 在钉钉群中添加自定义机器人
2. 获取webhook URL
3. 添加到环境变量中

## 📊 监控状态说明

- **starting** - 服务器运行中
- **offline** - 服务器已关闭，需要启动
- **stopping** - 服务器正在停止
- **installing** - 服务器正在安装

## 🛠️ 管理命令

### Docker管理

```bash
# 启动服务
./docker-start.sh

# 停止服务
./docker-stop.sh

# 查看日志
docker-compose logs -f vps-monitor

# 重启服务
docker-compose restart vps-monitor

# 进入容器
docker-compose exec vps-monitor bash
```

### 本地管理

```bash
# 启动监控
python3 vps_monitor.py

# 查看日志
tail -f vps_monitor.log

# 测试认证
python3 test_auth.py

# 测试WebSocket
python3 test_websocket.py
```

## 🧪 测试工具

项目包含多个测试和调试工具：

```bash
# 完整认证流程测试
python3 test_auth.py

# WebSocket连接测试（30秒）
python3 test_websocket.py

# 实时WebSocket监控
python3 websocket_monitor.py

# CSRF Token分析
python3 csrf_analyzer.py

# 419错误调试
python3 debug_419.py
```

## 🔍 故障排除

### 常见问题

1. **认证失败**
   - 检查用户名密码是否正确
   - 确认面板URL是否正确
   - 运行 `python3 test_auth.py` 测试

2. **WebSocket连接失败**
   - 检查节点主机名和端口
   - 确认防火墙设置
   - 运行 `python3 test_websocket.py` 测试

3. **服务器启动失败**
   - 检查服务器资源状态
   - 确认没有其他电源操作冲突
   - 查看详细日志错误信息

### 日志分析

日志文件位置：
- 本地：`vps_monitor.log`
- Docker：`./logs/vps_monitor.log`

### 调试模式

启用详细日志：
```bash
export PYTHONPATH=/app
export LOG_LEVEL=DEBUG
python3 vps_monitor.py
```

## 📈 性能优化

- 调整 `CHECK_INTERVAL` 平衡监控频率和性能
- 设置合理的 `MAX_RETRIES` 避免过度重试
- 定期清理日志文件避免磁盘空间不足
- 使用Docker部署便于管理和扩展

## 🔒 安全建议

- 不要在代码中硬编码敏感信息
- 使用环境变量或配置文件
- 定期更新访问密码
- 限制网络访问权限
- 监控日志文件权限

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用Apache 2.0许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Pterodactyl](https://pterodactyl.io/) - 优秀的游戏服务器管理面板
- [aiohttp](https://docs.aiohttp.org/) - 异步HTTP客户端/服务器
- [websockets](https://websockets.readthedocs.io/) - WebSocket库

---

⭐ 如果这个项目对你有帮助，请给个星标！