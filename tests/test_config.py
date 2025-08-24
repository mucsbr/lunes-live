import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from vps_monitor import VPSConfig, VPSMonitor

class TestVPSConfig:
    """VPS配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = VPSConfig()
        
        assert config.panel_url == ""
        assert config.server_id == ""
        assert config.server_uuid == ""
        assert config.node_host == ""
        assert config.ws_port == 8080
        assert config.username == ""
        assert config.password == ""
        assert config.check_interval == 30
        assert config.max_retries == 3
        
    def test_custom_config(self):
        """测试自定义配置"""
        config = VPSConfig(
            panel_url="https://custom.panel.com",
            server_id="custom-server",
            username="customuser",
            check_interval=60
        )
        
        assert config.panel_url == "https://custom.panel.com"
        assert config.server_id == "custom-server"
        assert config.username == "customuser"
        assert config.check_interval == 60
        
    def test_inheritance_config(self):
        """测试配置继承"""
        config = VPSConfig(
            username="newuser",
            password="newpass"
        )
        
        # 自定义值
        assert config.username == "newuser"
        assert config.password == "newpass"
        
        # 默认值保持不变
        assert config.panel_url == ""
        assert config.server_id == ""
        assert config.check_interval == 30