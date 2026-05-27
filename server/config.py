"""服务器配置"""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """配置类"""

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./video_system.db"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-this-in-production"  # 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 设备API令牌（用于设备端注册/心跳认证）
    DEVICE_API_TOKEN: str = "device-api-token-change-in-production"  # 生产环境必须修改

    # RTSP服务器配置
    RTSP_SERVER_HOST: str = "localhost"
    RTSP_SERVER_PORT: int = 8554

    # 录像存储配置
    RECORDING_PATH: str = "./recordings"

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # CORS配置（支持局域网访问）
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> List[str]:
        """获取CORS源列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 全局配置实例
settings = Settings()

