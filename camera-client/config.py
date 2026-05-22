"""配置文件"""
import os
from dotenv import load_dotenv

load_dotenv()

# 服务器配置
SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:8000')

# 设备API令牌（用于认证）
DEVICE_API_TOKEN = os.getenv('DEVICE_API_TOKEN', 'device-api-token-change-in-production')

# 设备配置
DEVICE_NAME = os.getenv('DEVICE_NAME', 'Camera-001')
DEVICE_TYPE = os.getenv('DEVICE_TYPE', 'robot')  # robot 或 fixed
DEVICE_LOCATION = os.getenv('DEVICE_LOCATION', '1号机组')

# 摄像头配置
CAMERA_ID = int(os.getenv('CAMERA_ID', '0'))  # 0表示默认摄像头
RESOLUTION_WIDTH = int(os.getenv('RESOLUTION_WIDTH', '1280'))
RESOLUTION_HEIGHT = int(os.getenv('RESOLUTION_HEIGHT', '720'))
FPS = int(os.getenv('FPS', '25'))

# 编码配置
VIDEO_CODEC = 'libx264'
BITRATE = int(os.getenv('BITRATE', '2000'))  # kbps
PRESET = 'ultrafast'
TUNE = 'zerolatency'

# 弱网自适应配置
NETWORK_PROFILES = {
    "good": {
        "width": RESOLUTION_WIDTH,
        "height": RESOLUTION_HEIGHT,
        "fps": FPS,
        "bitrate": BITRATE,
    },
    "weak": {
        "width": int(os.getenv('WEAK_RESOLUTION_WIDTH', '960')),
        "height": int(os.getenv('WEAK_RESOLUTION_HEIGHT', '540')),
        "fps": int(os.getenv('WEAK_FPS', '20')),
        "bitrate": int(os.getenv('WEAK_BITRATE', '1200')),
    },
    "poor": {
        "width": int(os.getenv('POOR_RESOLUTION_WIDTH', '640')),
        "height": int(os.getenv('POOR_RESOLUTION_HEIGHT', '360')),
        "fps": int(os.getenv('POOR_FPS', '15')),
        "bitrate": int(os.getenv('POOR_BITRATE', '600')),
    },
}

NETWORK_MONITOR_INTERVAL = int(os.getenv('NETWORK_MONITOR_INTERVAL', '2'))
NETWORK_RECOVERY_SUCCESS_COUNT = int(os.getenv('NETWORK_RECOVERY_SUCCESS_COUNT', '6'))
STREAM_RECONNECT_DELAY = int(os.getenv('STREAM_RECONNECT_DELAY', '3'))

# RTSP配置
RTSP_SERVER = os.getenv('RTSP_SERVER', 'localhost')
RTSP_PORT = int(os.getenv('RTSP_PORT', '8554'))

# 心跳配置
HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', '10'))  # 秒

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
