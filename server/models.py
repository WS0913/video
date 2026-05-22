"""数据库模型"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import bcrypt
import uuid

from config import settings

Base = declarative_base()


def hash_password(password: str) -> str:
    """哈希密码"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_uuid():
    """生成UUID"""
    return str(uuid.uuid4())


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer")  # admin/operator/viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Device(Base):
    """设备模型"""
    __tablename__ = "devices"
    
    device_id = Column(String(36), primary_key=True, default=generate_uuid)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(20), nullable=False)  # robot/fixed
    location = Column(String(200))
    ip_address = Column(String(50))
    status = Column(String(20), default="offline")  # online/offline/error
    stream_url = Column(String(500))
    resolution = Column(String(20))
    fps = Column(Integer)
    bitrate = Column(Integer)
    network_level = Column(String(20), default="unknown")  # good/weak/poor/unknown
    network_rtt_ms = Column(Float)
    packet_loss = Column(Float)
    reconnect_count = Column(Integer, default=0)
    stream_status = Column(String(20), default="inactive")  # active/inactive/reconnecting/error
    last_heartbeat = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Stream(Base):
    """视频流模型"""
    __tablename__ = "streams"
    
    stream_id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), nullable=False, index=True)
    stream_url = Column(String(500), nullable=False)
    status = Column(String(20), default="inactive")  # active/inactive
    bitrate = Column(Integer)
    resolution = Column(String(20))
    fps = Column(Integer)
    viewers = Column(Integer, default=0)
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recording(Base):
    """录像模型"""
    __tablename__ = "recordings"
    
    recording_id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(36), nullable=False, index=True)
    device_name = Column(String(100))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Integer)  # 秒
    file_path = Column(String(500))
    file_size = Column(Integer)  # 字节
    status = Column(String(20), default="recording")  # recording/completed/error
    created_at = Column(DateTime, default=datetime.utcnow)


class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = "operation_logs"

    log_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), index=True)
    username = Column(String(50))
    operation = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    details = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


# 数据库引擎和会话
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    # 创建默认管理员账户
    async with AsyncSessionLocal() as session:
        # 检查是否已存在管理员
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()

        if not admin:
            # 创建管理员账户
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin"
            )
            session.add(admin)
            await session.commit()
            print("✅ 默认管理员账户已创建: admin / admin123")
        else:
            print("ℹ️  管理员账户已存在")

    print("✅ 数据库初始化完成")
