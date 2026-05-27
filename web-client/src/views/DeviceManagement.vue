<template>
  <div class="device-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备列表</span>
          <el-button type="primary" @click="refreshDevices" :loading="deviceStore.loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-select v-model="filterStatus" placeholder="设备状态" clearable @change="handleFilter">
          <el-option label="全部" value="" />
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
        </el-select>
        <el-select v-model="filterType" placeholder="设备类型" clearable @change="handleFilter">
          <el-option label="全部" value="" />
          <el-option label="机器人" value="robot" />
          <el-option label="固定摄像头" value="fixed" />
        </el-select>
      </div>

      <!-- 设备表格 -->
      <el-table :data="deviceStore.devices" v-loading="deviceStore.loading" stripe>
        <el-table-column prop="device_name" label="设备名称" min-width="120" />
        <el-table-column prop="device_type" label="设备类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.device_type === 'robot' ? 'success' : 'info'">
              {{ row.device_type === 'robot' ? '机器人' : '固定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" min-width="150" />
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resolution" label="分辨率" width="100" />
        <el-table-column prop="fps" label="帧率" width="80">
          <template #default="{ row }">
            {{ row.fps ? `${row.fps}fps` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="bitrate" label="码率" width="90">
          <template #default="{ row }">
            {{ row.bitrate ? `${row.bitrate}kbps` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="network_level" label="网络" width="90">
          <template #default="{ row }">
            <el-tag :type="networkTagType(row.network_level)">
              {{ formatNetworkLevel(row.network_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="stream_status" label="视频流" width="100">
          <template #default="{ row }">
            {{ formatStreamStatus(row.stream_status) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_heartbeat" label="最后心跳" width="160">
          <template #default="{ row }">
            {{ row.last_heartbeat ? formatTime(row.last_heartbeat) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewStream(row)">
              查看视频
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDeviceStore } from '@/stores/device'
import { deleteDevice } from '@/api/device'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Device } from '@/types'

const router = useRouter()
const deviceStore = useDeviceStore()

const filterStatus = ref('')
const filterType = ref('')

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

const formatNetworkLevel = (level?: string) => {
  const map: Record<string, string> = {
    good: '良好',
    weak: '降级',
    poor: '弱网',
    unknown: '未知',
  }
  return map[level || 'unknown'] || '未知'
}

const networkTagType = (level?: string) => {
  if (level === 'good') return 'success'
  if (level === 'weak') return 'warning'
  if (level === 'poor') return 'danger'
  return 'info'
}

const formatStreamStatus = (status?: string) => {
  const map: Record<string, string> = {
    active: '传输中',
    inactive: '未传输',
    reconnecting: '重连中',
    registering: '注册中',
    starting: '启动中',
    error: '异常',
  }
  return map[status || 'inactive'] || status || '-'
}

const handleFilter = () => {
  const params: any = {}
  if (filterStatus.value) params.status = filterStatus.value
  if (filterType.value) params.device_type = filterType.value
  deviceStore.fetchDevices(params)
}

const refreshDevices = () => {
  handleFilter()
}

const viewStream = (device: Device) => {
  deviceStore.selectDevice(device.device_id)
  router.push('/monitor')
}

const handleDelete = async (device: Device) => {
  try {
    await ElMessageBox.confirm(`确定要删除设备 "${device.device_name}" 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await deleteDevice(device.device_id)
    ElMessage.success('删除成功')
    refreshDevices()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  refreshDevices()
})
</script>

<style scoped>
.device-management {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.el-select {
  width: 150px;
}
</style>
