import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from vps_monitor import VPSMonitor, VPSConfig

class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def monitor(self):
        """测试监控器"""
        config = VPSConfig(
            panel_url="https://test.panel.com",
            server_uuid="test-server-uuid",
            node_host="test.node.com",
            ws_port=8080,
            username="testuser",
            password="testpass",
            check_interval=1
        )
        return VPSMonitor(config)
    
    @pytest.mark.asyncio
    async def test_full_monitoring_cycle(self, monitor):
        """测试完整监控周期"""
        # 模拟完整的监控流程
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # 1. 获取CSRF token
            csrf_response = Mock()
            csrf_response.status = 204
            csrf_response.cookies = {
                'XSRF-TOKEN': Mock(value='test-xsrf-token'),
                'pterodactyl_session': Mock(value='test-session')
            }
            mock_session.get.return_value.__aenter__.return_value = csrf_response
            
            # 2. 登录
            login_response = Mock()
            login_response.status = 200
            login_response.json = AsyncMock(return_value={
                'data': {
                    'complete': True,
                    'user': {'username': 'testuser'}
                }
            })
            login_response.cookies = {
                'pterodactyl_session': Mock(value='auth-session'),
                'XSRF-TOKEN': Mock(value='auth-xsrf-token')
            }
            mock_session.post.return_value.__aenter__.return_value = login_response
            
            # 3. 检查登录状态
            status_response = Mock()
            status_response.status = 200
            status_response.text = AsyncMock(return_value='<script>window.PterodactylUser = {};</script>')
            mock_session.get.return_value.__aenter__.return_value = status_response
            
            # 4. WebSocket连接
            with patch('websockets.connect') as mock_connect:
                mock_ws = AsyncMock()
                mock_connect.return_value = mock_ws
                
                # 模拟WebSocket消息
                mock_ws.__aiter__.return_value = iter([
                    '{"event": "status", "args": ["starting"]}',
                    '{"event": "status", "args": ["offline"]}',
                    '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/test123#abc456"]}'
                ])
                
                # 执行监控
                await monitor.get_csrf_token()
                login_result = await monitor.login()
                status_result = await monitor.check_login_status()
                ws_result = await monitor.connect_websocket()
                
                # 处理WebSocket消息
                message_count = 0
                async for message in mock_ws:
                    await monitor.handle_websocket_message(message)
                    message_count += 1
                    if message_count >= 3:
                        break
                
                # 验证完整流程
                assert login_result == True
                assert status_result == True
                assert ws_result == True
                assert monitor.current_status == 'offline'
                assert monitor.sshx_link == "https://sshx.io/s/test123#abc456"
                
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, monitor):
        """测试错误处理和恢复"""
        # 模拟各种错误情况
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # 1. CSRF token失败
            csrf_response = Mock()
            csrf_response.status = 500
            mock_session.get.return_value.__aenter__.return_value = csrf_response
            
            csrf_result = await monitor.get_csrf_token()
            assert csrf_result == False
            
            # 2. 网络错误
            mock_session.get.side_effect = Exception("Network error")
            csrf_result = await monitor.get_csrf_token()
            assert csrf_result == False
            
            # 3. 恢复 - 成功获取CSRF token
            mock_session.get.side_effect = None
            csrf_response.status = 204
            csrf_response.cookies = {
                'XSRF-TOKEN': Mock(value='recovery-xsrf-token'),
                'pterodactyl_session': Mock(value='recovery-session')
            }
            
            csrf_result = await monitor.get_csrf_token()
            assert csrf_result == True
            assert monitor.xsrf_token == 'recovery-xsrf-token'
            
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, monitor):
        """测试并发操作"""
        # 模拟并发WebSocket消息处理
        monitor.send_command = AsyncMock()
        
        # 并发消息
        messages = [
            '{"event": "status", "args": ["offline"]}',
            '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/concurrent1#abc456"]}',
            '{"event": "status", "args": ["starting"]}',
            '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/concurrent2#xyz789"]}'
        ]
        
        # 并发处理消息
        tasks = [monitor.handle_websocket_message(msg) for msg in messages]
        await asyncio.gather(*tasks)
        
        # 验证结果
        assert monitor.current_status == 'starting'
        assert monitor.sshx_link is not None
        assert monitor.send_command.called
        
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, monitor):
        """测试资源清理"""
        # 模拟资源分配
        monitor.session = Mock()
        monitor.ws_connection = Mock()
        
        # 测试清理
        await monitor.close()
        
        # 验证资源被清理
        monitor.session.close.assert_called_once()
        monitor.ws_connection.close.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_long_running_stability(self, monitor):
        """测试长时间运行稳定性"""
        # 模拟长时间运行的监控
        monitor.is_running = True
        message_count = 0
        
        async def mock_monitor_websocket():
            nonlocal message_count
            while monitor.is_running and message_count < 10:
                # 模拟定期消息
                await asyncio.sleep(0.01)
                message_count += 1
                
                if message_count % 3 == 0:
                    await monitor.handle_websocket_message('{"event": "status", "args": ["starting"]}')
                elif message_count % 3 == 1:
                    await monitor.handle_websocket_message('{"event": "status", "args": ["offline"]}')
                else:
                    await monitor.handle_websocket_message('{"event": "console output", "args": ["Regular log message"]}')
                    
        # 运行监控
        task = asyncio.create_task(mock_monitor_websocket())
        
        # 让监控运行一段时间
        await asyncio.sleep(0.1)
        
        # 停止监控
        monitor.is_running = False
        await task
        
        # 验证稳定性
        assert message_count > 0
        assert monitor.current_status in ['starting', 'offline']
        
    @pytest.mark.asyncio
    async def test_configuration_validation(self, monitor):
        """测试配置验证"""
        # 测试各种配置组合
        test_configs = [
            # 默认配置
            VPSConfig(),
            # 自定义配置
            VPSConfig(
                panel_url="https://custom.panel.com",
                check_interval=60
            ),
            # 最小配置
            VPSConfig(username="minuser", password="minpass")
        ]
        
        for config in test_configs:
            test_monitor = VPSMonitor(config)
            assert test_monitor.config is not None
            assert test_monitor.config.username is not None
            assert test_monitor.config.password is not None
            assert test_monitor.config.check_interval > 0