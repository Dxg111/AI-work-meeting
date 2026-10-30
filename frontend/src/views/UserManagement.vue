<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="toolbar-title">
          <h2>用户管理</h2>
          <span>共 {{ total }} 个用户</span>
        </div>
        <el-button type="primary" @click="openCreate">新增用户</el-button>
      </div>

      <div class="filters">
        <el-select
          v-model="filterDept"
          placeholder="全部部门"
          clearable
          style="width: 180px"
          @change="handleSearch"
        >
          <el-option
            v-for="dept in deptOptions"
            :key="dept.dept_id"
            :label="dept.dept_name"
            :value="dept.dept_id"
          />
        </el-select>

        <el-input
          v-model="keyword"
          placeholder="搜索用户名 / 昵称"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />

        <el-button type="primary" plain @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="user_id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="nickname" label="昵称" width="140">
          <template #default="{ row }">{{ row.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'super_admin' ? 'warning' : 'info'" size="small">
              {{ row.role === 'super_admin' ? '超级管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dept_name" label="所属部门" width="150">
          <template #default="{ row }">{{ row.dept_name || '未分配' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              :disabled="row.role === 'super_admin' || isSelf(row)"
              @change="(val) => handleStatusChange(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="openResetPassword(row)">重置密码</el-button>
            <el-button
              v-if="!isSelf(row)"
              link
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchList"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 新增 / 编辑用户 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑用户' : '新增用户'"
      width="520px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            :disabled="editing"
            maxlength="50"
            placeholder="登录名，创建后不可修改"
          />
        </el-form-item>

        <el-form-item v-if="!editing" label="初始密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            maxlength="128"
            placeholder="至少 6 位"
          />
        </el-form-item>

        <el-form-item label="昵称">
          <el-input v-model="form.nickname" maxlength="100" placeholder="可选" />
        </el-form-item>

        <el-form-item label="所属部门">
          <el-select v-model="form.dept_id" placeholder="请选择部门" clearable style="width: 100%">
            <el-option
              v-for="dept in deptOptions"
              :key="dept.dept_id"
              :label="dept.dept_name"
              :value="dept.dept_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="普通用户" value="normal_user" />
            <el-option label="超级管理员" value="super_admin" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="editing" label="账号状态">
          <el-switch
            v-model="form.is_active"
            :disabled="editingRole === 'super_admin'"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="passwordDialogVisible" title="重置密码" width="420px" @closed="resetPasswordForm">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="90px">
        <el-form-item label="用户">
          <span>{{ passwordTarget?.username }}</span>
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            show-password
            maxlength="128"
            placeholder="至少 6 位"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetting" @click="handleResetPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createUser,
  deleteUser,
  getDeptOptions,
  getUserList,
  resetUserPassword,
  updateUser,
  updateUserStatus
} from '@/api/org'
import { formatDateTime } from '@/utils/datetime'
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const filterDept = ref(null)
const deptOptions = ref([])

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref(null)
const editingRole = ref('normal_user')
const formRef = ref(null)

const passwordDialogVisible = ref(false)
const passwordTarget = ref(null)
const passwordFormRef = ref(null)
const passwordForm = reactive({ new_password: '' })

const form = reactive({
  username: '',
  password: '',
  nickname: '',
  dept_id: null,
  role: 'normal_user',
  is_active: true
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度 3-50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码至少 6 位', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const passwordRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码至少 6 位', trigger: 'blur' }
  ]
}

const isSelf = (row) => row.user_id === authStore.user?.user_id

const fetchList = async () => {
  loading.value = true
  try {
    const response = await getUserList({
      page: page.value,
      page_size: pageSize.value,
      dept_id: filterDept.value ?? undefined,
      keyword: keyword.value || undefined
    })
    list.value = response.data.list
    total.value = response.data.total
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  } finally {
    loading.value = false
  }
}

const loadDeptOptions = async () => {
  try {
    const response = await getDeptOptions()
    deptOptions.value = response.data
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  }
}

const handleSearch = () => {
  page.value = 1
  fetchList()
}

const handleReset = () => {
  keyword.value = ''
  filterDept.value = null
  page.value = 1
  fetchList()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  page.value = 1
  fetchList()
}

const resetForm = () => {
  form.username = ''
  form.password = ''
  form.nickname = ''
  form.dept_id = null
  form.role = 'normal_user'
  form.is_active = true
  editingId.value = null
  editingRole.value = 'normal_user'
  formRef.value?.clearValidate()
}

const openCreate = () => {
  editing.value = false
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = true
  editingId.value = row.user_id
  editingRole.value = row.role
  form.username = row.username
  form.password = ''
  form.nickname = row.nickname || ''
  form.dept_id = row.dept_id ?? null
  form.role = row.role
  form.is_active = row.is_active
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  saving.value = true
  try {
    if (editing.value) {
      await updateUser(editingId.value, {
        nickname: form.nickname?.trim() || null,
        dept_id: form.dept_id ?? null,
        role: form.role,
        is_active: form.is_active
      })
      ElMessage.success('用户更新成功')
    } else {
      await createUser({
        username: form.username.trim(),
        password: form.password,
        nickname: form.nickname?.trim() || null,
        dept_id: form.dept_id ?? null,
        role: form.role
      })
      ElMessage.success('用户创建成功')
    }

    dialogVisible.value = false
    fetchList()
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  } finally {
    saving.value = false
  }
}

const handleStatusChange = async (row, isActive) => {
  try {
    await updateUserStatus(row.user_id, isActive)
    row.is_active = isActive
    ElMessage.success(isActive ? '账号已启用' : '账号已禁用')
  } catch (error) {
    // 失败时保持原状态（switch 使用 model-value 受控）
  }
}

const openResetPassword = (row) => {
  passwordTarget.value = row
  passwordForm.new_password = ''
  passwordDialogVisible.value = true
}

const resetPasswordForm = () => {
  passwordForm.new_password = ''
  passwordFormRef.value?.clearValidate()
}

const handleResetPassword = async () => {
  try {
    await passwordFormRef.value.validate()
  } catch (error) {
    return
  }

  resetting.value = true
  try {
    await resetUserPassword(passwordTarget.value.user_id, passwordForm.new_password)
    ElMessage.success('密码重置成功')
    passwordDialogVisible.value = false
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  } finally {
    resetting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除用户「${row.username}」吗？存在会议数据的用户无法删除，建议改用禁用。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
  } catch (error) {
    return
  }

  try {
    await deleteUser(row.user_id)
    ElMessage.success('用户删除成功')
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    fetchList()
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  }
}

onMounted(() => {
  loadDeptOptions()
  fetchList()
})
</script>

<style scoped>
.page {
  max-width: 1400px;
  margin: 0 auto;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.toolbar-title {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.toolbar-title h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.toolbar-title span {
  color: #909399;
  font-size: 13px;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pagination {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}
</style>
