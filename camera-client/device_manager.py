"""设备管理模块"""
import requests
import time
import threading
import socket
from loguru import logger
from typing import Optional, Dict


class DeviceManager:
    """设备管理类"""

    def __init__(
        self,
        server_url: str,
        device_name: str,
        device_type: str,
        location: str
    ):
        """
        初始化设备管理器

        Args:
            server_url: 服务器地址
            device_name: 设备名称
            device_type: 设备类型
            location: 设备位置
        """
        self.server_url = server_url.rstrip('/')
        self.device_name = device_name
        self.device_type = device_type
        self.location = location

        self.device_id: Optional[str] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.running = False
        self.consecutive_heartbeat_failures = 0
        self.consecutive_heartbeat_successes = 0
        self.last_heartbeat_rtt_ms: Optional[float] = None
        self.packet_loss_estimate = 0.0
        self.network_level = "good"

    def get_local_ip(self) -> str:
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def register(self) -> bool:
        """
        注册设备

        Returns:
            bool: 是否注册成功
        """
        try:
            device_info = {
                "device_name": self.device_name,
                "device_type": self.device_type,
                "location": self.location,
                "ip_address": self.get_local_ip()
            }

            logger.info(
                f"注册设备 name={self.device_name} type={self.device_type} "
                f"location={self.location} ip={device_info['ip_address']}"
            )

            response = requests.post(
                f'{self.server_url}/api/devices/register',
                json=device_info,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.device_id = data.get('device_id')
                logger.info(f"设备注册成功 device={self.device_id}")
                return True
            else:
                logger.error(f"设备注册失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"设备注册异常: {e}")
            return False

    def start_heartbeat(self, interval: int = 10):
        """
        启动心跳

        Args:
            interval: 心跳间隔(秒)
        """
        if self.device_id is None:
            logger.error("设备未注册，无法启动心跳")
            return

        self.running = True
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(interval,),
            daemon=True
        )
        self.heartbeat_thread.start()
        logger.info(f"心跳已启动，间隔: {interval}秒")

    def _heartbeat_loop(self, interval: int):
        """心跳循环"""
        while self.running:
            try:
                started_at = time.time()
                response = requests.post(
                    f'{self.server_url}/api/devices/{self.device_id}/heartbeat',
                    json={
                        'timestamp': time.time(),
                        'network_level': self.network_level,
                        'network_rtt_ms': self.last_heartbeat_rtt_ms,
                        'packet_loss': self.packet_loss_estimate,
                    },
                    timeout=5
                )
                self.last_heartbeat_rtt_ms = round((time.time() - started_at) * 1000, 2)

                if response.status_code == 200:
                    self.consecutive_heartbeat_failures = 0
                    self.consecutive_heartbeat_successes += 1
                    self.packet_loss_estimate = 0.0
                    # 每10次心跳打印一次，保留周期性日志
                    if self.consecutive_heartbeat_successes % 10 == 1:
                        logger.info(f"心跳正常 device={self.device_id} rtt={self.last_heartbeat_rtt_ms}ms net={self.network_level}")
                    else:
                        logger.debug(f"心跳成功 device={self.device_id} rtt={self.last_heartbeat_rtt_ms}ms")
                else:
                    self.consecutive_heartbeat_failures += 1
                    self.consecutive_heartbeat_successes = 0
                    self.packet_loss_estimate = min(1.0, self.consecutive_heartbeat_failures / 3)
                    logger.warning(
                        f"心跳失败 device={self.device_id} status={response.status_code} "
                        f"failures={self.consecutive_heartbeat_failures} net={self.network_level}"
                    )

            except Exception as e:
                self.consecutive_heartbeat_failures += 1
                self.consecutive_heartbeat_successes = 0
                self.packet_loss_estimate = min(1.0, self.consecutive_heartbeat_failures / 3)
                logger.warning(
                    f"心跳异常 device={self.device_id} failures={self.consecutive_heartbeat_failures} "
                    f"net={self.network_level} error={e}"
                )

            time.sleep(interval)

    def set_network_level(self, level: str):
        """更新心跳上报的网络等级"""
        self.network_level = level

    def report_stream_status(self, status: Dict) -> bool:
        """上报推流参数和网络状态"""
        if self.device_id is None:
            return False

        try:
            payload = {
                **status,
                "network_rtt_ms": self.last_heartbeat_rtt_ms,
                "packet_loss": self.packet_loss_estimate,
            }
            response = requests.post(
                f'{self.server_url}/api/devices/{self.device_id}/stream-status',
                json=payload,
                timeout=5
            )
            if response.status_code == 200:
                logger.debug(
                    f"状态上报成功 device={self.device_id} stream={payload.get('stream_status')} "
                    f"net={payload.get('network_level')} rtt={payload.get('network_rtt_ms')}ms "
                    f"loss={payload.get('packet_loss')} reconnects={payload.get('reconnect_count')}"
                )
                return True

            logger.warning(f"视频状态上报失败: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"视频状态上报异常: {e}")
            return False

    def stop_heartbeat(self):
        """停止心跳"""
        self.running = False
        if self.heartbeat_thread is not None:
            self.heartbeat_thread.join(timeout=5)
            logger.info("心跳已停止")

    def unregister(self) -> bool:
        """
        注销设备（标记为离线）

        Returns:
            bool: 是否注销成功
        """
        if self.device_id is None:
            return True

        try:
            response = requests.post(
                f'{self.server_url}/api/devices/{self.device_id}/offline',
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"设备注销成功: {self.device_id}")
                return True
            else:
                logger.error(f"设备注销失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"设备注销异常: {e}")
            return False
