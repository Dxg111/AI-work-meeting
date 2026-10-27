<template>
  <div class="meeting-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>会议列表</span>
          <el-button type="primary" @click="testHealth">测试后端连接</el-button>
        </div>
      </template>

      <el-empty v-if="!connected" description="点击上方按钮测试后端连接..." />

      <div v-else>
        <el-result
          icon="success"
          title="连接成功！"
          sub-title="前后端已成功连接，阶段0验收通过"
        >
          <template #extra>
            <el-space>
              <el-button type="primary" @click="testHealth">重新测试</el-button>
              <el-button @click="viewDocs">查看 API 文档</el-button>
            </el-space>
          </template>
        </el-result>

        <el-divider />

        <el-descriptions title="系统信息" :column="2" border>
          <el-descriptions-item label="后端状态">
            <el-tag type="success">运行中</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="API 版本">{{ apiVersion }}</el-descriptions-item>
          <el-descriptions-item label="健康检查接口">
            <el-link type="primary" href="http://localhost:8000/api/health" target="_blank">
              /api/health
            </el-link>
          </el-descriptions-item>
          <el-descriptions-item label="API 文档">
            <el-link type="primary" href="http://localhost:8000/docs" target="_blank">
              /docs (Swagger)
            </el-link>
          </el-descriptions-item>
        </el-descriptions>

        <el-alert
          title="阶段 0 已完成"
          type="success"
          description="后端 FastAPI 框架、前端 Vue3 脚手架、前后端连接测试均已通过。准备进入阶段 1 开发。"
          :closable="false"
          style="margin-top: 20px"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { healthCheck } from '@/api/meeting'

const connected = ref(false)
const apiVersion = ref('1.0.0')

async function testHealth() {
  try {
    const result = await healthCheck()
    console.log('健康检查结果:', result)

    if (result && result.status === 'healthy') {
      ElMessage.success('后端服务连接成功！')
      connected.value = true
      apiVersion.value = result.version || '1.0.0'
    } else {
      ElMessage.warning('后端返回数据格式异常')
      connected.value = false
    }
  } catch (error) {
    console.error('健康检查失败:', error)
    ElMessage.error('后端服务连接失败，请检查后端是否启动（http://localhost:8000）')
    connected.value = false
  }
}

function viewDocs() {
  window.open('http://localhost:8000/docs', '_blank')
}
</script>

<style scoped>
.meeting-list {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}
</style>
