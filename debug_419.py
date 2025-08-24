#!/usr/bin/env python3
"""
专门用于调试419错误的测试脚本
"""

import asyncio
import logging
import json
from vps_monitor import VPSMonitor, VPSConfig

# 设置日志级别为DEBUG以查看详细信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def debug_419_error():
    """调试419错误"""
    config = VPSConfig()
    
    async with VPSMonitor(config) as monitor:
        print("=" * 80)
        print("🔍 调试419 CSRF Token Mismatch错误")
        print("=" * 80)
        
        # 步骤1: 获取CSRF Token
        print("\n📋 步骤1: 获取CSRF Token")
        csrf_result = await monitor.get_csrf_token()
        
        if not csrf_result:
            print("❌ CSRF Token获取失败")
            return False
        
        print(f"✅ CSRF Token获取成功")
        print(f"   XSRF-TOKEN: {monitor.xsrf_token}")
        print(f"   Session: {monitor.session_cookie}")
        
        # 步骤2: 尝试登录
        print("\n📋 步骤2: 尝试登录")
        login_result = await monitor.login()
        
        if login_result:
            print("✅ 登录成功")
            return True
        else:
            print("❌ 登录失败")
            return False

async def manual_cookie_test():
    """手动测试cookie处理"""
    config = VPSConfig()
    
    async with VPSMonitor(config) as monitor:
        print("=" * 80)
        print("🔍 手动测试Cookie处理")
        print("=" * 80)
        
        # 手动测试cookie解码
        if monitor.xsrf_token:
            print(f"\n📋 CSRF Token分析:")
            print(f"   原始Token: {monitor.xsrf_token}")
            print(f"   Token长度: {len(monitor.xsrf_token)}")
            
            # 检查是否需要URL解码
            import urllib.parse
            try:
                decoded = urllib.parse.unquote(monitor.xsrf_token)
                print(f"   URL解码后: {decoded}")
                print(f"   解码后长度: {len(decoded)}")
            except Exception as e:
                print(f"   URL解码失败: {e}")
        
        if monitor.session_cookie:
            print(f"\n📋 Session Cookie分析:")
            print(f"   原始Session: {monitor.session_cookie}")
            print(f"   Session长度: {len(monitor.session_cookie)}")

async def compare_with_browser():
    """与浏览器请求对比"""
    print("=" * 80)
    print("🔍 与浏览器请求对比")
    print("=" * 80)
    
    print("\n📋 浏览器请求分析 (基于你提供的信息):")
    print("1. 初始请求:")
    print("   GET /server/{server_id}")
    print("   返回: Set-Cookie: XSRF-TOKEN=xxx; pterodactyl_session=xxx")
    
    print("\n2. CSRF Token请求:")
    print("   GET /sanctum/csrf-cookie")
    print("   Cookie: XSRF-TOKEN=xxx; pterodactyl_session=xxx")
    print("   返回: 更新的Set-Cookie")
    
    print("\n3. 登录请求:")
    print("   POST /auth/login")
    print("   Cookie: XSRF-TOKEN=xxx; pterodactyl_session=xxx")
    print("   X-XSRF-TOKEN: xxx")
    print("   返回: 200 或 419")
    
    print("\n🔍 可能的问题点:")
    print("1. CSRF Token在请求头和Cookie中的值不一致")
    print("2. CSRF Token需要URL编码/解码")
    print("3. Cookie格式不正确")
    print("4. 请求头大小写问题")

async def main():
    """主函数"""
    print("🚀 开始调试419错误...")
    
    # 运行调试
    result1 = await debug_419_error()
    
    # 手动分析
    await manual_cookie_test()
    
    # 对比分析
    await compare_with_browser()
    
    print("\n" + "=" * 80)
    print(f"📊 调试结果: {'成功' if result1 else '失败'}")
    print("=" * 80)
    
    print("\n💡 建议:")
    print("1. 检查日志中的请求和响应详情")
    print("2. 对比发送的CSRF Token和Cookie值")
    print("3. 确认X-XSRF-TOKEN头的大小写")
    print("4. 验证Cookie格式是否正确")

if __name__ == "__main__":
    asyncio.run(main())