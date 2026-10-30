<template>
  <div id="app">
    <el-container>
      <el-header v-if="!isLoginPage" height="60px">
        <div class="header-content">
          <div class="header-left">
            <h1>智能会议纪要助手系统</h1>

            <nav class="nav">
              <router-link
                to="/stats"
                class="nav-link"
                :class="{ active: route.path === '/stats' }"
              >
                统计首页
              </router-link>
              <router-link
                to="/"
                class="nav-link"
                :class="{ active: isMeetingPage }"
              >
                会议列表
              </router-link>
              <router-link
                v-if="authStore.isSuperAdmin"
                to="/depts"
                class="nav-link"
                :class="{ active: route.path === '/depts' }"
              >
                部门管理
              </router-link>
              <router-link
                v-if="authStore.isSuperAdmin"
                to="/users"
                class="nav-link"
                :class="{ active: route.path === '/users' }"
              >
                用户管理
              </router-link>
            </nav>
          </div>

          <el-dropdown
            v-if="authStore.isLoggedIn"
            trigger="click"
            @command="handleCommand"
          >
            <span class="user-info">
              <el-avatar :size="26" :src="authStore.user?.avatar_url" class="header-avatar">
                <el-icon><UserFilled /></el-icon>
              </el-avatar>
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
                <el-dropdown-item command="profile" :icon="User">
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="logout" :icon="SwitchButton" divided>
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
import { ArrowDown, SwitchButton, User, UserFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isLoginPage = computed(() => route.path === '/login')
const isMeetingPage = computed(
  () => route.path === '/' || route.path.startsWith('/meeting/')
)

onMounted(async () => {
  // 每次进入应用都刷新一次当前用户，确保角色、禁用状态、首次改密标记是最新的
  if (authStore.token) {
    try {
      await authStore.fetchMe()
    } catch (error) {
      // 401 已由 Axios 拦截器统一处理
    }
  }

  // 首次登录/重置密码后，强制进入个人中心修改密码
  if (authStore.user?.must_change_password && route.path !== '/profile') {
    router.replace('/profile')
  }
})

const handleCommand = async (command) => {
  if (command === 'profile') {
    router.push('/profile')
    return
  }

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

.header-left {
  display: flex;
  align-items: center;
  gap: 32px;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link {
  color: rgba(255, 255, 255, 0.82);
  text-decoration: none;
  font-size: 14px;
  padding: 7px 14px;
  border-radius: 8px;
  transition: background-color 0.2s ease, color 0.2s ease;
  white-space: nowrap;
}

.nav-link:hover,
.nav-link.active {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
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

.header-avatar {
  border: 1px solid rgba(255, 255, 255, 0.65);
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  flex-shrink: 0;
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
