<template>
  <div class="login-page">
    <div class="login-panel">
      <div class="brand">
        <div class="brand-mark">AI</div>
        <h1>智能会议纪要助手</h1>
        <p class="brand-subtitle">录音转写 · 智能纪要 · 团队协同</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            size="large"
            placeholder="用户名"
            :prefix-icon="User"
            clearable
            autocomplete="username"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            size="large"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="login-button"
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>
      </el-form>

      <p class="login-hint">初始管理员账号：admin，密码见部署文档</p>
    </div>

    <p class="login-footer">基于 LangChain 的企业级会议纪要系统</p>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (loading.value) return

  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  loading.value = true
  try {
    await authStore.login(form.username.trim(), form.password)
    ElMessage.success('登录成功')

    // 只接受站内路径，避免开放重定向
    const redirect =
      typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
        ? route.query.redirect
        : '/'
    await router.replace(redirect)
  } catch (error) {
    // 错误提示由 Axios 响应拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  background:
    radial-gradient(circle at 15% 15%, rgba(64, 158, 255, 0.35), transparent 42%),
    radial-gradient(circle at 85% 80%, rgba(99, 102, 241, 0.28), transparent 45%),
    linear-gradient(135deg, #0b1f3a 0%, #102a4c 55%, #071426 100%);
}

.login-panel {
  width: 100%;
  max-width: 420px;
  padding: 44px 40px 30px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 18px;
  box-shadow: 0 30px 80px rgba(2, 8, 23, 0.45);
}

.brand {
  text-align: center;
  margin-bottom: 32px;
}

.brand-mark {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #409eff, #2563eb);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.35);
}

.brand h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1f2d3d;
}

.brand-subtitle {
  margin: 8px 0 0;
  font-size: 13px;
  color: #8a94a6;
  letter-spacing: 1px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 4px 14px;
}

.login-button {
  width: 100%;
  margin-top: 8px;
  border-radius: 10px;
  font-size: 16px;
  letter-spacing: 4px;
}

.login-hint {
  margin: 22px 0 0;
  text-align: center;
  font-size: 12px;
  color: #a0a8b8;
}

.login-footer {
  margin: 28px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 1px;
}

@media (max-width: 480px) {
  .login-panel {
    padding: 34px 24px 24px;
  }
}
</style>
