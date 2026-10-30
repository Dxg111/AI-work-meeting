<template>
  <div class="meeting-list-container">
    <!-- 顶部操作栏 -->
    <el-card class="header-card">
      <div class="header-actions">
        <h2>会议列表</h2>
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传会议
        </el-button>
      </div>

      <!-- 搜索筛选 -->
      <div class="filter-bar">
        <el-input
          v-model="searchTitle"
          placeholder="搜索会议标题"
          clearable
          style="width: 300px"
          @change="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="filterStatus"
          placeholder="筛选状态"
          clearable
          style="width: 150px; margin-left: 10px"
          @change="handleSearch"
        >
          <el-option label="已上传" value="uploaded" />
          <el-option label="转写中" value="transcribing" />
          <el-option label="已转写" value="transcribed" />
          <el-option label="生成中" value="summarizing" />
          <el-option label="已完成" value="done" />
          <el-option label="失败" value="failed" />
        </el-select>

        <el-select
          v-if="authStore.isSuperAdmin"
          v-model="filterDept"
          placeholder="筛选部门"
          clearable
          style="width: 160px; margin-left: 10px"
          @change="handleSearch"
        >
          <el-option
            v-for="dept in deptOptions"
            :key="dept.dept_id"
            :label="dept.dept_name"
            :value="dept.dept_id"
          />
        </el-select>

        <el-select
          v-if="authStore.isSuperAdmin"
          v-model="filterUser"
          placeholder="筛选创建人"
          clearable
          filterable
          style="width: 180px; margin-left: 10px"
          @change="handleSearch"
        >
          <el-option
            v-for="user in userOptions"
            :key="user.user_id"
            :label="user.nickname || user.username"
            :value="user.user_id"
          />
        </el-select>
      </div>
    </el-card>

    <!-- 会议列表 -->
    <el-card class="list-card" v-loading="meetingStore.loading">
      <el-table
        :data="meetingStore.meetingList"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="meeting_id" label="ID" width="80" />
        <el-table-column prop="title" label="会议标题" min-width="200" />
        <el-table-column prop="creator_name" label="创建人" width="120" />
        <el-table-column prop="dept_name" label="部门" width="120" />
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
            <el-tag
              v-if="row.is_shared"
              type="info"
              size="small"
              style="margin-left: 4px"
            >
              只读
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.can_edit && ['uploaded', 'failed', 'transcribed'].includes(row.status)"
              type="primary"
              size="small"
              @click.stop="handleProcess(row)"
            >
              处理
            </el-button>
            <el-button
              type="success"
              size="small"
              @click.stop="handleViewDetail(row)"
            >
              详情
            </el-button>
            <el-button
              v-if="row.can_edit"
              type="danger"
              size="small"
              @click.stop="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="meetingStore.currentPage"
          v-model:page-size="meetingStore.pageSize"
          :total="meetingStore.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传会议音视频"
      width="500px"
    >
      <el-form :model="uploadForm" label-width="120px">
        <el-form-item label="会议标题" required>
          <el-input v-model="uploadForm.title" placeholder="请输入会议标题" />
        </el-form-item>

        <el-form-item label="音视频文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :file-list="fileList"
            accept=".mp3,.wav,.m4a,.mp4,.avi,.mov"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持格式：mp3, wav, m4a, mp4, avi, mov，大小不超过 500MB
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="自动处理">
          <el-switch v-model="uploadForm.auto_process" />
          <span class="form-tip">开启后上传完成自动进行转写和纪要生成</span>
        </el-form-item>

        <el-form-item label="部门分享">
          <el-switch v-model="uploadForm.share_dept" />
          <span class="form-tip">开启后同部门成员可查看（阶段2功能）</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          @click="handleUpload"
        >
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMeetingStore } from '@/store/meeting'
import { useAuthStore } from '@/store/auth'
import { uploadMeeting } from '@/api/meeting'
import { getDeptOptions, getUserOptions } from '@/api/org'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Search } from '@element-plus/icons-vue'
import { createPoller, isProcessingStatus } from '@/utils/poll'
import { formatDateTime } from '@/utils/datetime'

const router = useRouter()
const meetingStore = useMeetingStore()
const authStore = useAuthStore()

// 搜索筛选
const searchTitle = ref('')
const filterStatus = ref('')
const filterDept = ref(null)
const deptOptions = ref([])
const filterUser = ref(null)
const userOptions = ref([])

// 上传对话框
const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadRef = ref(null)
const fileList = ref([])
const uploadForm = ref({
  title: '',
  file: null,
  auto_process: true,
  share_dept: false
})

