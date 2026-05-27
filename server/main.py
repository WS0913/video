"""传输服务器主程序"""
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
import os

from config import settings
from database import init_database, close_database
import api_devices
import api_auth
import api_recordings
import api_config
from recording_scanner import scanner
from device_monitor import monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("=" * 60)
    logger.info("传输服务器启动")
    logger.info("=" * 60)

    # 初始化数据库
    await init_database()

    # 创建录像目录
    os.makedirs(settings.RECORDING_PATH, exist_ok=True)

    # 启动录像扫描服务（后台任务）
    scanner_task = asyncio.create_task(scanner.start())
    # 启动设备监控服务（后台任务）
    monitor_task = asyncio.create_task(monitor.start())

    logger.info("服务器初始化完成")

    yield

    # 关闭时清理
    logger.info("开始清理资源...")

    scanner.stop()
    scanner_task.cancel()

    monitor.stop()
    monitor_task.cancel()

    try:
        await asyncio.gather(scanner_task, monitor_task, return_exceptions=True)
    except Exception as e:
        logger.error(f"清理后台任务异常: {e}")

    await close_database()
    logger.info("传输服务器已停止")


# 创建FastAPI应用
app = FastAPI(
    title="电厂巡检视频传输系统",
    description="端到端无线视频传输系统API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS（从环境变量读取允许的来源）
# 开发环境可以使用 CORS_ORIGINS="*" 允许所有来源
# 生产环境应该明确指定允许的前端地址
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
allow_credentials = settings.CORS_ORIGINS != "*"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时输出安全提示
if settings.SECRET_KEY == "your-secret-key-change-this-in-production":
    logger.warning("⚠️  警告：正在使用默认JWT密钥，生产环境必须修改 SECRET_KEY")
if settings.DEVICE_API_TOKEN == "device-api-token-change-in-production":
    logger.warning("⚠️  警告：正在使用默认设备API令牌，生产环境必须修改 DEVICE_API_TOKEN")
if settings.CORS_ORIGINS == "*":
    logger.warning("⚠️  警告：CORS允许所有来源，生产环境建议限制为具体前端地址")

# 注册路由
app.include_router(api_auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(api_devices.router, prefix="/api/devices", tags=["设备管理"])
app.include_router(api_recordings.router, prefix="/api/recordings", tags=["录像管理"])
app.include_router(api_config.router)

# 静态文件服务（录像文件）
if os.path.exists(settings.RECORDING_PATH):
    app.mount("/recordings", StaticFiles(directory=settings.RECORDING_PATH), name="recordings")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "电厂巡检视频传输系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


def setup_logging():
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    logger.add(
        "logs/server_{time}.log",
        rotation="100 MB",
        retention="7 days",
        level=settings.LOG_LEVEL
    )


if __name__ == "__main__":
    import uvicorn

    # 配置日志
    setup_logging()

    # 启动服务器
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )

