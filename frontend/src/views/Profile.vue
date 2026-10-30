<template>
  <div class="profile-page">
    <el-alert
      v-if="mustChangePassword"
      title="首次登录，请先修改初始密码后再使用系统"
      type="warning"
      :closable="false"
      show-icon
      class="force-alert"
    />

    <el-card class="profile-card" v-loading="loading">
      <div class="profile-header">
        <el-upload
          class="avatar-uploader"
          action="#"
          :show-file-list="false"
          :before-upload="beforeAvatarUpload"
          :http-request="handleAvatarUpload"
          accept=".jpg,.jpeg,.png,.gif,.webp"
        >
          <el-avatar :size="96" :src="authStore.user?.avatar_url" class="avatar">
            <el-icon :size="34"><UserFilled /></el-icon>
          </el-avatar>
          <div class="avatar-tip">点击更换头像</div>
        </el-upload>

        <div class="profile-meta">
          <h2>{{ authStore.user?.nickname || authStore.user?.username }}</h2>
          <div class="meta-row">
            <el-tag :type="authStore.isSuperAdmin ? 'warning' : 'info'" size="small">
              {{ roleText }}
            </el-tag>
            <span class="dept">{{ authStore.user?.dept_name || '未分配部门' }}</span>
          </div>
          <p class="meta-sub">用户名：{{ authStore.user?.username }}</p>
          <p class="meta-sub" v-if="authStore.user?.email">邮箱：{{ authStore.user.email }}</p>
        </div>
      </div>
    </el-card>

    <el-card class="tabs-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本资料" name="profile" :disabled="mustChangePassword">
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="90px"
            class="form"
          >
            <el-form-item label="用户名">
              <el-input :model-value="authStore.user?.username" disabled />
            </el-form-item>

            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="profileForm.nickname" maxlength="100" placeholder="请输入昵称" />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" maxlength="100" placeholder="请输入邮箱" />
            </el-form-item>

            <el-form-item label="所属部门">
              <span class="readonly-text">{{ authStore.user?.dept_name || '未分配' }}</span>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="savingProfile" @click="handleSaveProfile">
                保存资料
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="修改密码" name="password">
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="90px"
            class="form"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                show-password
                placeholder="请输入原密码"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                show-password
                placeholder="至少 6 位"
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="changingPassword" @click="handleChangePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const loading = ref(false)
const savingProfile = ref(false)
const changingPassword = ref(false)
const activeTab = ref('profile')

const profileFormRef = ref(null)
const passwordFormRef = ref(null)

const profileForm = reactive({
  nickname: '',
  email: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const roleText = computed(() =>
  authStore.isSuperAdmin ? '超级管理员' : '普通用户'
)

const mustChangePassword = computed(
  () => !!authStore.user?.must_change_password
)

const validateEmail = (rule, value, callback) => {
  if (!value) {
    callback()
    return
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) {
    callback(new Error('邮箱格式不正确'))
    return
  }
  callback()
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const profileRules = {
  email: [{ validator: validateEmail, trigger: 'blur' }]
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const fillProfileForm = () => {
  profileForm.nickname = authStore.user?.nickname || ''
  profileForm.email = authStore.user?.email || ''
}

const beforeAvatarUpload = (file) => {
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowed.includes(file.type)) {
    ElMessage.error('仅支持 jpg、png、gif、webp 格式的图片')
    return false
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像大小不能超过 2MB')
    return false
  }
  return true
}

const handleAvatarUpload = async ({ file }) => {
  try {
    await authStore.uploadAvatar(file)
    ElMessage.success('头像更新成功')
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  }
}

const handleSaveProfile = async () => {
  try {
    await profileFormRef.value.validate()
  } catch (error) {
    return
  }

  savingProfile.value = true
  try {
    await authStore.updateProfile({
      nickname: profileForm.nickname.trim() || null,
      email: profileForm.email.trim() || null
    })
    ElMessage.success('资料更新成功')
    fillProfileForm()
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  } finally {
    savingProfile.value = false
  }
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate()
  } catch (error) {
    return
  }

  changingPassword.value = true
  try {
    await authStore.changePassword(
      passwordForm.old_password,
      passwordForm.new_password
    )

    // 刷新用户信息，清除 must_change_password 标记
    await authStore.fetchMe()

    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordFormRef.value?.clearValidate()
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  } finally {
    changingPassword.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await authStore.fetchMe()
  } catch (error) {
    // 401 已由 Axios 拦截器处理
  } finally {
    loading.value = false
    fillProfileForm()

    if (authStore.user?.must_change_password) {
      activeTab.value = 'password'
    }
  }
})
</script>

<style scoped>
.profile-page {
  max-width: 960px;
  margin: 0 auto;
}

.force-alert {
  margin-bottom: 18px;
}

.profile-card {
  margin-bottom: 20px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 32px;
}

.avatar-uploader {
  text-align: center;
  cursor: pointer;
}

.avatar {
  background: linear-gradient(135deg, #409eff, #2563eb);
  color: #fff;
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.25);
}

.avatar-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

.profile-meta h2 {
  margin: 0 0 12px;
  font-size: 22px;
  color: #303133;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.dept {
  color: #606266;
  font-size: 14px;
}

.meta-sub {
  margin: 4px 0;
  color: #909399;
  font-size: 13px;
}

.tabs-card {
  min-height: 360px;
}

.form {
  max-width: 520px;
  margin-top: 12px;
}

.readonly-text {
  color: #606266;
}

@media (max-width: 640px) {
  .profile-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
}
</style>
