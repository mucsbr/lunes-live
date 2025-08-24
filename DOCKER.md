# Docker部署指南

## 快速开始

### 1. 准备配置文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

### 2. 启动服务

```bash
# 使用启动脚本（推荐）
./docker-start.sh

# 或手动启动
docker-compose up -d
```

### 3. 查看日志

```bash
# 查看实时日志
docker-compose logs -f vps-monitor

# 查看最近日志
docker-compose logs vps-monitor
```

### 4. 停止服务

```bash
# 使用停止脚本
./docker-stop.sh

# 或手动停止
docker-compose down
```

## 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `PANEL_URL` | Pterodactyl面板地址 | - |
| `SERVER_ID` | 服务器ID | - |
| `SERVER_UUID` | 服务器UUID | - |
| `NODE_HOST` | 节点主机名 | - |
| `WS_PORT` | WebSocket端口 | `8080` |
| `USERNAME` | 登录用户名 | - |
| `PASSWORD` | 登录密码 | - |
| `CHECK_INTERVAL` | 检查间隔（秒） | `30` |
| `MAX_RETRIES` | 最大重试次数 | `3` |
| `DINGTALK_WEBHOOK_URL` | 钉钉webhook URL | - |

### 日志管理

日志文件会挂载到 `./logs` 目录：

- `vps_monitor.log` - 主日志文件
- 容器日志 - 通过 `docker-compose logs` 查看

## 管理命令

```bash
# 查看容器状态
docker-compose ps

# 重启容器
docker-compose restart vps-monitor

# 进入容器
docker-compose exec vps-monitor bash

# 查看资源使用情况
docker stats vps-monitor

# 更新镜像
docker-compose pull && docker-compose up -d
```

## 故障排除

### 1. 容器启动失败

```bash
# 查看详细错误信息
docker-compose logs vps-monitor

# 检查环境变量
docker-compose exec vps-monitor env
```

### 2. 网络连接问题

```bash
# 检查网络连接
docker-compose exec vps-monitor ping your-node-host

# 检查WebSocket连接
docker-compose exec vps-monitor curl -I https://your-node-host:8080
```

### 3. 配置更新

```bash
# 修改.env文件后重启容器
docker-compose restart vps-monitor
```

## 备份和恢复

### 备份

```bash
# 备份配置和日志
tar -czf vps-monitor-backup-$(date +%Y%m%d).tar.gz .env logs/
```

### 恢复

```bash
# 恢复配置和日志
tar -xzf vps-monitor-backup-YYYYMMDD.tar.gz
```

## 监控和告警

### 健康检查

容器包含健康检查，每30秒检查一次：

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' vps-monitor
```

### 资源监控

```bash
# 查看资源使用情况
docker stats vps-monitor --no-stream
```

## 安全建议

1. **不要提交.env文件到版本控制**
2. **定期更新镜像**
3. **监控日志文件大小**
4. **使用强密码**
5. **限制网络访问**