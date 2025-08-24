# 测试目录

这个目录包含VPS监控系统的所有单元测试。

## 测试文件结构

- `test_vps_monitor.py` - 主要功能测试
- `test_config.py` - 配置测试
- `test_authentication.py` - 认证流程测试
- `test_websocket.py` - WebSocket连接测试
- `test_auto_recovery.py` - 自动恢复功能测试
- `test_integration.py` - 集成测试

## 运行测试

### 运行所有测试
```bash
./run_tests.sh
```

### 运行特定测试文件
```bash
./run_tests.sh --file test_vps_monitor.py
```

### 运行特定测试类或方法
```bash
./run_tests.sh --test TestVPSMonitor
./run_tests.sh --test test_login_success
```

### 查看测试覆盖率
```bash
./run_tests.sh --coverage
```

### 查看帮助
```bash
./run_tests.sh --help
```

## 测试覆盖范围

### 核心功能测试
- 配置管理和验证
- HTTP会话管理
- CSRF token获取
- 用户认证流程
- 登录状态检查
- WebSocket连接建立
- 消息处理和解析
- 状态监控逻辑
- 自动重启功能
- SSHX链接提取
- 错误处理和恢复
- 资源清理

### 集成测试
- 完整监控周期
- 错误处理和恢复
- 并发操作处理
- 长时间运行稳定性
- 配置验证

### 测试特性
- 异步测试支持
- Mock和异步Mock
- 异常情况处理
- 边界条件测试
- 性能和稳定性测试

## 测试依赖

- `pytest` - 测试框架
- `pytest-asyncio` - 异步测试支持
- `pytest-mock` - Mock对象支持
- `pytest-cov` - 覆盖率分析（可选）

## 测试配置

测试配置文件 `pytest.ini` 包含：
- 测试发现规则
- 异步测试模式
- 测试标记定义
- 输出格式设置

## 测试最佳实践

1. 每个测试函数应该独立运行
2. 使用Mock对象隔离外部依赖
3. 测试成功和失败场景
4. 包含边界条件和异常情况
5. 使用描述性的测试名称
6. 保持测试代码简洁和可维护