// 轮询器
let poller = null

// 获取状态标签类型
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

// 获取状态文本
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

// 搜索
const loadDeptOptions = async () => {
  try {
    const response = await getDeptOptions()
    deptOptions.value = response.data
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  }
}

const loadUserOptions = async () => {
  try {
    const response = await getUserOptions()
    userOptions.value = response.data
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  }
}

const handleSearch = () => {
  meetingStore.fetchMeetingList({
    page: 1,
    title: searchTitle.value,
    status: filterStatus.value,
    dept_id: filterDept.value ?? undefined,
    user_id: filterUser.value ?? undefined
  })
}

// 分页
const handlePageChange = (page) => {
  meetingStore.fetchMeetingList({
    page,
    title: searchTitle.value,
    status: filterStatus.value,
    dept_id: filterDept.value ?? undefined,
    user_id: filterUser.value ?? undefined
  })
}

const handleSizeChange = (size) => {
  meetingStore.fetchMeetingList({
    page: 1,
    page_size: size,
    title: searchTitle.value,
    status: filterStatus.value,
    dept_id: filterDept.value ?? undefined,
    user_id: filterUser.value ?? undefined
  })
}

// 文件选择
const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
  fileList.value = [file]
}

// 上传
const handleUpload = async () => {
  if (!uploadForm.value.title) {
    ElMessage.warning('请输入会议标题')
    return
  }

  if (!uploadForm.value.file) {
    ElMessage.warning('请选择音视频文件')
    return
  }

  uploading.value = true

  try {
    const response = await uploadMeeting(uploadForm.value)

    console.log('上传响应:', response)

    if (response.code === 200) {
      const meetingId = response.data.meeting_id
      console.log('meeting_id:', meetingId)

      ElMessage.success(response.message)

      // 重置表单
      uploadForm.value = {
        title: '',
        file: null,
        auto_process: true,
        share_dept: false
      }
      fileList.value = []

      // 关闭对话框
      showUploadDialog.value = false

      // 使用 nextTick 确保 DOM 更新后再跳转
      await new Promise(resolve => setTimeout(resolve, 100))

      // 跳转到详情页
      console.log('准备跳转到:', `/meeting/${meetingId}`)
      await router.push({ name: 'MeetingDetail', params: { id: meetingId } })
      console.log('跳转完成')
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    console.error('上传错误:', error)
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

// 处理会议
const handleProcess = async (row) => {
  if (!row.can_edit) {
    ElMessage.warning('无权操作该会议')
    return
  }

  try {
    const response = await meetingStore.processMeeting(row.meeting_id)

    if (response.code === 200) {
      ElMessage.success('处理已启动')
      meetingStore.fetchMeetingList()
      startPolling()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('启动失败: ' + error.message)
  }
}

// 查看详情
const handleViewDetail = (row) => {
  router.push(`/meeting/${row.meeting_id}`)
}

// 行点击
const handleRowClick = (row) => {
  handleViewDetail(row)
}

// 删除
const handleDelete = async (row) => {
  if (!row.can_edit) {
    ElMessage.warning('无权操作该会议')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除会议"${row.title}"吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )

    const response = await meetingStore.removeMeeting(row.meeting_id)

    if (response.code === 200) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 启动轮询
const startPolling = () => {
  if (poller && poller.isRunning()) {
    return
  }

  poller = createPoller(
    async () => {
      await meetingStore.fetchMeetingList({
        title: searchTitle.value,
        status: filterStatus.value,
        dept_id: filterDept.value ?? undefined,
        user_id: filterUser.value ?? undefined
      })
      return meetingStore.meetingList
    },
    (meetings) => {
      // 检查是否有处理中的会议
      return meetings.some(m => isProcessingStatus(m.status))
    },
    5000 // 5秒轮询
  )

  poller.start()
}

// 停止轮询
const stopPolling = () => {
  if (poller) {
    poller.stop()
  }
}

// 页面加载
onMounted(async () => {
  if (authStore.isSuperAdmin) {
    loadDeptOptions()
    loadUserOptions()
  }

  await meetingStore.fetchMeetingList()

  // 检查是否有处理中的会议，如果有则启动轮询
  const hasProcessing = meetingStore.meetingList.some(m => isProcessingStatus(m.status))
  if (hasProcessing) {
    startPolling()
  }
})

// 页面卸载
onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.meeting-list-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions h2 {
  margin: 0;
}

.filter-bar {
  display: flex;
  align-items: center;
}

.list-card {
  min-height: 500px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.el-table {
  cursor: pointer;
}
</style>
