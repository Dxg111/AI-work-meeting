<template>
  <div class="page">
    <el-card>
      <div class="toolbar">
        <div class="toolbar-title">
          <h2>部门管理</h2>
          <span>共 {{ total }} 个部门</span>
        </div>
        <el-button type="primary" @click="openCreate">新增部门</el-button>
      </div>

      <div class="filters">
        <el-input
          v-model="keyword"
          placeholder="搜索部门名称"
          clearable
          style="width: 280px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button type="primary" plain @click="handleSearch">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="dept_id" label="ID" width="80" />
        <el-table-column prop="dept_name" label="部门名称" min-width="180" />
        <el-table-column prop="dept_desc" label="部门描述" min-width="220" show-overflow-tooltip />
        <el-table-column prop="user_count" label="用户数" width="100" />
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑部门' : '新增部门'"
      width="480px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="部门名称" prop="dept_name">
          <el-input v-model="form.dept_name" maxlength="100" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="部门描述">
          <el-input
            v-model="form.dept_desc"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="可选"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createDept,
  deleteDept,
  getDeptList,
  updateDept
} from '@/api/org'
import { formatDateTime } from '@/utils/datetime'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const form = reactive({
  dept_name: '',
  dept_desc: ''
})

const rules = {
  dept_name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const fetchList = async () => {
  loading.value = true
  try {
    const response = await getDeptList({
      page: page.value,
      page_size: pageSize.value,
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

const handleSearch = () => {
  page.value = 1
  fetchList()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  page.value = 1
  fetchList()
}

const resetForm = () => {
  form.dept_name = ''
  form.dept_desc = ''
  editingId.value = null
  formRef.value?.clearValidate()
}

const openCreate = () => {
  editing.value = false
  resetForm()
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = true
  editingId.value = row.dept_id
  form.dept_name = row.dept_name
  form.dept_desc = row.dept_desc || ''
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
    const payload = {
      dept_name: form.dept_name.trim(),
      dept_desc: form.dept_desc?.trim() || null
    }

    if (editing.value) {
      await updateDept(editingId.value, payload)
      ElMessage.success('部门更新成功')
    } else {
      await createDept(payload)
      ElMessage.success('部门创建成功')
    }

    dialogVisible.value = false
    fetchList()
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除部门「${row.dept_name}」吗？部门下存在用户时将无法删除。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
  } catch (error) {
    return
  }

  try {
    await deleteDept(row.dept_id)
    ElMessage.success('部门删除成功')
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    fetchList()
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  }
}

onMounted(fetchList)
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
}

.pagination {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}
</style>
