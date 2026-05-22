"""设备在线状态监控服务"""
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import select, update

from models import Device, AsyncSessionLocal
from config import settings


class DeviceMonitor:
    """设备状态监控器，负责检测心跳超时并将设备置为离线"""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.check_interval = 6  # 检查间隔（秒）
        self.running = False

    async def check_device_status(self):
        """检查所有在线设备的心跳时间"""
        try:
            async with AsyncSessionLocal() as db:
                # 找出所有状态为 online 且心跳超时的设备
                threshold_time = datetime.utcnow() - timedelta(seconds=self.timeout_seconds)
                
                # 查询超时的设备
                stmt = (
                    select(Device)
                    .where(Device.status == "online")
                    .where(Device.last_heartbeat < threshold_time)
                )
                
                result = await db.execute(stmt)
                timeout_devices = result.scalars().all()
                
                if timeout_devices:
                    for device in timeout_devices:
                        logger.warning(f"设备心跳超时，设置为离线: {device.device_id} ({device.device_name})")
                        device.status = "offline"
                        device.network_level = "poor"
                        device.stream_status = "inactive"
                    
                    await db.commit()
                    logger.info(f"已更新 {len(timeout_devices)} 个设备的状态为离线")
                
        except Exception as e:
            logger.error(f"检查设备状态失败: {e}")

    async def start(self):
        """启动监控服务"""
        self.running = True
        logger.info(f"设备监控服务启动，超时阈值: {self.timeout_seconds}s, 检查间隔: {self.check_interval}s")

        while self.running:
            await self.check_device_status()
            await asyncio.sleep(self.check_interval)

    def stop(self):
        """停止监控服务"""
        self.running = False
        logger.info("设备监控服务停止")


# 全局监控器实例
monitor = DeviceMonitor()


async def start_monitor():
    """启动监控器"""
    await monitor.start()


def stop_monitor():
    """停止监控器"""
    monitor.stop()
