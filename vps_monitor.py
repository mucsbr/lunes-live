#!/usr/bin/env python3
"""
VPS监控和自动拉起系统
监控Pterodactyl面板中的VPS状态，自动拉起关闭的机器
"""

import asyncio
import json
import logging
import os
import re
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse, unquote

import aiohttp
import websockets
import requests
from aiohttp import ClientSession, ClientResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vps_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VPSConfig:
    """VPS配置"""
    panel_url: str = os.getenv('PANEL_URL', "")
    server_id: str = os.getenv('SERVER_ID', "")
    server_uuid: str = os.getenv('SERVER_UUID', "")
    node_host: str = os.getenv('NODE_HOST', "")
    ws_port: int = int(os.getenv('WS_PORT', "8080"))
    username: str = os.getenv('USERNAME', "")
    password: str = os.getenv('PASSWORD', "")
    check_interval: int = int(os.getenv('CHECK_INTERVAL', "30"))  # 检查间隔（秒）
    max_retries: int = int(os.getenv('MAX_RETRIES', "3"))  # 最大重试次数
    dingtalk_webhook_url: str = os.getenv('DINGTALK_WEBHOOK_URL', "")

class VPSMonitor:
    """VPS监控器"""
    
    def __init__(self, config: VPSConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.csrf_token: Optional[str] = None
        self.session_cookie: Optional[str] = None
        self.xsrf_token: Optional[str] = None
        self.is_running = False
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self.current_status: Optional[str] = None
        self.sshx_link: Optional[str] = None
        self.dingtalk_webhook_url = config.dingtalk_webhook_url
        
    async def __aenter__(self):
        await self.start_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start_session(self):
        """启动HTTP会话"""
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = ClientSession(connector=connector)
        
    async def close(self):
        """关闭连接"""
        if self.ws_connection:
            await self.ws_connection.close()
        if self.session:
            await self.session.close()
            
    async def get_csrf_token(self) -> bool:
        """获取CSRF Token"""
        try:
            # 第一步：访问服务器页面获取初始cookie
            url1 = f"{self.config.panel_url}/server/{self.config.server_id}"
            headers1 = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            logger.info(f"=== 第一步：获取初始cookie ===")
            logger.info(f"请求URL: {url1}")
            logger.info(f"请求头: {headers1}")
            
            async with self.session.get(url1, headers=headers1) as response:
                logger.info(f"响应状态: {response.status}")
                logger.info(f"响应头: {dict(response.headers)}")
                
                # 获取响应cookies
                response_cookies = {}
                for cookie_name, cookie in response.cookies.items():
                    response_cookies[cookie_name] = cookie.value
                logger.info(f"响应Cookie: {response_cookies}")
                
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"响应内容长度: {len(content)}")
                    if 'window.PterodactylUser' in content:
                        logger.info("页面包含window.PterodactylUser")
                    else:
                        logger.info("页面不包含window.PterodactylUser")
                    
                    # 获取初始cookies
                    cookies = response.cookies
                    if 'XSRF-TOKEN' in cookies and 'pterodactyl_session' in cookies:
                        self.xsrf_token = cookies['XSRF-TOKEN'].value
                        self.session_cookie = cookies['pterodactyl_session'].value
                        logger.info(f"成功获取初始CSRF Token: {self.xsrf_token}")
                        logger.info(f"成功获取初始Session: {self.session_cookie}")
                    else:
                        logger.error(f"未找到初始cookie，可用cookie: {list(cookies.keys())}")
                        return False
                else:
                    logger.error(f"获取初始cookie失败: {response.status}")
                    return False
            
            # 第二步：访问sanctum/csrf-cookie更新cookie
            url2 = f"{self.config.panel_url}/sanctum/csrf-cookie"
            headers2 = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            # 如果有cookie，添加到请求头 - 使用URL解码的token
            if self.session_cookie and self.xsrf_token:
                decoded_xsrf_token = unquote(self.xsrf_token)
                decoded_session = unquote(self.session_cookie)
                headers2["Cookie"] = f"XSRF-TOKEN={decoded_xsrf_token}; pterodactyl_session={decoded_session}"
            
            logger.info(f"=== 第二步：更新CSRF Token ===")
            logger.info(f"请求URL: {url2}")
            logger.info(f"请求头: {headers2}")
            
            async with self.session.get(url2, headers=headers2) as response:
                logger.info(f"响应状态: {response.status}")
                logger.info(f"响应头: {dict(response.headers)}")
                
                # 获取响应cookies
                response_cookies = {}
                for cookie_name, cookie in response.cookies.items():
                    response_cookies[cookie_name] = cookie.value
                logger.info(f"响应Cookie: {response_cookies}")
                
                if response.status == 204:
                    # 更新cookies
                    cookies = response.cookies
                    if 'XSRF-TOKEN' in cookies:
                        self.xsrf_token = cookies['XSRF-TOKEN'].value
                        if 'pterodactyl_session' in cookies:
                            self.session_cookie = cookies['pterodactyl_session'].value
                        logger.info(f"成功更新CSRF Token: {self.xsrf_token}")
                        logger.info(f"成功更新Session: {self.session_cookie}")
                        return True
                    else:
                        logger.error(f"未找到更新的XSRF-TOKEN cookie，可用cookie: {list(cookies.keys())}")
                        return False
                else:
                    logger.error(f"更新CSRF Token失败: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"获取CSRF Token异常: {e}")
            return False
            
    async def login(self) -> bool:
        """登录认证"""
        if not self.xsrf_token:
            if not await self.get_csrf_token():
                return False
                
        try:
            login_data = {
                "user": self.config.username,
                "password": self.config.password,
                "g-recaptcha-response": ""
            }
            
            # 构建请求头，包含cookie
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "X-Xsrf-Token": unquote(self.xsrf_token),
                "Origin": self.config.panel_url,
                "Referer": f"{self.config.panel_url}/auth/login"
            }
            
            # 添加cookie到请求头 - 使用URL解码的token
            if self.session_cookie and self.xsrf_token:
                # 确保token没有被URL编码
                decoded_xsrf_token = unquote(self.xsrf_token)
                decoded_session = unquote(self.session_cookie)
                headers["Cookie"] = f"XSRF-TOKEN={decoded_xsrf_token}; pterodactyl_session={decoded_session}"
            
            url = f"{self.config.panel_url}/auth/login"
            
            logger.info(f"=== 第三步：登录认证 ===")
            logger.info(f"请求URL: {url}")
            logger.info(f"请求数据: {login_data}")
            logger.info(f"请求头: {headers}")
            logger.info(f"当前CSRF Token: {self.xsrf_token}")
            logger.info(f"当前Session: {self.session_cookie}")
            
            async with self.session.post(url, json=login_data, headers=headers) as response:
                logger.info(f"响应状态: {response.status}")
                logger.info(f"响应头: {dict(response.headers)}")
                
                # 获取响应cookies
                response_cookies = {}
                for cookie_name, cookie in response.cookies.items():
                    response_cookies[cookie_name] = cookie.value
                logger.info(f"响应Cookie: {response_cookies}")
                
                # 读取响应内容
                response_text = await response.text()
                logger.info(f"响应内容: {response_text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(response_text)
                        logger.info(f"解析JSON成功: {data}")
                        
                        if data.get('data', {}).get('complete'):
                            # 更新cookies
                            cookies = response.cookies
                            if 'pterodactyl_session' in cookies and 'XSRF-TOKEN' in cookies:
                                self.session_cookie = cookies['pterodactyl_session'].value
                                self.xsrf_token = cookies['XSRF-TOKEN'].value
                                logger.info(f"登录成功: {data['data']['user']['username']}")
                                logger.info(f"更新后的Session: {self.session_cookie}")
                                logger.info(f"更新后的CSRF Token: {self.xsrf_token}")
                            else:
                                logger.error("登录成功但未获取到更新后的cookie")
                            return True
                        else:
                            logger.error("登录失败: complete=false")
                            return False
                    except json.JSONDecodeError as e:
                        logger.error(f"解析JSON失败: {e}")
                        logger.error(f"响应内容: {response_text}")
                        return False
                else:
                    logger.error(f"登录失败: {response.status}")
                    
                    # 如果是419错误，打印详细错误信息
                    if response.status == 419:
                        logger.error("=== 419 CSRF Token Mismatch 错误 ===")
                        logger.error("可能的原因:")
                        logger.error("1. CSRF Token已过期")
                        logger.error("2. CSRF Token格式不正确")
                        logger.error("3. Session已过期")
                        logger.error("4. Cookie传递有问题")
                        
                        # 打印发送的CSRF Token
                        logger.error(f"发送的X-XSRF-TOKEN: {headers.get('X-Xsrf-Token')}")
                        logger.error(f"发送的Cookie: {headers.get('Cookie')}")
                        
                        # 尝试解析错误响应
                        try:
                            error_data = json.loads(response_text)
                            logger.error(f"错误详情: {error_data}")
                        except:
                            logger.error("无法解析错误响应")
                        
                        logger.info("准备重新获取Token并重试...")
                        self.xsrf_token = None
                        self.session_cookie = None
                        return await self.login()  # 重试一次
                    return False
        except Exception as e:
            logger.error(f"登录异常: {e}")
            return False
            
    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 构建请求头，包含cookie
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            # 添加cookie到请求头 - 使用URL解码的token
            if self.session_cookie and self.xsrf_token:
                # 确保token没有被URL编码
                decoded_xsrf_token = unquote(self.xsrf_token)
                decoded_session = unquote(self.session_cookie)
                headers["Cookie"] = f"XSRF-TOKEN={decoded_xsrf_token}; pterodactyl_session={decoded_session}"
            
            url = f"{self.config.panel_url}/server/{self.config.server_id}"
            
            logger.info(f"=== 检查登录状态 ===")
            logger.info(f"请求URL: {url}")
            logger.info(f"请求头: {headers}")
            logger.info(f"使用的Session: {self.session_cookie}")
            logger.info(f"使用的CSRF Token: {self.xsrf_token}")
            
            async with self.session.get(url, headers=headers) as response:
                logger.info(f"响应状态: {response.status}")
                logger.info(f"响应头: {dict(response.headers)}")
                
                # 获取响应cookies
                response_cookies = {}
                for cookie_name, cookie in response.cookies.items():
                    response_cookies[cookie_name] = cookie.value
                logger.info(f"响应Cookie: {response_cookies}")
                
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"响应内容长度: {len(content)}")
                    
                    if 'window.PterodactylUser' in content:
                        logger.info("✓ 登录状态正常 - 找到window.PterodactylUser")
                        return True
                    else:
                        logger.warning("✗ 登录状态异常 - 未找到window.PterodactylUser")
                        logger.info("页面内容预览:")
                        logger.info(content[:500] + "..." if len(content) > 500 else content)
                        return False
                else:
                    logger.error(f"检查登录状态失败: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"检查登录状态异常: {e}")
            return False
            
    async def get_websocket_token(self) -> Optional[str]:
        """获取WebSocket认证用的JWT token"""
        try:
            # 构建请求头，包含cookie
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # 添加cookie到请求头 - 使用URL解码的token
            if self.session_cookie and self.xsrf_token:
                decoded_xsrf_token = unquote(self.xsrf_token)
                decoded_session = unquote(self.session_cookie)
                headers["Cookie"] = f"XSRF-TOKEN={decoded_xsrf_token}; pterodactyl_session={decoded_session}"
            
            # 获取WebSocket token的API端点
            url = f"{self.config.panel_url}/api/client/servers/{self.config.server_uuid}/websocket"
            
            logger.info(f"=== 获取WebSocket Token ===")
            logger.info(f"请求URL: {url}")
            
            async with self.session.get(url, headers=headers) as response:
                logger.info(f"响应状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"获取WebSocket Token成功: {data}")
                    
                    # 从响应中提取token
                    if 'data' in data and 'token' in data['data']:
                        jwt_token = data['data']['token']
                        logger.info(f"JWT Token: {jwt_token}")
                        return jwt_token
                    else:
                        logger.error(f"响应格式错误: {data}")
                        return None
                else:
                    logger.error(f"获取WebSocket Token失败: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取WebSocket Token异常: {e}")
            return None
    
    async def connect_websocket(self) -> bool:
        """连接WebSocket"""
        try:
            # 首先获取JWT token
            jwt_token = await self.get_websocket_token()
            if not jwt_token:
                logger.error("无法获取JWT token，WebSocket连接失败")
                return False
            
            # 构建WebSocket URL
            ws_url = f"wss://{self.config.node_host}:{self.config.ws_port}/api/servers/{self.config.server_uuid}/ws"
            
            # 准备cookies
            cookies = {
                'pterodactyl_session': self.session_cookie,
                'XSRF-TOKEN': self.xsrf_token
            }
            
            # 构建cookie字符串
            cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Origin': self.config.panel_url,
                'Cookie': cookie_str
            }
            
            self.ws_connection = await websockets.connect(ws_url, extra_headers=headers)
            logger.info("WebSocket连接成功")
            
            # 发送认证命令
            auth_command = {
                "event": "auth",
                "args": [jwt_token]
            }
            
            if await self.send_command(auth_command):
                logger.info("WebSocket认证命令已发送")
                return True
            else:
                logger.error("WebSocket认证命令发送失败")
                return False
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            return False
            
    async def send_command(self, command: Dict[str, Any]) -> bool:
        """发送WebSocket命令"""
        if not self.ws_connection:
            return False
            
        try:
            await self.ws_connection.send(json.dumps(command))
            logger.info(f"发送命令: {command}")
            return True
        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            return False
            
    async def start_server(self, max_retries: int = 3) -> bool:
        """启动服务器"""
        for attempt in range(max_retries):
            command = {"event": "set state", "args": ["start"]}
            
            if await self.send_command(command):
                logger.info(f"✅ 启动命令发送成功 (尝试 {attempt + 1}/{max_retries})")
                return True
            else:
                logger.warning(f"启动命令发送失败 (尝试 {attempt + 1}/{max_retries})")
                
                # 如果不是最后一次尝试，等待一段时间后重试
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"❌ 启动服务器失败，已重试 {max_retries} 次")
        return False
        
    def extract_sshx_link(self, message: str) -> Optional[str]:
        """提取SSHX链接"""
        # 匹配SSHX链接的正则表达式
        pattern = r'https://sshx\.io/s/[a-zA-Z0-9]+#[a-zA-Z0-9]+'
        match = re.search(pattern, message)
        return match.group(0) if match else None
        
    async def send_dingtalk_notification(self, sshx_link: str):
        """发送钉钉通知"""
        try:
            # 构建消息内容
            message = {
                "msgtype": "text",
                "text": {
                    "content": f"🔗 SSHX链接已更新\n\n新的SSHX链接: {sshx_link}\n\n请及时访问以连接到服务器。"
                }
            }
            
            # 发送HTTP请求
            response = requests.post(
                self.dingtalk_webhook_url,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("✅ 钉钉通知发送成功")
                else:
                    logger.error(f"❌ 钉钉通知发送失败: {result.get('errmsg', '未知错误')}")
            else:
                logger.error(f"❌ 钉钉通知HTTP请求失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ 发送钉钉通知异常: {e}")
        
    async def send_server_logs(self):
        """发送服务器日志响应"""
        try:
            if self.ws_connection and not self.ws_connection.closed:
                # 发送日志命令
                logs_command = {"event": "send logs"}
                await self.ws_connection.send(json.dumps(logs_command))
                logger.info("✅ 已发送服务器日志响应")
            else:
                logger.warning("WebSocket连接未建立，无法发送日志响应")
        except Exception as e:
            logger.error(f"❌ 发送服务器日志响应异常: {e}")
    
    async def send_server_stats(self):
        """发送服务器统计响应"""
        try:
            if self.ws_connection and not self.ws_connection.closed:
                # 发送统计命令
                stats_command = {"event": "send stats"}
                await self.ws_connection.send(json.dumps(stats_command))
                logger.info("✅ 已发送服务器统计响应")
            else:
                logger.warning("WebSocket连接未建立，无法发送统计响应")
        except Exception as e:
            logger.error(f"❌ 发送服务器统计响应异常: {e}")
    
    async def request_logs_and_stats(self):
        """认证成功后请求日志和统计信息"""
        try:
            if self.ws_connection and not self.ws_connection.closed:
                # 发送请求日志命令
                logs_command = {"event": "send logs", "args": [None]}
                await self.ws_connection.send(json.dumps(logs_command))
                logger.info("✅ 已发送请求日志命令")
                
                # 发送请求统计命令
                stats_command = {"event": "send stats", "args": [None]}
                await self.ws_connection.send(json.dumps(stats_command))
                logger.info("✅ 已发送请求统计命令")
            else:
                logger.warning("WebSocket连接未建立，无法请求日志和统计")
        except Exception as e:
            logger.error(f"❌ 请求日志和统计异常: {e}")
        
    async def handle_websocket_message(self, message: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            event = data.get('event')
            args = data.get('args', [])
            
            logger.info(f"收到WebSocket消息: {event} - {args}")
            
            if event == 'auth success':
                logger.info("✅ WebSocket认证成功")
                # 认证成功后，主动请求日志和统计信息
                await self.request_logs_and_stats()
                
            elif event == 'send logs':
                logger.info("收到日志请求")
                # 发送日志响应
                await self.send_server_logs()
                
            elif event == 'send stats':
                logger.info("收到统计请求")
                # 发送统计响应
                await self.send_server_stats()
                
            elif event == 'status' and args:
                new_status = args[0]
                if new_status != self.current_status:
                    self.current_status = new_status
                    logger.info(f"状态变化: {new_status}")
                    
                    if new_status == 'offline':
                        logger.warning("服务器已关闭，准备启动...")
                        await self.start_server()
                        
            elif event == 'daemon error' and args:
                error_message = args[0]
                logger.error(f"守护进程错误: {error_message}")
                
                # 检查是否是电源操作冲突错误
                if 'another power action is currently being processed' in error_message:
                    logger.warning("检测到电源操作冲突，将在30秒后重试启动")
                    # 30秒后重试启动
                    await asyncio.sleep(30)
                    if self.current_status == 'offline':
                        logger.info("重试启动服务器...")
                        await self.start_server()
                        
            elif event == 'console output' and args:
                message_text = args[0]
                if 'Link:' in message_text:
                    sshx_link = self.extract_sshx_link(message_text)
                    if sshx_link and sshx_link != self.sshx_link:
                        self.sshx_link = sshx_link
                        logger.info(f"SSHX链接更新: {sshx_link}")
                        await self.send_dingtalk_notification(sshx_link)
                        
        except json.JSONDecodeError as e:
            logger.error(f"解析WebSocket消息失败: {e}")
        except Exception as e:
            logger.error(f"处理WebSocket消息异常: {e}")
            
    async def monitor_websocket(self):
        """监控WebSocket消息"""
        try:
            async for message in self.ws_connection:
                await self.handle_websocket_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket连接关闭")
        except Exception as e:
            logger.error(f"WebSocket监控异常: {e}")
            
    async def run_monitor(self):
        """运行监控"""
        logger.info("启动VPS监控...")
        
        while self.is_running:
            try:
                # 检查登录状态
                if not await self.check_login_status():
                    logger.info("重新登录...")
                    if not await self.login():
                        logger.error("登录失败，等待重试...")
                        await asyncio.sleep(self.config.check_interval)
                        continue
                        
                # 连接WebSocket
                if not self.ws_connection or self.ws_connection.closed:
                    if not await self.connect_websocket():
                        logger.error("WebSocket连接失败，等待重试...")
                        await asyncio.sleep(self.config.check_interval)
                        continue
                        
                # 开始监控
                logger.info("开始监控WebSocket消息...")
                await self.monitor_websocket()
                
            except Exception as e:
                logger.error(f"监控异常: {e}")
                
            # 如果连接断开，等待后重试
            if self.is_running:
                logger.info(f"等待 {self.config.check_interval} 秒后重试...")
                await asyncio.sleep(self.config.check_interval)
                
    async def start(self):
        """启动监控"""
        self.is_running = True
        
        # 初始登录
        if not await self.login():
            logger.error("初始登录失败")
            return
            
        # 开始监控
        await self.run_monitor()
        
    def stop(self):
        """停止监控"""
        self.is_running = False
        logger.info("停止VPS监控")

async def main():
    """主函数"""
    config = VPSConfig()
    
    async with VPSMonitor(config) as monitor:
        try:
            await monitor.start()
        except KeyboardInterrupt:
            logger.info("收到停止信号")
            monitor.stop()
        except Exception as e:
            logger.error(f"程序异常: {e}")
            monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())