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
        <el-descriptions-item label="创建人">
          {{ meetingStore.currentMeeting.creator_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="所属部门">
          {{ meetingStore.currentMeeting.dept_name || '未分配' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(meetingStore.currentMeeting.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(meetingStore.currentMeeting.updated_at) }}
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
          v-if="canEdit && ['uploaded', 'failed', 'transcribed'].includes(meetingStore.currentMeeting.status)"
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
        <el-button
          v-if="meetingStore.minutes"
          type="warning"
          :loading="exportingPdf"
          @click="handleExportPdf"
        >
          导出 PDF
        </el-button>
        <el-button type="info" @click="handleRefresh">
          刷新
        </el-button>

        <el-switch
          v-if="canEdit"
          v-model="shareDept"
          active-text="部门内分享"
          style="margin-left: 12px"
          @change="handleShareChange"
        />
      </div>
    </el-card>

    <!-- 只读分享提示 -->
    <el-alert
      v-if="meetingStore.currentMeeting && meetingStore.currentMeeting.is_shared"
      title="该会议由同部门同事分享，仅可查看和导出，不能修改、删除或重新处理"
      type="info"
      :closable="false"
      show-icon
      style="margin-top: 20px"
    />

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
          <el-button v-if="canEdit" size="small" @click="openSpeakerDialog">
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

    <!-- PDF 导出模板（屏幕外渲染，不显示给用户） -->
    <div ref="pdfTemplate" class="pdf-template">
      <h1>{{ meetingStore.currentMeeting?.title || '会议纪要' }}</h1>
      <p class="pdf-meta">
        创建人：{{ meetingStore.currentMeeting?.creator_name || '-' }}
        ｜ 部门：{{ meetingStore.currentMeeting?.dept_name || '未分配' }}
        ｜ 时间：{{ formatDateTime(meetingStore.currentMeeting?.created_at) }}
      </p>

      <template v-if="meetingStore.minutes">
        <h2>会议摘要</h2>
        <p>{{ meetingStore.minutes.summary || '（无摘要）' }}</p>

        <h2>关键词</h2>
        <p>{{ (meetingStore.minutes.keywords || []).join('、') || '（无关键词）' }}</p>

        <h2>待办事项</h2>
        <table v-if="meetingStore.minutes.todos && meetingStore.minutes.todos.length">
          <thead>
            <tr>
              <th>事项</th>
              <th>负责人</th>
              <th>截止时间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(todo, index) in meetingStore.minutes.todos"
              :key="index"
            >
              <td>{{ todo.content }}</td>
              <td>{{ todo.owner || '-' }}</td>
              <td>{{ todo.deadline || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else>（无待办事项）</p>

        <h2>发言人总结</h2>
        <div
          v-if="meetingStore.minutes.speaker_summary && Object.keys(meetingStore.minutes.speaker_summary).length > 0"
        >
          <p
            v-for="(summary, speakerId) in meetingStore.minutes.speaker_summary"
            :key="speakerId"
          >
            <strong>{{ getSpeakerName(speakerId) }}：</strong>{{ summary }}
          </p>
        </div>
        <p v-else>（无发言人总结）</p>
      </template>

      <p class="pdf-footer">由智能会议纪要助手生成</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMeetingStore } from '@/store/meeting'
import { triggerProcess } from '@/api/meeting'
import { ElLoading, ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { createPoller, isProcessingStatus, isWaitingForAutoProcess } from '@/utils/poll'
import { formatTimestamp } from '@/utils/download'
import { formatDateTime } from '@/utils/datetime'

const route = useRoute()
const router = useRouter()
const meetingStore = useMeetingStore()

const meetingId = ref(parseInt(route.params.id))
const showSpeakerDialog = ref(false)
const speakerRenames = ref([])
const shareDept = ref(false)
const exportingPdf = ref(false)
const pdfTemplate = ref(null)

let poller = null

const isProcessing = computed(() => {
  const meeting = meetingStore.currentMeeting
  return !!meeting && (
    isProcessingStatus(meeting.status) ||
    isWaitingForAutoProcess(meeting)
  )
})

const canEdit = computed(() => !!meetingStore.currentMeeting?.can_edit)

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
  if (!canEdit.value) {
    ElMessage.warning('无权操作该会议')
    return
  }

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

const safeFilename = (title) => {
  return (title || '会议纪要').replace(/[\\/:*?"<>|]/g, '_')
}

const handleExportPdf = async () => {
  if (!pdfTemplate.value) {
    ElMessage.warning('暂无可导出的纪要内容')
    return
  }

  exportingPdf.value = true
  let pdfClone = null
  let loadingInstance = null

  try {
    // 直接使用 html2pdf 的底层库，绕开 html2pdf 内部的离屏容器。
    // 该容器在部分环境下会被 html2canvas 裁剪，导致导出空白页。
    const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf')
    ])

    pdfClone = pdfTemplate.value.cloneNode(true)
    Object.assign(pdfClone.style, {
      position: 'fixed',
      left: '0',
      top: '0',
      width: '794px',
      minHeight: '1px',
      padding: '40px 48px',
      background: '#ffffff',
      color: '#0b0b0b',
      zIndex: '1500',
      pointerEvents: 'none',
      display: 'block',
      boxSizing: 'border-box'
    })
    document.body.appendChild(pdfClone)

    loadingInstance = ElLoading.service({
      lock: true,
      text: '正在生成 PDF...',
      background: 'rgba(0, 0, 0, 0.55)'
    })

    // 等待克隆节点完成布局
    await new Promise(resolve => {
      requestAnimationFrame(() => requestAnimationFrame(resolve))
    })

    // 直接对可见模板截图，不再经过 html2pdf 的离屏容器
    const canvas = await html2canvas(pdfClone, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      scrollX: 0,
      scrollY: 0,
      logging: false
    })

    // 检查画布是否全白，避免把空白图写进 PDF
    const ctx = canvas.getContext('2d')
    const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data
    let nonWhiteSamples = 0
    // 稀疏采样，避免遍历上百万像素
    for (let i = 0; i < pixels.length; i += 4 * 50) {
      if (pixels[i] < 245 || pixels[i + 1] < 245 || pixels[i + 2] < 245) {
        nonWhiteSamples += 1
        if (nonWhiteSamples > 20) break
      }
    }
    if (nonWhiteSamples < 20) {
      throw new Error('导出内容为空（画布全白），请检查纪要模板')
    }

    const filename = `${safeFilename(meetingStore.currentMeeting?.title)}.pdf`
    const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' })

    const pageWidth = 210
    const pageHeight = 297
    const margin = 10
    const contentWidth = pageWidth - margin * 2
    const contentHeight = pageHeight - margin * 2
    const pxPerMm = canvas.width / contentWidth
    const pageHeightPx = Math.max(1, Math.floor(contentHeight * pxPerMm))

    let offset = 0
    let pageIndex = 0

    while (offset < canvas.height) {
      const sliceHeight = Math.min(pageHeightPx, canvas.height - offset)
      const pageCanvas = document.createElement('canvas')
      pageCanvas.width = canvas.width
      pageCanvas.height = sliceHeight

      const pageCtx = pageCanvas.getContext('2d')
      pageCtx.fillStyle = '#ffffff'
      pageCtx.fillRect(0, 0, pageCanvas.width, pageCanvas.height)
      pageCtx.drawImage(
        canvas,
        0, offset, canvas.width, sliceHeight,
        0, 0, canvas.width, sliceHeight
      )

      const imgData = pageCanvas.toDataURL('image/jpeg', 0.95)
      if (pageIndex > 0) {
        pdf.addPage()
      }

      pdf.addImage(
        imgData,
        'JPEG',
        margin,
        margin,
        contentWidth,
        sliceHeight / pxPerMm,
        undefined,
        'FAST'
      )

      offset += sliceHeight
      pageIndex += 1
    }

    pdf.save(filename)
    ElMessage.success('PDF 导出成功')
  } catch (error) {
    console.error('PDF 导出失败:', error)
    ElMessage.error(`PDF 导出失败: ${error?.message || '未知错误'}`)
  } finally {
    loadingInstance?.close()
    if (pdfClone && pdfClone.parentNode) {
      pdfClone.parentNode.removeChild(pdfClone)
    }
    exportingPdf.value = false
  }
}

const openSpeakerDialog = () => {
  speakerRenames.value = meetingStore.speakers.map(s => ({
    speaker_id: s.speaker_id,
    speaker_name: s.speaker_name
  }))
  showSpeakerDialog.value = true
}

const handleShareChange = async (value) => {
  if (!canEdit.value) {
    shareDept.value = !value
    return
  }

  try {
    await meetingStore.updateShare(meetingId.value, value)
    ElMessage.success(value ? '已开启部门内分享' : '已关闭部门内分享')
  } catch (error) {
    // 失败时回滚开关状态
    shareDept.value = !value
  }
}

const handleRenameSpeakers = async () => {
  if (!canEdit.value) {
    ElMessage.warning('无权操作该会议')
    return
  }

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
    shareDept.value = !!meetingStore.currentMeeting?.share_dept
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
      return isProcessingStatus(meeting.status) || isWaitingForAutoProcess(meeting)
    },
    5000,
    120 // 最多轮询 10 分钟，避免异常情况下无限刷新
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

<style>
/* PDF 导出模板：屏幕外渲染，供 html2pdf 截图 */
.pdf-template {
  position: fixed;
  left: -10000px;
  top: 0;
  width: 794px;
  padding: 40px 48px;
  background: #ffffff;
  color: #0b0b0b;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  font-size: 14px;
  line-height: 1.8;
  box-sizing: border-box;
}

.pdf-template h1 {
  margin: 0 0 8px;
  font-size: 26px;
  line-height: 1.4;
}

.pdf-template .pdf-meta {
  margin: 0 0 28px;
  color: #52514e;
  font-size: 12px;
}

.pdf-template h2 {
  margin: 24px 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e1e0d9;
  font-size: 17px;
  page-break-after: avoid;
}

.pdf-template p {
  margin: 0 0 8px;
}

.pdf-template table {
  width: 100%;
  margin-top: 8px;
  border-collapse: collapse;
  font-size: 13px;
}

.pdf-template th,
.pdf-template td {
  border: 1px solid #d9d9d9;
  padding: 8px 10px;
  text-align: left;
}

.pdf-template th {
  background: #f5f7fa;
  font-weight: 600;
}

.pdf-template .pdf-footer {
  margin-top: 36px;
  padding-top: 12px;
  border-top: 1px solid #e1e0d9;
  color: #898781;
  font-size: 11px;
  text-align: center;
}
</style>
