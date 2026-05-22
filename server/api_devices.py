"""设备管理API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from loguru import logger

from database import get_db
from models import Device, Stream
from config import settings

router = APIRouter()
_last_stream_snapshots = {}


# Pydantic模型
class DeviceRegister(BaseModel):
    device_name: str
    device_type: str
    location: Optional[str] = None
    ip_address: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None


class DeviceResponse(BaseModel):
    device_id: str
    device_name: str
    device_type: str
    location: Optional[str]
    ip_address: Optional[str]
    status: str
    stream_url: Optional[str]
    resolution: Optional[str]
    fps: Optional[int]
    bitrate: Optional[int]
    network_level: Optional[str]
    network_rtt_ms: Optional[float]
    packet_loss: Optional[float]
    reconnect_count: Optional[int]
    stream_status: Optional[str]
    last_heartbeat: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HeartbeatRequest(BaseModel):
    timestamp: float
    network_level: Optional[str] = None
    network_rtt_ms: Optional[float] = None
    packet_loss: Optional[float] = None


class StreamStatusUpdate(BaseModel):
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate: Optional[int] = None
    network_level: Optional[str] = None
    network_rtt_ms: Optional[float] = None
    packet_loss: Optional[float] = None
    reconnect_count: Optional[int] = None
    stream_status: Optional[str] = None


@router.post("/register", response_model=dict)
async def register_device(
    device_data: DeviceRegister,
    db: AsyncSession = Depends(get_db)
):
    """注册设备（基于IP地址去重）"""
    try:
        # 先查找是否已存在相同IP的设备
        result = await db.execute(
            select(Device).where(Device.ip_address == device_data.ip_address)
        )
        device = result.scalar_one_or_none()

        if device:
            # 设备已存在，更新信息
            device.device_name = device_data.device_name
            device.device_type = device_data.device_type
            device.location = device_data.location
            device.status = "online"
            device.resolution = device_data.resolution or device.resolution
            device.fps = device_data.fps or device.fps
            device.bitrate = device_data.bitrate or device.bitrate
            device.network_level = "good"
            device.stream_status = "registering"
            device.last_heartbeat = datetime.utcnow()

            # 确保有stream_url
            if not device.stream_url or device.stream_url.endswith('/None'):
                device.stream_url = f"rtsp://{settings.RTSP_SERVER_HOST}:{settings.RTSP_SERVER_PORT}/{device.device_id}"

            logger.info(f"设备重新上线: {device.device_id} - {device.device_name}")
        else:
            # 创建新设备
            device = Device(
                device_name=device_data.device_name,
                device_type=device_data.device_type,
                location=device_data.location,
                ip_address=device_data.ip_address,
                status="online",
                resolution=device_data.resolution,
                fps=device_data.fps,
                bitrate=device_data.bitrate,
                network_level="good",
                stream_status="registering",
                last_heartbeat=datetime.utcnow()
            )

            # 生成RTSP流地址
            device.stream_url = f"rtsp://{settings.RTSP_SERVER_HOST}:{settings.RTSP_SERVER_PORT}/{device.device_id}"

            db.add(device)
            logger.info(f"设备注册成功: {device.device_id} - {device.device_name}")

        await db.commit()
        await db.refresh(device)

        return {
            "device_id": device.device_id,
            "stream_url": device.stream_url,
            "message": "设备注册成功"
        }

    except Exception as e:
        logger.error(f"设备注册失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str,
    heartbeat: HeartbeatRequest,
    db: AsyncSession = Depends(get_db)
):
    """设备心跳"""
    try:
        # 更新设备心跳时间、在线状态和可选网络指标
        values = {
            "last_heartbeat": datetime.utcnow(),
            "status": "online",
        }
        if heartbeat.network_level is not None:
            values["network_level"] = heartbeat.network_level
        if heartbeat.network_rtt_ms is not None:
            values["network_rtt_ms"] = heartbeat.network_rtt_ms
        if heartbeat.packet_loss is not None:
            values["packet_loss"] = heartbeat.packet_loss

        stmt = update(Device).where(Device.device_id == device_id).values(**values)
        
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        logger.debug(f"设备心跳: {device_id}")
        
        return {"message": "心跳成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设备心跳失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/stream-status")
async def update_stream_status(
    device_id: str,
    status_data: StreamStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """上报视频参数和网络质量状态"""
    try:
        values = {"updated_at": datetime.utcnow()}
        for field in (
            "resolution",
            "fps",
            "bitrate",
            "network_level",
            "network_rtt_ms",
            "packet_loss",
            "reconnect_count",
            "stream_status",
        ):
            value = getattr(status_data, field)
            if value is not None:
                values[field] = value

        snapshot = {
            "resolution": values.get("resolution"),
            "fps": values.get("fps"),
            "bitrate": values.get("bitrate"),
            "network_level": values.get("network_level"),
            "network_rtt_ms": values.get("network_rtt_ms"),
            "packet_loss": values.get("packet_loss"),
            "reconnect_count": values.get("reconnect_count"),
            "stream_status": values.get("stream_status"),
        }

        stmt = update(Device).where(Device.device_id == device_id).values(**values)
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="设备不存在")

        previous = _last_stream_snapshots.get(device_id, {})
        important_changed = any(
            snapshot.get(key) != previous.get(key)
            for key in ("resolution", "fps", "bitrate", "network_level", "reconnect_count", "stream_status")
        )
        _last_stream_snapshots[device_id] = {**previous, **snapshot}

        if important_changed:
            message = (
                f"视频状态 device={device_id} "
                f"stream={snapshot.get('stream_status') or previous.get('stream_status') or '-'} "
                f"net={snapshot.get('network_level') or previous.get('network_level') or '-'} "
                f"rtt={snapshot.get('network_rtt_ms') if snapshot.get('network_rtt_ms') is not None else '-'}ms "
                f"loss={snapshot.get('packet_loss') if snapshot.get('packet_loss') is not None else '-'} "
                f"reconnects={snapshot.get('reconnect_count') if snapshot.get('reconnect_count') is not None else 0} "
                f"profile={snapshot.get('resolution') or previous.get('resolution') or '-'}@"
                f"{snapshot.get('fps') or previous.get('fps') or '-'}fps/"
                f"{snapshot.get('bitrate') or previous.get('bitrate') or '-'}kbps"
            )
            if snapshot.get("network_level") == "poor" or snapshot.get("stream_status") == "reconnecting":
                logger.warning(message)
            else:
                logger.info(message)
        else:
            logger.debug(f"视频状态心跳 device={device_id} net={snapshot.get('network_level')} rtt={snapshot.get('network_rtt_ms')}ms")

        return {"message": "视频状态更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"视频状态更新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[DeviceResponse])
async def get_devices(
    status: Optional[str] = None,
    device_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取设备列表"""
    try:
        query = select(Device)

        if status:
            query = query.where(Device.status == status)
        if device_type:
            query = query.where(Device.device_type == device_type)

        query = query.order_by(Device.created_at.desc())

        result = await db.execute(query)
        devices = result.scalars().all()

        # 确保每个设备都有stream_url
        for device in devices:
            if not device.stream_url or device.stream_url.endswith('/None'):
                device.stream_url = f"rtsp://{settings.RTSP_SERVER_HOST}:{settings.RTSP_SERVER_PORT}/{device.device_id}"

        return devices

    except Exception as e:
        logger.error(f"获取设备列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取设备详情"""
    try:
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if device is None:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 确保设备有stream_url
        if not device.stream_url or device.stream_url.endswith('/None'):
            device.stream_url = f"rtsp://{settings.RTSP_SERVER_HOST}:{settings.RTSP_SERVER_PORT}/{device.device_id}"

        return device

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取设备详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{device_id}/offline")
async def device_offline(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """设备下线"""
    try:
        stmt = (
            update(Device)
            .where(Device.device_id == device_id)
            .values(status="offline")
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        logger.info(f"设备手动下线: {device_id}")
        
        return {"message": "下线成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设备下线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除设备"""
    try:
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if device is None:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        await db.delete(device)
        await db.commit()
        
        logger.info(f"设备已删除: {device_id}")
        
        return {"message": "设备删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除设备失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
