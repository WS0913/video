"""摄像头采集端主程序"""
import sys
import time
import signal
import asyncio
from loguru import logger

from whip_streamer import WHIPStreamer
from device_manager import DeviceManager
import config


class CameraClient:
    """摄像头客户端"""

    def __init__(self):
        self.streamer: WHIPStreamer = None
        self.device_manager: DeviceManager = None
        self.running = False
        self.loop = None
        self.current_profile = "good"
        self.reconnect_count = 0
        self.last_stream_state = "inactive"
        self.last_report_snapshot = None
        
    async def setup(self) -> bool:
        """初始化设置"""
        try:
            # 配置日志
            logger.remove()
            logger.add(
                sys.stderr,
                level=config.LOG_LEVEL,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
            )
            logger.add(
                "logs/camera_client_{time}.log",
                rotation="100 MB",
                retention="7 days",
                level=config.LOG_LEVEL
            )

            logger.info("摄像头采集端启动 mode=WHIP")

            # 初始化设备管理器
            self.device_manager = DeviceManager(
                server_url=config.SERVER_URL,
                device_name=config.DEVICE_NAME,
                device_type=config.DEVICE_TYPE,
                location=config.DEVICE_LOCATION
            )

            # 注册设备
            if not self.device_manager.register():
                logger.error("设备注册失败")
                return False

            # 启动心跳
            self.device_manager.start_heartbeat(config.HEARTBEAT_INTERVAL)

            # 初始化WHIP推流器
            if not await self.start_streamer("good"):
                logger.error("WHIP推流启动失败")
                return False

            logger.info("初始化完成")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False

    async def start_streamer(self, profile_name: str) -> bool:
        """按网络档位启动WHIP推流"""
        profile = config.NETWORK_PROFILES[profile_name]
        whip_url = f"http://{config.RTSP_SERVER}:8889/{self.device_manager.device_id}/whip"

        self.current_profile = profile_name
        self.last_stream_state = "starting"
        self.device_manager.set_network_level(profile_name)
        logger.info(
            f"启动推流 profile={profile_name} "
            f"resolution={profile['width']}x{profile['height']} "
            f"fps={profile['fps']} bitrate={profile['bitrate']}kbps"
        )

        self.streamer = WHIPStreamer(
            whip_url=whip_url,
            camera_id=config.CAMERA_ID,
            width=profile["width"],
            height=profile["height"],
            fps=profile["fps"],
            bitrate=profile["bitrate"],
            on_state_change=self.handle_stream_state_change,
        )

        started = await self.streamer.start()
        self.last_stream_state = "active" if started else "error"
        self.report_stream_status()
        return started

    def handle_stream_state_change(self, state: str):
        """记录WebRTC连接状态，供主循环执行重连"""
        if state in {"connected", "completed"}:
            self.last_stream_state = "active"
        elif state in {"failed", "disconnected", "closed"}:
            self.last_stream_state = "reconnecting"
        else:
            self.last_stream_state = state

        self.report_stream_status()

    def report_stream_status(self):
        """把当前档位、码率和重连次数同步到后端"""
        if not self.device_manager or not self.device_manager.device_id:
            return

        profile = config.NETWORK_PROFILES[self.current_profile]
        snapshot = (
            self.current_profile,
            profile["width"],
            profile["height"],
            profile["fps"],
            profile["bitrate"],
            self.reconnect_count,
            self.last_stream_state,
            self.device_manager.last_heartbeat_rtt_ms,
            self.device_manager.packet_loss_estimate,
        )
        changed = snapshot[:7] != (self.last_report_snapshot[:7] if self.last_report_snapshot else None)
        if changed:
            logger.info(
                f"采集状态 stream={self.last_stream_state} net={self.current_profile} "
                f"rtt={self.device_manager.last_heartbeat_rtt_ms if self.device_manager.last_heartbeat_rtt_ms is not None else '-'}ms "
                f"loss={self.device_manager.packet_loss_estimate} "
                f"reconnects={self.reconnect_count} "
                f"profile={profile['width']}x{profile['height']}@{profile['fps']}fps/{profile['bitrate']}kbps"
            )
        self.last_report_snapshot = snapshot
        self.device_manager.set_network_level(self.current_profile)
        self.device_manager.report_stream_status({
            "resolution": f"{profile['width']}x{profile['height']}",
            "fps": profile["fps"],
            "bitrate": profile["bitrate"],
            "network_level": self.current_profile,
            "reconnect_count": self.reconnect_count,
            "stream_status": self.last_stream_state,
        })

    def choose_profile(self) -> str:
        """根据心跳连续失败/成功次数选择网络档位"""
        failures = self.device_manager.consecutive_heartbeat_failures
        successes = self.device_manager.consecutive_heartbeat_successes

        if failures >= 3:
            return "poor"
        if failures >= 1:
            return "weak"
        if successes >= config.NETWORK_RECOVERY_SUCCESS_COUNT:
            return "good"
        return self.current_profile

    async def restart_streamer(self, profile_name: str):
        """重建推流连接，可同时完成降级或恢复"""
        self.reconnect_count += 1
        self.last_stream_state = "reconnecting"
        self.report_stream_status()

        if self.streamer:
            await self.streamer.stop()
            self.streamer = None

        await asyncio.sleep(config.STREAM_RECONNECT_DELAY)
        logger.warning(f"重建WHIP推流 profile={profile_name} reconnects={self.reconnect_count}")
        await self.start_streamer(profile_name)
    
    async def run(self):
        """运行主循环"""
        self.running = True

        logger.info("WHIP推流运行中...")

        try:
            # WHIP推流是异步的，只需要保持连接
            while self.running:
                target_profile = self.choose_profile()

                if self.streamer and self.streamer.is_unhealthy():
                    if target_profile == "good":
                        target_profile = "weak"
                    await self.restart_streamer(target_profile)
                    continue

                if target_profile != self.current_profile:
                    logger.warning(f"网络档位变化 {self.current_profile} -> {target_profile}")
                    await self.restart_streamer(target_profile)
                    continue

                self.report_stream_status()
                await asyncio.sleep(config.NETWORK_MONITOR_INTERVAL)

        except KeyboardInterrupt:
            logger.info("收到中断信号")
        except Exception as e:
            logger.error(f"运行异常: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        logger.info("开始清理资源...")

        self.running = False

        if self.streamer:
            await self.streamer.stop()

        if self.device_manager:
            self.device_manager.stop_heartbeat()
            self.device_manager.unregister()

        logger.info("资源清理完成")
        logger.info("摄像头采集端已停止")


async def main():
    """主函数"""
    client = CameraClient()

    # 信号处理
    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}")
        client.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动
    if await client.setup():
        await client.run()
    else:
        logger.error("启动失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
