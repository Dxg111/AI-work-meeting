<template>
  <div id="app">
    <el-container>
      <el-header v-if="!isLoginPage" height="60px">
        <div class="header-content">
          <h1>智能会议纪要助手系统</h1>

          <el-dropdown
            v-if="authStore.isLoggedIn"
            trigger="click"
            @command="handleCommand"
          >
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              <span class="user-name">{{ authStore.displayName }}</span>
              <el-tag
                v-if="authStore.isSuperAdmin"
                size="small"
                effect="dark"
                type="warning"
              >
                超级管理员
              </el-tag>
              <el-icon><ArrowDown /></el-icon>
            </span>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout" :icon="SwitchButton">
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main :class="{ 'login-main': isLoginPage }">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, SwitchButton, UserFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isLoginPage = computed(() => route.path === '/login')

onMounted(async () => {
  // 已有 token 但本地没有用户信息时，拉取一次当前用户
  if (authStore.token && !authStore.user) {
    try {
      await authStore.fetchMe()
    } catch (error) {
      // 401 已由 Axios 拦截器统一处理
    }
  }
})

const handleCommand = async (command) => {
  if (command !== 'logout') return

  await authStore.logout()
  ElMessage.success('已退出登录')
  router.replace('/login')
}
</script>

<style scoped>
#app {
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-header {
  background: linear-gradient(90deg, #2f7ed8, #409eff);
  color: white;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 10px rgba(15, 40, 80, 0.18);
}

.header-content {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.user-info {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.14);
}

.user-name {
  font-size: 14px;
}

.el-main {
  background: #f5f7fa;
  padding: 20px;
}

.login-main {
  padding: 0;
  background: transparent;
  overflow: hidden;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
</style>
