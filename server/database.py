"""数据库连接和会话管理"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from config import settings
from models import Base
from loguru import logger
from passlib.context import CryptContext
from models import User

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_db():
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await ensure_device_columns(conn)
        
        logger.info("数据库表创建完成")
        
        # 创建默认管理员用户
        await create_default_admin()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def ensure_device_columns(conn):
    """为已存在的 SQLite 设备表补充新增字段。"""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    result = await conn.execute(text("PRAGMA table_info(devices)"))
    existing_columns = {row[1] for row in result.fetchall()}
    columns = {
        "network_level": "VARCHAR(20) DEFAULT 'unknown'",
        "network_rtt_ms": "FLOAT",
        "packet_loss": "FLOAT",
        "reconnect_count": "INTEGER DEFAULT 0",
        "stream_status": "VARCHAR(20) DEFAULT 'inactive'",
    }

    for name, definition in columns.items():
        if name not in existing_columns:
            await conn.execute(text(f"ALTER TABLE devices ADD COLUMN {name} {definition}"))
            logger.info(f"设备表新增字段: {name}")


async def create_default_admin():
    """创建默认管理员用户"""
    try:
        async with async_session_maker() as session:
            # 检查是否已存在admin用户
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user is None:
                # 创建默认管理员
                admin_user = User(
                    username="admin",
                    password_hash=pwd_context.hash("admin123"),
                    role="admin"
                )
                session.add(admin_user)
                await session.commit()
                logger.info("默认管理员用户已创建 (username: admin, password: admin123)")
            else:
                logger.info("管理员用户已存在")
                
    except Exception as e:
        logger.error(f"创建默认管理员失败: {e}")


async def close_database():
    """关闭数据库连接"""
    try:
        await engine.dispose()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")
