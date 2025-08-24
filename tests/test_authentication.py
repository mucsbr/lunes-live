import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from vps_monitor import VPSMonitor, VPSConfig

class TestAuthentication:
    """认证流程测试"""
    
    @pytest.fixture
    def monitor(self):
        """测试监控器"""
        config = VPSConfig(
            panel_url="https://test.panel.com",
            username="testuser",
            password="testpass"
        )
        return VPSMonitor(config)
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, monitor):
        """测试完整认证流程"""
        # 模拟获取CSRF token
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # CSRF token响应
            csrf_response = Mock()
            csrf_response.status = 204
            csrf_response.cookies = {
                'XSRF-TOKEN': Mock(value='test-xsrf-token'),
                'pterodactyl_session': Mock(value='test-session')
            }
            mock_session.get.return_value.__aenter__.return_value = csrf_response
            
            # 登录响应
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
            
            # 状态检查响应
            status_response = Mock()
            status_response.status = 200
            status_response.text = AsyncMock(return_value='<script>window.PterodactylUser = {};</script>')
            mock_session.get.return_value.__aenter__.return_value = status_response
            
            # 执行完整流程
            await monitor.get_csrf_token()
            login_result = await monitor.login()
            status_result = await monitor.check_login_status()
            
            # 验证结果
            assert login_result == True
            assert status_result == True
            assert monitor.session_cookie == 'auth-session'
            assert monitor.xsrf_token == 'auth-xsrf-token'
            
    @pytest.mark.asyncio
    async def test_auth_flow_with_csrf_failure(self, monitor):
        """测试认证流程 - CSRF获取失败"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # CSRF token失败响应
            csrf_response = Mock()
            csrf_response.status = 500
            mock_session.get.return_value.__aenter__.return_value = csrf_response
            
            # 尝试获取CSRF token
            csrf_result = await monitor.get_csrf_token()
            
            assert csrf_result == False
            assert monitor.xsrf_token is None
            
    @pytest.mark.asyncio
    async def test_auth_flow_with_login_failure(self, monitor):
        """测试认证流程 - 登录失败"""
        # 先设置CSRF token
        monitor.xsrf_token = 'test-xsrf-token'
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # 登录失败响应
            login_response = Mock()
            login_response.status = 401
            login_response.json = AsyncMock(return_value={'error': 'Invalid credentials'})
            mock_session.post.return_value.__aenter__.return_value = login_response
            
            # 尝试登录
            login_result = await monitor.login()
            
            assert login_result == False
            
    @pytest.mark.asyncio
    async def test_auth_flow_with_session_expiry(self, monitor):
        """测试认证流程 - 会话过期"""
        # 设置初始认证状态
        monitor.session_cookie = 'expired-session'
        monitor.xsrf_token = 'expired-xsrf-token'
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # 状态检查响应 - 会话过期（重定向到登录页）
            status_response = Mock()
            status_response.status = 200
            status_response.text = AsyncMock(return_value='<html><body>Redirecting to login...</body></html>')
            mock_session.get.return_value.__aenter__.return_value = status_response
            
            # 检查状态
            status_result = await monitor.check_login_status()
            
            assert status_result == False
            
    @pytest.mark.asyncio
    async def test_auth_flow_with_network_error(self, monitor):
        """测试认证流程 - 网络错误"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # 模拟网络错误
            mock_session.get.side_effect = Exception("Network error")
            
            # 尝试获取CSRF token
            csrf_result = await monitor.get_csrf_token()
            
            assert csrf_result == False
            
    @pytest.mark.asyncio
    async def test_auth_flow_with_invalid_json_response(self, monitor):
        """测试认证流程 - 无效JSON响应"""
        monitor.xsrf_token = 'test-xsrf-token'
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # 登录响应 - 无效JSON
            login_response = Mock()
            login_response.status = 200
            login_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
            mock_session.post.return_value.__aenter__.return_value = login_response
            
            # 尝试登录
            login_result = await monitor.login()
            
            assert login_result == False