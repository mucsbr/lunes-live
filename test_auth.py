#!/usr/bin/env python3
"""
测试认证流程的脚本
"""

import asyncio
import logging
from vps_monitor import VPSMonitor, VPSConfig

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auth_test.log')
    ]
)

async def test_authentication():
    """测试认证流程"""
    config = VPSConfig()
    
    async with VPSMonitor(config) as monitor:
        print("=== 测试认证流程 ===")
        
        # 1. 测试获取CSRF Token
        print("\n1. 获取CSRF Token...")
        csrf_result = await monitor.get_csrf_token()
        print(f"CSRF Token获取结果: {csrf_result}")
        if csrf_result:
            print(f"XSRF-TOKEN: {monitor.xsrf_token}")
            print(f"Session Cookie: {monitor.session_cookie}")
        
        # 2. 测试登录
        print("\n2. 登录...")
        login_result = await monitor.login()
        print(f"登录结果: {login_result}")
        if login_result:
            print(f"登录后的XSRF-TOKEN: {monitor.xsrf_token}")
            print(f"登录后的Session Cookie: {monitor.session_cookie}")
        
        # 3. 测试检查登录状态
        print("\n3. 检查登录状态...")
        status_result = await monitor.check_login_status()
        print(f"登录状态检查结果: {status_result}")
        
        # 4. 测试WebSocket连接
        print("\n4. 连接WebSocket...")
        ws_result = await monitor.connect_websocket()
        print(f"WebSocket连接结果: {ws_result}")
        
        print("\n=== 测试完成 ===")
        
        return csrf_result and login_result and status_result

if __name__ == "__main__":
    result = asyncio.run(test_authentication())
    print(f"\n总体测试结果: {'成功' if result else '失败'}")