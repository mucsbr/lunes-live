import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from vps_monitor import VPSMonitor, VPSConfig

class TestWebSocket:
    """WebSocket连接和消息处理测试"""
    
    @pytest.fixture
    def monitor(self):
        """测试监控器"""
        config = VPSConfig(
            panel_url="https://test.panel.com",
            server_uuid="test-server-uuid",
            node_host="test.node.com",
            ws_port=8080
        )
        return VPSMonitor(config)
    
    @pytest.mark.asyncio
    async def test_websocket_connection_with_cookies(self, monitor):
        """测试WebSocket连接 - 包含Cookie"""
        monitor.session_cookie = 'test-session'
        monitor.xsrf_token = 'test-xsrf-token'
        
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value = mock_ws
            
            result = await monitor.connect_websocket()
            
            assert result == True
            mock_connect.assert_called_once()
            
            # 验证连接参数
            call_args = mock_connect.call_args
            expected_url = "wss://test.node.com:8080/api/servers/test-server-uuid/ws"
            assert call_args[0][0] == expected_url
            
            # 验证headers包含cookie
            headers = call_args[1]['extra_headers']
            assert 'Cookie' in headers
            assert 'pterodactyl_session=test-session' in headers['Cookie']
            assert 'XSRF-TOKEN=test-xsrf-token' in headers['Cookie']
            
    @pytest.mark.asyncio
    async def test_websocket_connection_without_cookies(self, monitor):
        """测试WebSocket连接 - 无Cookie"""
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value = mock_ws
            
            result = await monitor.connect_websocket()
            
            assert result == True
            
            # 验证headers
            call_args = mock_connect.call_args
            headers = call_args[1]['extra_headers']
            assert 'Cookie' in headers
            assert 'pterodactyl_session=None' in headers['Cookie']
            
    @pytest.mark.asyncio
    async def test_websocket_connection_failure(self, monitor):
        """测试WebSocket连接失败"""
        monitor.session_cookie = 'test-session'
        
        with patch('websockets.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            result = await monitor.connect_websocket()
            
            assert result == False
            
    @pytest.mark.asyncio
    async def test_websocket_monitoring(self, monitor):
        """测试WebSocket监控"""
        monitor.ws_connection = AsyncMock()
        
        # 模拟WebSocket消息流
        messages = [
            '{"event": "status", "args": ["starting"]}',
            '{"event": "status", "args": ["offline"]}',
            '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/test123#abc456"]}'
        ]
        
        monitor.ws_connection.__aiter__.return_value = iter(messages)
        monitor.handle_websocket_message = AsyncMock()
        
        # 模拟监控运行一段时间后停止
        async def mock_monitor():
            await asyncio.sleep(0.1)  # 短暂运行
            monitor.is_running = False
            
        monitor.is_running = True
        await mock_monitor()
        
        # 验证消息处理
        assert monitor.handle_websocket_message.call_count == 3
        
    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, monitor):
        """测试WebSocket重连机制"""
        monitor.connect_websocket = AsyncMock(side_effect=[False, True])
        monitor.check_login_status = AsyncMock(return_value=True)
        
        messages_processed = []
        
        async def mock_monitor_websocket():
            messages_processed.append("monitor_started")
            await asyncio.sleep(0.1)
            raise Exception("Connection closed")
            
        monitor.monitor_websocket = mock_monitor_websocket
        monitor.is_running = True
        
        # 模拟监控循环
        async def mock_run_monitor():
            for _ in range(2):  # 两次尝试
                if not await monitor.connect_websocket():
                    await asyncio.sleep(0.01)
                else:
                    await monitor.monitor_websocket()
                    
        await mock_run_monitor()
        
        # 验证重连逻辑
        assert monitor.connect_websocket.call_count == 2
        assert len(messages_processed) == 1
        
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self, monitor):
        """测试WebSocket消息处理"""
        test_cases = [
            # 状态消息
            {
                'message': '{"event": "status", "args": ["starting"]}',
                'expected_status': 'starting',
                'expected_action': 'status_change'
            },
            {
                'message': '{"event": "status", "args": ["offline"]}',
                'expected_status': 'offline',
                'expected_action': 'restart_trigger'
            },
            # 控制台输出消息
            {
                'message': '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/test123#abc456"]}',
                'expected_status': None,
                'expected_action': 'sshx_extract'
            },
            # 其他消息
            {
                'message': '{"event": "install output", "args": ["Installing..."]}',
                'expected_status': None,
                'expected_action': 'ignored'
            }
        ]
        
        for test_case in test_cases:
            monitor.current_status = None
            monitor.sshx_link = None
            monitor.start_server = AsyncMock()
            
            await monitor.handle_websocket_message(test_case['message'])
            
            if test_case['expected_status']:
                assert monitor.current_status == test_case['expected_status']
                
            if test_case['expected_action'] == 'restart_trigger':
                assert monitor.start_server.called
            elif test_case['expected_action'] == 'sshx_extract':
                assert monitor.sshx_link == "https://sshx.io/s/test123#abc456"
                
    @pytest.mark.asyncio
    async def test_websocket_invalid_json_message(self, monitor):
        """测试无效JSON消息处理"""
        invalid_messages = [
            'invalid json string',
            '{"event": "status", "args": ["starting"]',  # 不完整的JSON
            '{"event": "status"}',  # 缺少args字段
            'null',
            ''
        ]
        
        for invalid_message in invalid_messages:
            # 应该不抛出异常
            await monitor.handle_websocket_message(invalid_message)
            
    @pytest.mark.asyncio
    async def test_websocket_connection_headers(self, monitor):
        """测试WebSocket连接头信息"""
        monitor.session_cookie = 'test-session'
        monitor.xsrf_token = 'test-xsrf-token'
        
        with patch('websockets.connect') as mock_connect:
            mock_ws = AsyncMock()
            mock_connect.return_value = mock_ws
            
            await monitor.connect_websocket()
            
            # 验证headers
            call_args = mock_connect.call_args
            headers = call_args[1]['extra_headers']
            
            assert headers['User-Agent'] == 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            assert headers['Origin'] == 'https://test.panel.com'
            assert 'pterodactyl_session=test-session' in headers['Cookie']
            assert 'XSRF-TOKEN=test-xsrf-token' in headers['Cookie']