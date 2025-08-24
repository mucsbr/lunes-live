#!/usr/bin/env python3
"""
CSRF Token分析工具
"""

import urllib.parse
import base64
import json

def analyze_csrf_token(token):
    """分析CSRF Token"""
    print("=" * 60)
    print("🔍 CSRF Token分析")
    print("=" * 60)
    
    if not token:
        print("❌ Token为空")
        return
    
    print(f"📋 原始Token: {token}")
    print(f"📏 长度: {len(token)}")
    
    # 检查是否是Base64编码
    print("\n🔍 Base64检查:")
    try:
        # 尝试Base64解码
        decoded_bytes = base64.b64decode(token + '=' * (-len(token) % 4))
        decoded_str = decoded_bytes.decode('utf-8')
        print(f"✅ Base64解码成功: {decoded_str}")
        
        # 尝试解析为JSON
        try:
            json_data = json.loads(decoded_str)
            print(f"✅ JSON解析成功: {json_data}")
        except:
            print("❌ 不是有效的JSON")
            
    except Exception as e:
        print(f"❌ Base64解码失败: {e}")
    
    # 检查URL编码
    print("\n🔍 URL编码检查:")
    try:
        url_decoded = urllib.parse.unquote(token)
        if url_decoded != token:
            print(f"✅ URL解码成功: {url_decoded}")
            print(f"📏 解码后长度: {len(url_decoded)}")
            
            # 递归检查解码后的内容
            analyze_csrf_token(url_decoded)
        else:
            print("ℹ️ 无URL编码")
    except Exception as e:
        print(f"❌ URL解码失败: {e}")
    
    # 检查特殊字符
    print("\n🔍 特殊字符检查:")
    special_chars = ['%', '=', '+', '/', '.']
    for char in special_chars:
        count = token.count(char)
        if count > 0:
            print(f"   '{char}': {count}次")

def analyze_cookie_format(cookie_string):
    """分析Cookie格式"""
    print("=" * 60)
    print("🔍 Cookie格式分析")
    print("=" * 60)
    
    if not cookie_string:
        print("❌ Cookie为空")
        return
    
    print(f"📋 原始Cookie: {cookie_string}")
    print(f"📏 长度: {len(cookie_string)}")
    
    # 解析Cookie
    print("\n🔍 Cookie解析:")
    try:
        # 分割Cookie
        cookie_parts = cookie_string.split(';')
        print(f"📦 Cookie部分数量: {len(cookie_parts)}")
        
        for i, part in enumerate(cookie_parts):
            part = part.strip()
            print(f"   Part {i+1}: {part}")
            
            # 检查是否是键值对
            if '=' in part:
                key, value = part.split('=', 1)
                print(f"     Key: {key}")
                print(f"     Value: {value}")
                
                # 分析XSRF-TOKEN
                if key.strip() == 'XSRF-TOKEN':
                    print("     🎯 这是XSRF-TOKEN!")
                    analyze_csrf_token(value)
                    
    except Exception as e:
        print(f"❌ Cookie解析失败: {e}")

def generate_request_headers(csrf_token, session_cookie):
    """生成请求头"""
    print("=" * 60)
    print("🔍 请求头生成")
    print("=" * 60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": csrf_token,
        "Origin": "https://your-panel.com",
        "Referer": "https://your-panel.com/auth/login"
    }
    
    if session_cookie:
        headers["Cookie"] = f"XSRF-TOKEN={csrf_token}; pterodactyl_session={session_cookie}"
    
    print("📋 生成的请求头:")
    for key, value in headers.items():
        print(f"   {key}: {value}")
    
    return headers

def test_different_formats(csrf_token, session_cookie):
    """测试不同的格式组合"""
    print("=" * 60)
    print("🔍 测试不同格式")
    print("=" * 60)
    
    formats = [
        # 标准格式
        f"XSRF-TOKEN={csrf_token}; pterodactyl_session={session_cookie}",
        # 交换顺序
        f"pterodactyl_session={session_cookie}; XSRF-TOKEN={csrf_token}",
        # URL编码
        f"XSRF-TOKEN={urllib.parse.quote(csrf_token)}; pterodactyl_session={session_cookie}",
        # 无分号
        f"XSRF-TOKEN={csrf_token}, pterodactyl_session={session_cookie}",
    ]
    
    for i, cookie_format in enumerate(formats, 1):
        print(f"\n📋 格式 {i}: {cookie_format}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-XSRF-TOKEN": csrf_token,
            "Cookie": cookie_format
        }
        
        print("   请求头:")
        for key, value in headers.items():
            print(f"     {key}: {value}")

# 测试数据
if __name__ == "__main__":
    # 模拟从日志中获取的数据
    test_csrf_token = "eyJpdiI6Ilp1MWd2Q0RwcTh2WCs5Z09lbXdsZUE9PSIsInZhbHVlIjoiVW1kVTJmVlJBZ01XdWRtNElCZkk5NTArdldTd3A5ZnNGZEwxS2phQW1SNUM1ZTJoL1NiRWRneFU2WXQvNGQxTGRTK1dUYkVPSE1GQVFkOXFvUnBOWnkxZklRMVRYaHpBSEZrb0xnL3VxK2dWcDlaYnFFTTJ3RStVeUZqUHcwTkYiLCJtYWMiOiI3NjM0ZjE2NGQwYjE5MjYyNjEyNzdkNmEyMzMyZTU3MWNiM2MyYjhhNGYzZmFjZTQ1ZTQ3MGEwYjdjZDM4NWUzIiwidGFnIjoiIn0"
    test_session_cookie = "eyJpdiI6ImpjSHpoREJUb3FHdDRPaksvQlNQUXc9PSIsInZhbHVlIjoiNDdZMWhMTHdIQyt1MjE0TFZ2TE1kSW95V0dnYllySFBzOGpSS2VTYWF3Rzc3dHZyanB6LzN5TFVQMC9MS0h5TjF4WmxHNXlYMDFKL1g5OUxISmpMQ3V4dDdUWTVtbTRzbjhQT1RYZ1g2YWJVa1Y2UEUzVmcwRzJrNkNsNEVFN1QiLCJtYWMiOiIxOTE4YjM0ZGZjZTAxMDFlYjk1ZTkzYWFhMGY5Njc4MWIwODNjNzM0ZjZkMzhkMzgxNzc4MWNjYzk2ZjYzYzk3IiwidGFnIjoiIn0"
    
    print("🚀 开始CSRF Token分析...")
    
    # 分析Token
    analyze_csrf_token(test_csrf_token)
    
    # 分析Cookie
    analyze_cookie_format(f"XSRF-TOKEN={test_csrf_token}; pterodactyl_session={test_session_cookie}")
    
    # 生成请求头
    generate_request_headers(test_csrf_token, test_session_cookie)
    
    # 测试不同格式
    test_different_formats(test_csrf_token, test_session_cookie)
    
    print("\n" + "=" * 60)
    print("✅ 分析完成")
    print("=" * 60)