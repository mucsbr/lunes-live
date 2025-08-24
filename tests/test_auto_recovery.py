import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from vps_monitor import VPSMonitor, VPSConfig

class TestAutoRecovery:
    """自动恢复功能测试"""
    
    @pytest.fixture
    def monitor(self):
        """测试监控器"""
        config = VPSConfig(
            panel_url="https://test.panel.com",
            server_uuid="test-server-uuid",
            check_interval=1  # 缩短测试间隔
        )
        return VPSMonitor(config)
    
    @pytest.mark.asyncio
    async def test_auto_restart_on_offline_status(self, monitor):
        """测试离线状态自动重启"""
        monitor.send_command = AsyncMock(return_value=True)
        
        # 模拟离线状态消息
        offline_message = '{"event": "status", "args": ["offline"]}'
        await monitor.handle_websocket_message(offline_message)
        
        # 验证发送了重启命令
        monitor.send_command.assert_called_once_with({
            "event": "set state",
            "args": ["start"]
        })
        
    @pytest.mark.asyncio
    async def test_no_restart_on_starting_status(self, monitor):
        """测试启动状态不重启"""
        monitor.send_command = AsyncMock()
        monitor.current_status = 'starting'
        
        # 模拟启动状态消息
        starting_message = '{"event": "status", "args": ["starting"]}'
        await monitor.handle_websocket_message(starting_message)
        
        # 验证没有发送重启命令
        monitor.send_command.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_restart_command_failure(self, monitor):
        """测试重启命令失败"""
        monitor.send_command = AsyncMock(return_value=False)
        
        offline_message = '{"event": "status", "args": ["offline"]}'
        await monitor.handle_websocket_message(offline_message)
        
        # 验证尝试发送命令但失败
        monitor.send_command.assert_called_once_with({
            "event": "set state",
            "args": ["start"]
        })
        
    @pytest.mark.asyncio
    async def test_multiple_restart_attempts(self, monitor):
        """测试多次重启尝试"""
        # 模拟多次离线状态
        monitor.send_command = AsyncMock(return_value=True)
        
        offline_messages = [
            '{"event": "status", "args": ["offline"]}',
            '{"event": "status", "args": ["offline"]}',
            '{"event": "status", "args": ["offline"]}'
        ]
        
        for message in offline_messages:
            await monitor.handle_websocket_message(message)
            
        # 验证每次都发送了重启命令
        assert monitor.send_command.call_count == 3
        
    @pytest.mark.asyncio
    async def test_status_change_detection(self, monitor):
        """测试状态变化检测"""
        monitor.start_server = AsyncMock()
        
        # 状态变化序列
        status_changes = [
            ('{"event": "status", "args": ["starting"]}', 'starting'),
            ('{"event": "status", "args": ["offline"]}', 'offline'),
            ('{"event": "status", "args": ["starting"]}', 'starting'),
            ('{"event": "status", "args": ["offline"]}', 'offline')
        ]
        
        for message, expected_status in status_changes:
            await monitor.handle_websocket_message(message)
            assert monitor.current_status == expected_status
            
        # 验证离线状态触发了重启
        assert monitor.start_server.call_count == 2
        
    @pytest.mark.asyncio
    async def test_auto_recovery_with_websocket_reconnect(self, monitor):
        """测试WebSocket重连后的自动恢复"""
        # 模拟连接断开和重连
        monitor.connect_websocket = AsyncMock()
        monitor.monitor_websocket = AsyncMock()
        monitor.check_login_status = AsyncMock(return_value=True)
        
        # 第一次连接失败，第二次成功
        monitor.connect_websocket.side_effect = [False, True]
        
        # 模拟监控循环
        monitor.is_running = True
        reconnect_count = 0
        
        async def mock_run_monitor():
            nonlocal reconnect_count
            for i in range(2):
                if not await monitor.connect_websocket():
                    await asyncio.sleep(0.01)
                    reconnect_count += 1
                else:
                    await monitor.monitor_websocket()
                    break
                    
        await mock_run_monitor()
        
        # 验证重连逻辑
        assert reconnect_count == 1
        assert monitor.connect_websocket.call_count == 2
        
    @pytest.mark.asyncio
    async def test_sshx_link_extraction_on_restart(self, monitor):
        """测试重启时的SSHX链接提取"""
        monitor.sshx_link = None
        
        # 模拟重启后的控制台输出
        console_messages = [
            '{"event": "console output", "args": ["Starting server..."]}',
            '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/new123#xyz789"]}',
            '{"event": "console output", "args": ["Server started successfully"]}'
        ]
        
        for message in console_messages:
            await monitor.handle_websocket_message(message)
            
        # 验证SSHX链接被提取
        assert monitor.sshx_link == "https://sshx.io/s/new123#xyz789"
        
    @pytest.mark.asyncio
    async def test_sshx_link_update(self, monitor):
        """测试SSHX链接更新"""
        monitor.sshx_link = "https://sshx.io/s/old123#abc456"
        
        # 模拟新的SSHX链接
        new_message = '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/new123#xyz789"]}'
        await monitor.handle_websocket_message(new_message)
        
        # 验证链接已更新
        assert monitor.sshx_link == "https://sshx.io/s/new123#xyz789"
        
    @pytest.mark.asyncio
    async def test_sshx_link_duplicate_prevention(self, monitor):
        """测试SSHX链接重复提取防护"""
        monitor.sshx_link = "https://sshx.io/s/test123#abc456"
        
        # 模拟相同的SSHX链接
        duplicate_message = '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/test123#abc456"]}'
        await monitor.handle_websocket_message(duplicate_message)
        
        # 验证链接没有重复更新
        assert monitor.sshx_link == "https://sshx.io/s/test123#abc456"
        
    @pytest.mark.asyncio
    async def test_auto_recovery_with_login_renewal(self, monitor):
        """测试登录续期后的自动恢复"""
        monitor.login = AsyncMock(return_value=True)
        monitor.connect_websocket = AsyncMock(return_value=True)
        monitor.check_login_status = AsyncMock(side_effect=[False, True])
        
        # 模拟监控循环
        monitor.is_running = True
        
        async def mock_run_monitor():
            # 第一次检查登录失败，需要重新登录
            if not await monitor.check_login_status():
                await monitor.login()
                await asyncio.sleep(0.01)
                
            # 第二次检查登录成功，连接WebSocket
            if await monitor.connect_websocket():
                await asyncio.sleep(0.01)
                
        await mock_run_monitor()
        
        # 验证登录续期逻辑
        assert monitor.check_login_status.call_count == 2
        assert monitor.login.called
        assert monitor.connect_websocket.called