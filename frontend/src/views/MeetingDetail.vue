<template>
  <div class="meeting-detail-container" v-loading="meetingStore.detailLoading">
    <!-- 返回按钮 -->
    <el-button @click="handleBack" style="margin-bottom: 20px">
      <el-icon><ArrowLeft /></el-icon>
      返回列表
    </el-button>

    <!-- 会议基础信息 -->
    <el-card v-if="meetingStore.currentMeeting" class="info-card">
      <template #header>
        <div class="card-header">
          <span>{{ meetingStore.currentMeeting.title }}</span>
          <el-tag :type="getStatusType(meetingStore.currentMeeting.status)">
            {{ getStatusText(meetingStore.currentMeeting.status) }}
          </el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="会议ID">
          {{ meetingStore.currentMeeting.meeting_id }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(meetingStore.currentMeeting.status)">
            {{ getStatusText(meetingStore.currentMeeting.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ meetingStore.currentMeeting.created_at }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ meetingStore.currentMeeting.updated_at }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="meetingStore.currentMeeting.error_msg"
          label="错误信息"
          :span="2"
        >
          <el-text type="danger">{{ meetingStore.currentMeeting.error_msg }}</el-text>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 操作按钮 -->
      <div class="actions" style="margin-top: 20px">
        <el-button
          v-if="['uploaded', 'failed', 'transcribed'].includes(meetingStore.currentMeeting.status)"
          type="primary"
          @click="handleProcess"
        >
          触发处理
        </el-button>
        <el-button
          v-if="meetingStore.currentMeeting.status === 'done'"
          type="success"
          @click="handleDownloadMarkdown"
        >
          下载纪要
        </el-button>
        <el-button type="info" @click="handleRefresh">
          刷新
        </el-button>
      </div>
    </el-card>

    <!-- 转写中提示 -->
    <el-alert
      v-if="isProcessing"
      title="会议正在处理中，页面将自动刷新..."
      type="info"
      :closable="false"
      show-icon
      style="margin-top: 20px"
    />

    <!-- 发言人列表 -->
    <el-card v-if="meetingStore.speakers.length > 0" class="speakers-card">
      <template #header>
        <div class="card-header">
          <span>发言人列表</span>
          <el-button size="small" @click="openSpeakerDialog">
            重命名发言人
          </el-button>
        </div>
      </template>

      <el-space wrap>
        <el-tag
          v-for="speaker in meetingStore.speakers"
          :key="speaker.speaker_pk"
          size="large"
        >
          {{ speaker.speaker_name }}
        </el-tag>
      </el-space>
    </el-card>

    <!-- AI 纪要 -->
    <el-card v-if="meetingStore.minutes" class="minutes-card">
      <template #header>
        <span>AI 生成纪要</span>
      </template>

      <!-- 摘要 -->
      <div class="section">
        <h3>📝 会议摘要</h3>
        <p>{{ meetingStore.minutes.summary || '（无摘要）' }}</p>
      </div>

      <!-- 关键词 -->
      <div class="section">
        <h3>🔑 关键词</h3>
        <el-space wrap v-if="meetingStore.minutes.keywords && meetingStore.minutes.keywords.length > 0">
          <el-tag
            v-for="(keyword, index) in meetingStore.minutes.keywords"
            :key="index"
          >
            {{ keyword }}
          </el-tag>
        </el-space>
        <p v-else>（无关键词）</p>
      </div>

      <!-- 待办事项 -->
      <div class="section">
        <h3>✅ 待办事项</h3>
        <el-table
          v-if="meetingStore.minutes.todos && meetingStore.minutes.todos.length > 0"
          :data="meetingStore.minutes.todos"
          border
        >
          <el-table-column prop="content" label="事项" />
          <el-table-column prop="owner" label="负责人" width="150">
            <template #default="{ row }">
              {{ row.owner || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="deadline" label="截止时间" width="200">
            <template #default="{ row }">
              {{ row.deadline || '-' }}
            </template>
          </el-table-column>
        </el-table>
        <p v-else>（无待办事项）</p>
      </div>

      <!-- 发言人总结 -->
      <div class="section">
        <h3>👥 发言人总结</h3>
        <div v-if="meetingStore.minutes.speaker_summary && Object.keys(meetingStore.minutes.speaker_summary).length > 0">
          <div
            v-for="(summary, speakerId) in meetingStore.minutes.speaker_summary"
            :key="speakerId"
            class="speaker-summary"
          >
            <strong>{{ getSpeakerName(speakerId) }}:</strong>
            <span>{{ summary }}</span>
          </div>
        </div>
        <p v-else>（无发言人总结）</p>
      </div>
    </el-card>

    <!-- 转写文本 -->
    <el-card v-if="meetingStore.transcripts.length > 0" class="transcripts-card">
      <template #header>
        <span>📄 完整转写文本</span>
      </template>

      <div class="transcript-list">
        <div
          v-for="transcript in meetingStore.transcripts"
          :key="transcript.transcript_id"
          class="transcript-item"
        >
          <div class="transcript-time">
            {{ formatTimestamp(transcript.start_time) }} - {{ formatTimestamp(transcript.end_time) }}
          </div>
          <div class="transcript-speaker">
            <el-tag size="small">{{ getSpeakerName(transcript.speaker_id) }}</el-tag>
          </div>
          <div class="transcript-content">
            {{ transcript.content }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 发言人重命名对话框 -->
    <el-dialog
      v-model="showSpeakerDialog"
      title="重命名发言人"
      width="500px"
    >
      <el-form label-width="120px">
        <el-form-item
          v-for="speaker in speakerRenames"
          :key="speaker.speaker_id"
          :label="speaker.speaker_id"
        >
          <el-input v-model="speaker.speaker_name" placeholder="输入新名称" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showSpeakerDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRenameSpeakers">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeetingStore } from '@/store/meeting'
import { triggerProcess } from '@/api/meeting'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { createPoller, isProcessingStatus } from '@/utils/poll'
import { formatTimestamp } from '@/utils/download'

const route = useRoute()
const router = useRouter()
const meetingStore = useMeetingStore()

const meetingId = ref(parseInt(route.params.id))
const showSpeakerDialog = ref(false)
const speakerRenames = ref([])

let poller = null

const isProcessing = computed(() => {
  return meetingStore.currentMeeting && isProcessingStatus(meetingStore.currentMeeting.status)
})

const getStatusType = (status) => {
  const typeMap = {
    uploaded: 'info',
    transcribing: 'warning',
    transcribed: 'primary',
    summarizing: 'warning',
    done: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    uploaded: '已上传',
    transcribing: '转写中',
    transcribed: '已转写',
    summarizing: '生成中',
    done: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const getSpeakerName = (speakerId) => {
  const speaker = meetingStore.speakers.find(s => s.speaker_id === speakerId)
  return speaker ? speaker.speaker_name : speakerId
}

const handleBack = () => {
  router.push('/')
}

const handleRefresh = () => {
  loadMeetingDetail()
}

const handleProcess = async () => {
  try {
    const response = await triggerProcess(meetingId.value)

    if (response.code === 200) {
      ElMessage.success('处理已启动')
      loadMeetingDetail()
      startPolling()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('启动失败: ' + error.message)
  }
}

const handleDownloadMarkdown = async () => {
  try {
    await meetingStore.downloadMarkdown(
      meetingId.value,
      meetingStore.currentMeeting.title
    )
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
  }
}

const openSpeakerDialog = () => {
  speakerRenames.value = meetingStore.speakers.map(s => ({
    speaker_id: s.speaker_id,
    speaker_name: s.speaker_name
  }))
  showSpeakerDialog.value = true
}

const handleRenameSpeakers = async () => {
  try {
    const response = await meetingStore.updateSpeakers(
      meetingId.value,
      speakerRenames.value
    )

    if (response.code === 200) {
      ElMessage.success('重命名成功')
      showSpeakerDialog.value = false
      loadMeetingDetail()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('重命名失败: ' + error.message)
  }
}

const loadMeetingDetail = async () => {
  try {
    await meetingStore.fetchMeetingDetail(meetingId.value)
  } catch (error) {
    ElMessage.error('加载失败: ' + error.message)
  }
}

const startPolling = () => {
  if (poller && poller.isRunning()) {
    return
  }

  poller = createPoller(
    async () => {
      await loadMeetingDetail()
      return meetingStore.currentMeeting
    },
    (meeting) => {
      return isProcessingStatus(meeting.status)
    },
    5000
  )

  poller.start()
}

const stopPolling = () => {
  if (poller) {
    poller.stop()
  }
}

onMounted(async () => {
  await loadMeetingDetail()

  if (isProcessing.value) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
  meetingStore.clearCurrentMeeting()
})
</script>

<style scoped>
.meeting-detail-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.info-card,
.speakers-card,
.minutes-card,
.transcripts-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section {
  margin-bottom: 30px;
}

.section h3 {
  margin-bottom: 15px;
  color: #303133;
}

.section p {
  line-height: 1.8;
  color: #606266;
}

.speaker-summary {
  margin-bottom: 10px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.speaker-summary strong {
  color: #409eff;
  margin-right: 10px;
}

.transcript-list {
  max-height: 600px;
  overflow-y: auto;
}

.transcript-item {
  display: flex;
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
}

.transcript-item:hover {
  background-color: #f5f7fa;
}

.transcript-time {
  width: 120px;
  color: #909399;
  font-size: 12px;
  flex-shrink: 0;
}

.transcript-speaker {
  width: 100px;
  flex-shrink: 0;
}

.transcript-content {
  flex: 1;
  line-height: 1.8;
  color: #303133;
}
</style>
