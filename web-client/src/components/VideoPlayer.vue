<template>
  <div class="video-player">
    <div class="video-header">
      <span class="device-name">{{ device.device_name }}</span>
      <div class="controls">
        <el-icon class="control-icon" @click="toggleFullscreen"><FullScreen /></el-icon>
        <el-icon class="control-icon" @click="handleClose"><Close /></el-icon>
      </div>
    </div>
    <div class="video-container" ref="videoContainer">
      <video ref="videoElement" class="video-element" autoplay muted></video>
      <div v-if="loading" class="loading-overlay">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
      <div v-if="error" class="error-overlay">
        <el-icon :size="40"><WarningFilled /></el-icon>
        <p>{{ error }}</p>
      </div>

      <!-- 性能监控面板 -->
      <div class="stats-panel" v-if="showStats && stats">
        <div class="stats-header">
          <span class="stats-title">📊 实时性能监控</span>
          <el-icon class="close-stats" @click="showStats = false"><Close /></el-icon>
        </div>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">分辨率</span>
            <span class="stat-value">{{ stats.resolution || '-' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">帧率</span>
            <span class="stat-value">{{ stats.fps }} fps</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">码率</span>
            <span class="stat-value">{{ stats.bitrate }} kbps</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">丢包率</span>
            <span class="stat-value" :class="{ 'stat-warning': stats.packetLoss > 5, 'stat-danger': stats.packetLoss > 10 }">
              {{ stats.packetLoss }}%
            </span>
          </div>
          <div class="stat-item">
            <span class="stat-label">RTT</span>
            <span class="stat-value" :class="{ 'stat-warning': stats.rtt > 100, 'stat-danger': stats.rtt > 200 }">
              {{ stats.rtt }} ms
            </span>
          </div>
          <div class="stat-item">
            <span class="stat-label">抖动</span>
            <span class="stat-value">{{ stats.jitter }} ms</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">丢包数</span>
            <span class="stat-value">{{ stats.packetsLost }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">接收包数</span>
            <span class="stat-value">{{ stats.packetsReceived }}</span>
          </div>
          <div class="stat-item full-width">
            <span class="stat-label">网络档位</span>
            <span class="stat-value network-level" :class="'level-' + (device.network_level || 'good')">
              {{ networkLevelText }}
            </span>
          </div>
        </div>
      </div>

      <!-- 显示统计按钮 -->
      <div class="stats-toggle" @click="showStats = !showStats" v-if="!loading && !error">
        <el-icon><DataAnalysis /></el-icon>
      </div>
    </div>
    <div class="video-footer">
      <span class="info">
        {{ device.resolution || '720P' }} | {{ device.fps || 25 }}fps
        <template v-if="device.bitrate"> | {{ device.bitrate }}kbps</template>
      </span>
      <span class="status" :class="device.status">
        <el-icon><VideoCameraFilled /></el-icon>
        {{ statusText }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { Device } from '@/types'
import { WHEPClient, type VideoStats } from '@/utils/whepClient'
import config from '@/config'

interface Props {
  device: Device
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const videoElement = ref<HTMLVideoElement>()
const videoContainer = ref<HTMLDivElement>()
const loading = ref(true)
const error = ref('')
const connectionState = ref('')
const showStats = ref(false)
const stats = ref<VideoStats | null>(null)
let player: WHEPClient | null = null
let statsInterval: number | null = null
let lastBytesReceived = 0
let lastTimestamp = 0

const statusText = computed(() => {
  if (props.device.status !== 'online') return '离线'
  if (props.device.stream_status === 'reconnecting' || connectionState.value === 'disconnected') return '重连中'
  if (props.device.network_level === 'poor') return '弱网'
  if (props.device.network_level === 'weak') return '降级'
  return '在线'
})

const networkLevelText = computed(() => {
  const level = props.device.network_level || 'good'
  const levelMap: Record<string, string> = {
    good: '良好',
    weak: '一般',
    poor: '较差'
  }
  return levelMap[level] || level
})

// 初始化视频流
const initVideoStream = async () => {
  if (!videoElement.value || !props.device.device_id) {
    error.value = '无效的视频流地址'
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = ''

    // 从RTSP URL提取device_id，或直接使用device_id
    const deviceId = props.device.device_id

    // MediaMTX的WebRTC WHEP端点
    // 格式: http://{host}:8889/{stream_name}/whep
    const whepUrl = `${config.webrtcBaseUrl}/${deviceId}/whep`

    console.log('Connecting to WHEP endpoint:', whepUrl)

    player = new WHEPClient(videoElement.value, whepUrl, {
      onLoading: () => {
        loading.value = true
      },
      onRecovered: () => {
        loading.value = false
        error.value = ''
        // 开始统计
        startStatsCollection()
      },
      onError: (message) => {
        loading.value = false
        error.value = message
        // 停止统计
        stopStatsCollection()
      },
      onStateChange: (state) => {
        connectionState.value = state
      },
    })

    // 加载流
    await player.start()

    loading.value = false

  } catch (err) {
    console.error('初始化视频流失败:', err)
    error.value = `视频加载失败: ${err instanceof Error ? err.message : String(err)}`
    loading.value = false
  }
}

// 开始收集统计信息
const startStatsCollection = () => {
  if (statsInterval) return

  lastBytesReceived = 0
  lastTimestamp = Date.now()

  statsInterval = window.setInterval(async () => {
    if (!player) return

    const currentStats = await player.getStats()
    if (currentStats) {
      // 计算码率（kbps）
      const now = Date.now()
      const timeDiff = (now - lastTimestamp) / 1000 // 秒
      const bytesDiff = currentStats.bytesReceived - lastBytesReceived

      if (timeDiff > 0 && lastBytesReceived > 0) {
        currentStats.bitrate = Math.round((bytesDiff * 8) / timeDiff / 1000) // kbps
      }

      lastBytesReceived = currentStats.bytesReceived
      lastTimestamp = now

      stats.value = currentStats
    }
  }, 1000) // 每秒更新一次
}

// 停止收集统计信息
const stopStatsCollection = () => {
  if (statsInterval) {
    clearInterval(statsInterval)
    statsInterval = null
  }
  stats.value = null
}

const toggleFullscreen = () => {
  if (!videoContainer.value) return

  if (!document.fullscreenElement) {
    videoContainer.value.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

const handleClose = () => {
  emit('close')
}

onMounted(() => {
  initVideoStream()
})

onUnmounted(() => {
  // 停止统计收集
  stopStatsCollection()

  // 清理WebRTC播放器
  if (player) {
    player.stop()
    player = null
  }
})
</script>

<style scoped>
.video-player {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #000;
}

.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 14px;
}

.device-name {
  font-weight: 500;
}

.controls {
  display: flex;
  gap: 10px;
}

.control-icon {
  cursor: pointer;
  font-size: 18px;
  transition: color 0.3s;
}

.control-icon:hover {
  color: #409eff;
}

.video-container {
  flex: 1;
  position: relative;
  background: #000;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.8);
  color: white;
}

.loading-overlay p,
.error-overlay p {
  margin-top: 10px;
  font-size: 14px;
}

.video-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.7);
  color: #ccc;
  font-size: 12px;
}

.status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status.online {
  color: #67c23a;
}

.status.offline {
  color: #f56c6c;
}

/* 性能监控面板样式 */
.stats-panel {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.85);
  border-radius: 8px;
  padding: 12px;
  min-width: 280px;
  color: white;
  font-size: 12px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  z-index: 10;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-title {
  font-weight: 600;
  font-size: 13px;
}

.close-stats {
  cursor: pointer;
  font-size: 16px;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.close-stats:hover {
  opacity: 1;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-item.full-width {
  grid-column: 1 / -1;
}

.stat-label {
  font-size: 11px;
  color: #aaa;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #67c23a;
}

.stat-value.stat-warning {
  color: #e6a23c;
}

.stat-value.stat-danger {
  color: #f56c6c;
}

.stat-value.network-level {
  padding: 4px 8px;
  border-radius: 4px;
  text-align: center;
  font-size: 13px;
}

.stat-value.level-good {
  background: rgba(103, 194, 58, 0.2);
  color: #67c23a;
}

.stat-value.level-weak {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.stat-value.level-poor {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

/* 统计按钮 */
.stats-toggle {
  position: absolute;
  bottom: 10px;
  right: 10px;
  width: 40px;
  height: 40px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  font-size: 20px;
  transition: all 0.3s;
  z-index: 10;
}

.stats-toggle:hover {
  background: rgba(64, 158, 255, 0.8);
  transform: scale(1.1);
}
</style>
