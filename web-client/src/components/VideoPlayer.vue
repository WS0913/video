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
import { WHEPClient } from '@/utils/whepClient'
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
let player: WHEPClient | null = null

const statusText = computed(() => {
  if (props.device.status !== 'online') return '离线'
  if (props.device.stream_status === 'reconnecting' || connectionState.value === 'disconnected') return '重连中'
  if (props.device.network_level === 'poor') return '弱网'
  if (props.device.network_level === 'weak') return '降级'
  return '在线'
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
      },
      onError: (message) => {
        loading.value = false
        error.value = message
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
</style>
