"""WHIP WebRTC推流模块 - 超低延迟"""
import asyncio
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from aiohttp import ClientSession
from av import VideoFrame
from loguru import logger
import time
from fractions import Fraction
from typing import Callable, Optional


from picamera2 import Picamera2



class CameraVideoTrack(VideoStreamTrack):

    def __init__(self, width=1280, height=720, fps=30):
        super().__init__()

        self.width = width
        self.height = height
        self.fps = fps

        self.picam2 = Picamera2()

        config = self.picam2.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )

        self.picam2.configure(config)

        self.picam2.start()

        self.frame_count = 0
        self.start_time = time.time()

    async def recv(self):

        pts, time_base = await self.next_timestamp()

        frame = self.picam2.capture_array()



        video_frame = VideoFrame.from_ndarray(
            frame,
            format="bgr24"
        )

        video_frame.pts = pts
        video_frame.time_base = time_base

        self.frame_count += 1

        return video_frame

    def stop(self):
        """停止摄像头"""
        if hasattr(self, 'picam2') and self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
            except Exception as e:
                logger.warning(f"停止摄像头时出错: {e}")


class WHIPStreamer:
    """WHIP推流器 - 直接WebRTC推流"""

    def __init__(
        self,
        whip_url: str,
        camera_id: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        bitrate: int = 2000,
        on_state_change: Optional[Callable[[str], None]] = None
    ):
        self.whip_url = whip_url
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.on_state_change = on_state_change

        self.pc = None
        self.video_track = None
        self.session = None
        self.connection_state = "new"

    async def start(self):
        """启动WHIP推流"""
        try:
            logger.info(
                f"启动WHIP推流 url={self.whip_url} "
                f"resolution={self.width}x{self.height} fps={self.fps} bitrate={self.bitrate}kbps"
            )

            # 创建 PeerConnection
            self.pc = RTCPeerConnection()

            @self.pc.on("connectionstatechange")
            async def on_connectionstatechange():
                # 检查 pc 是否还存在，避免空指针异常
                if self.pc is None:
                    return
                self.connection_state = self.pc.connectionState
                if self.connection_state in {"failed", "disconnected", "closed"}:
                    logger.warning(f"WHIP连接状态 state={self.connection_state}")
                else:
                    logger.info(f"WHIP连接状态 state={self.connection_state}")
                if self.on_state_change:
                    self.on_state_change(self.connection_state)

            # 创建视频轨道
            self.video_track = CameraVideoTrack(
                width=self.width,
                height=self.height,
                fps=self.fps
            )

            # 添加视频轨道
            sender = self.pc.addTrack(self.video_track)
            try:
                parameters = sender.getParameters()
                if parameters.encodings:
                    parameters.encodings[0].maxBitrate = self.bitrate * 1000
                await sender.setParameters(parameters)
            except Exception as e:
                logger.debug(f"设置WebRTC发送码率失败，使用默认拥塞控制: {e}")

            # 创建 Offer
            offer = await self.pc.createOffer()
            await self.pc.setLocalDescription(offer)

            # 发送 Offer 到 WHIP 端点
            self.session = ClientSession()
            async with self.session.post(
                self.whip_url,
                data=self.pc.localDescription.sdp,
                headers={"Content-Type": "application/sdp"}
            ) as response:
                if response.status != 201:
                    raise Exception(f"WHIP请求失败: {response.status}")

                answer_sdp = await response.text()

                # 设置远程描述
                answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
                await self.pc.setRemoteDescription(answer)

            logger.info("WHIP推流已启动")
            return True

        except Exception as e:
            logger.error(f"启动WHIP推流失败: {e}")
            await self.stop()
            return False

    def is_unhealthy(self) -> bool:
        """判断连接是否需要重建"""
        return self.connection_state in {"failed", "disconnected", "closed"}

    async def stop(self):
        """停止推流"""
        logger.info("停止WHIP推流...")

        # 先停止视频轨道，释放摄像头
        if self.video_track:
            try:
                self.video_track.stop()
            except Exception as e:
                logger.warning(f"停止视频轨道时出错: {e}")
            self.video_track = None

        # 关闭 PeerConnection
        if self.pc:
            try:
                await self.pc.close()
            except Exception as e:
                logger.warning(f"关闭PeerConnection时出错: {e}")
            self.pc = None

        # 关闭 HTTP session
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.warning(f"关闭HTTP session时出错: {e}")
            self.session = None

        self.connection_state = "closed"

        logger.info("WHIP推流已停止")
