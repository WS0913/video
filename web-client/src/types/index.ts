/**
 * 类型定义
 */

// 设备类型
export interface Device {
  device_id: string
  device_name: string
  device_type: 'robot' | 'fixed'
  location?: string
  ip_address?: string
  status: 'online' | 'offline' | 'error'
  stream_url?: string
  resolution?: string
  fps?: number
  bitrate?: number
  network_level?: 'good' | 'weak' | 'poor' | 'unknown'
  network_rtt_ms?: number
  packet_loss?: number
  reconnect_count?: number
  stream_status?: 'active' | 'inactive' | 'reconnecting' | 'error' | string
  last_heartbeat?: string
  created_at: string
}

// 用户类型
export interface User {
  user_id: string
  username: string
  role: 'admin' | 'operator' | 'viewer'
  created_at: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  token_type: string
}

// 视频流信息
export interface StreamInfo {
  device_id: string
  device_name: string
  stream_url: string
  status: 'active' | 'inactive'
}

// 录像信息
export interface Recording {
  recording_id: string
  device_id: string
  device_name: string
  start_time: string
  end_time?: string
  duration?: number
  file_path?: string
  file_size?: number
  status: 'recording' | 'completed' | 'error'
  created_at: string
}

// WebSocket消息类型
export enum WSMessageType {
  DEVICE_STATUS = 'device_status',
  STREAM_STATUS = 'stream_status',
  SYSTEM_ALERT = 'system_alert',
  HEARTBEAT = 'heartbeat',
}

// WebSocket消息
export interface WSMessage {
  type: WSMessageType
  timestamp: string
  data: any
}

// 分屏布局
export type LayoutType = 1 | 4 | 9 | 16

// API响应
export interface ApiResponse<T = any> {
  code?: number
  message?: string
  data?: T
}
