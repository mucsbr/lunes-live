#!/usr/bin/env python3
"""
WebSocket实时监控脚本
监控VPS状态变化和服务器消息
"""

import asyncio
import logging
import json
import time
from vps_monitor import VPSMonitor, VPSConfig

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def monitor_websocket_messages():
    """监控WebSocket消息"""
    config = VPSConfig()
    
    async with VPSMonitor(config) as monitor:
        print("🚀 开始WebSocket实时监控...")
        
        # 1. 登录
        if not await monitor.login():
            print("❌ 登录失败")
            return False
        
        # 2. 连接WebSocket
        if not await monitor.connect_websocket():
            print("❌ WebSocket连接失败")
            return False
        
        print("✅ WebSocket连接和认证成功")
        print("📡 开始监控消息...")
        print("=" * 60)
        
        # 3. 监控消息
        try:
            message_count = 0
            async for message in monitor.ws_connection:
                message_count += 1
                print(f"[{message_count}] 收到消息: {message}")
                
                # 解析消息
                try:
                    data = json.loads(message)
                    event = data.get('event')
                    args = data.get('args', [])
                    
                    print(f"   事件: {event}")
                    print(f"   参数: {args}")
                    
                    # 处理特定事件
                    if event == 'auth success':
                        print("   ✅ 认证成功！")
                    elif event == 'status':
                        print(f"   📊 状态变化: {args[0] if args else 'N/A'}")
                    elif event == 'console output':
                        console_msg = args[0][:100] if args else 'N/A'
                        print(f"   📝 控制台输出: {console_msg}...")
                        
                        # 检查SSHX链接
                        if 'Link:' in console_msg:
                            print("   🔗 发现SSHX链接！")
                    elif event == 'send logs':
                        print("   📋 请求发送日志")
                    elif event == 'send stats':
                        print("   📈 请求发送统计")
                    
                    print("-" * 40)
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ 解析JSON失败: {e}")
                except Exception as e:
                    print(f"   ❌ 处理消息失败: {e}")
                    
        except Exception as e:
            print(f"❌ 监控异常: {e}")
        
        return True

async def main():
    """主函数"""
    print("🔍 WebSocket实时监控工具")
    print("按 Ctrl+C 停止监控")
    print("=" * 60)
    
    try:
        await monitor_websocket_messages()
    except KeyboardInterrupt:
        print("\n🛑 用户停止监控")
    except Exception as e:
        print(f"❌ 程序异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())