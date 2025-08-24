import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiohttp import ClientSession, ClientResponse
from aiohttp.web import Application, Response, json_response
from vps_monitor import VPSMonitor, VPSConfig

@pytest.fixture
def config():
    """测试配置"""
    return VPSConfig(
        panel_url="https://test.panel.com",
        server_id="test-server-id",
        server_uuid="test-server-uuid",
        node_host="test.node.com",
        ws_port=8080,
        username="testuser",
        password="testpass",
        check_interval=5,
        max_retries=2
    )

@pytest.fixture
def monitor(config):
    """监控器实例"""
    return VPSMonitor(config)

@pytest.fixture
def mock_session():
    """模拟HTTP会话"""
    with patch('aiohttp.ClientSession') as mock:
        session = Mock(spec=ClientSession)
        mock.return_value = session
        yield session

@pytest.fixture
def mock_websockets():
    """模拟WebSocket连接"""
    with patch('websockets.connect') as mock:
        ws_mock = AsyncMock()
        mock.return_value = ws_mock
        yield ws_mock

class TestVPSMonitor:
    """VPS监控器测试"""
    
    @pytest.mark.asyncio
    async def test_init(self, monitor):
        """测试初始化"""
        assert monitor.config.username == "testuser"
        assert monitor.config.panel_url == "https://test.panel.com"
        assert monitor.is_running == False
        assert monitor.session is None
        assert monitor.ws_connection is None
        
    @pytest.mark.asyncio
    async def test_get_csrf_token_success(self, monitor, mock_session):
        """测试成功获取CSRF Token"""
        # 初始化session
        monitor.session = mock_session
        
        # 模拟响应
        mock_response = Mock(spec=ClientResponse)
        mock_response.status = 204
        
        # 创建cookie mock对象
        xsrf_cookie = Mock()
        xsrf_cookie.value = 'test-xsrf-token'
        session_cookie = Mock()
        session_cookie.value = 'test-session'
        
        mock_response.cookies = {
            'XSRF-TOKEN': xsrf_cookie,
            'pterodactyl_session': session_cookie
        }
        
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        result = await monitor.get_csrf_token()
        
        assert result == True
        assert monitor.xsrf_token == 'test-xsrf-token'
        assert monitor.session_cookie == 'test-session'
        
    @pytest.mark.asyncio
    async def test_get_csrf_token_failure(self, monitor, mock_session):
        """测试获取CSRF Token失败"""
        monitor.session = mock_session
        
        mock_response = Mock(spec=ClientResponse)
        mock_response.status = 500
        
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        result = await monitor.get_csrf_token()
        
        assert result == False
        
    @pytest.mark.asyncio
    async def test_login_success(self, monitor, mock_session):
        """测试登录成功"""
        # 初始化session
        monitor.session = mock_session
        
        # 设置CSRF token
        monitor.xsrf_token = 'test-xsrf-token'
        
        # 模拟登录响应
        mock_response = Mock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'data': {
                'complete': True,
                'user': {'username': 'testuser'}
            }
        })
        
        # 创建cookie mock对象
        new_session_cookie = Mock()
        new_session_cookie.value = 'new-session'
        new_xsrf_cookie = Mock()
        new_xsrf_cookie.value = 'new-xsrf-token'
        
        mock_response.cookies = {
            'pterodactyl_session': new_session_cookie,
            'XSRF-TOKEN': new_xsrf_cookie
        }
        
        mock_session.post.return_value = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        result = await monitor.login()
        
        assert result == True
        assert monitor.session_cookie == 'new-session'
        assert monitor.xsrf_token == 'new-xsrf-token'
        
    @pytest.mark.asyncio
    async def test_login_failure(self, monitor, mock_session):
        """测试登录失败"""
        monitor.session = mock_session
        monitor.xsrf_token = 'test-xsrf-token'
        
        mock_response = Mock(spec=ClientResponse)
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={'error': 'Invalid credentials'})
        
        mock_session.post.return_value = AsyncMock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        result = await monitor.login()
        
        assert result == False
        
    @pytest.mark.asyncio
    async def test_check_login_status_logged_in(self, monitor, mock_session):
        """测试检查登录状态 - 已登录"""
        monitor.session = mock_session
        
        mock_response = Mock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='<script>window.PterodactylUser = {};</script>')
        
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        result = await monitor.check_login_status()
        
        assert result == True
        
    @pytest.mark.asyncio
    async def test_check_login_status_not_logged_in(self, monitor, mock_session):
        """测试检查登录状态 - 未登录"""
        monitor.session = mock_session
        
        mock_response = Mock(spec=ClientResponse)
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='<html><body>Redirecting to login...</body></html>')
        
        mock_session.get.return_value = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        
        result = await monitor.check_login_status()
        
        assert result == False
        
    @pytest.mark.asyncio
    async def test_connect_websocket_success(self, monitor, mock_session, mock_websockets):
        """测试WebSocket连接成功"""
        monitor.session_cookie = 'test-session'
        monitor.xsrf_token = 'test-xsrf-token'
        
        # 确保mock_websockets.connect返回一个async mock
        mock_websockets.return_value = AsyncMock()
        
        result = await monitor.connect_websocket()
        
        assert result == True
        assert monitor.ws_connection == mock_websockets.return_value
        mock_websockets.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_connect_websocket_failure(self, monitor, mock_websockets):
        """测试WebSocket连接失败"""
        mock_websockets.connect.side_effect = Exception("Connection failed")
        
        result = await monitor.connect_websocket()
        
        assert result == False
        
    @pytest.mark.asyncio
    async def test_send_command_success(self, monitor):
        """测试发送命令成功"""
        monitor.ws_connection = AsyncMock()
        
        command = {"event": "set state", "args": ["start"]}
        result = await monitor.send_command(command)
        
        assert result == True
        monitor.ws_connection.send.assert_called_once_with(json.dumps(command))
        
    @pytest.mark.asyncio
    async def test_send_command_failure(self, monitor):
        """测试发送命令失败"""
        monitor.ws_connection = AsyncMock()
        monitor.ws_connection.send.side_effect = Exception("Send failed")
        
        command = {"event": "set state", "args": ["start"]}
        result = await monitor.send_command(command)
        
        assert result == False
        
    def test_extract_sshx_link(self, monitor):
        """测试提取SSHX链接"""
        message = "🔗 Your SSHX link is: https://sshx.io/s/test123#abc456"
        result = monitor.extract_sshx_link(message)
        
        assert result == "https://sshx.io/s/test123#abc456"
        
    def test_extract_sshx_link_no_match(self, monitor):
        """测试提取SSHX链接 - 无匹配"""
        message = "Some other message without SSHX link"
        result = monitor.extract_sshx_link(message)
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_handle_status_message_offline(self, monitor):
        """测试处理状态消息 - 离线状态"""
        monitor.current_status = 'starting'
        monitor.start_server = AsyncMock()
        
        message = '{"event": "status", "args": ["offline"]}'
        await monitor.handle_websocket_message(message)
        
        assert monitor.current_status == 'offline'
        monitor.start_server.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_handle_status_message_starting(self, monitor):
        """测试处理状态消息 - 启动状态"""
        monitor.current_status = 'offline'
        
        message = '{"event": "status", "args": ["starting"]}'
        await monitor.handle_websocket_message(message)
        
        assert monitor.current_status == 'starting'
        
    @pytest.mark.asyncio
    async def test_handle_console_output_with_sshx(self, monitor):
        """测试处理控制台输出 - 包含SSHX链接"""
        monitor.sshx_link = None
        
        message = '{"event": "console output", "args": ["🔗 Your SSHX link is: https://sshx.io/s/new123#xyz789"]}'
        await monitor.handle_websocket_message(message)
        
        assert monitor.sshx_link == "https://sshx.io/s/new123#xyz789"
        
    @pytest.mark.asyncio
    async def test_handle_console_output_without_sshx(self, monitor):
        """测试处理控制台输出 - 不包含SSHX链接"""
        monitor.sshx_link = None
        
        message = '{"event": "console output", "args": ["Some other console message"]}'
        await monitor.handle_websocket_message(message)
        
        assert monitor.sshx_link is None
        
    @pytest.mark.asyncio
    async def test_start_server(self, monitor):
        """测试启动服务器"""
        monitor.send_command = AsyncMock(return_value=True)
        
        result = await monitor.start_server()
        
        assert result == True
        monitor.send_command.assert_called_once_with({"event": "set state", "args": ["start"]})