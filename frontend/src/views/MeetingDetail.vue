<template>
  <div class="meeting-detail">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>会议详情</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>
      <el-empty description="会议详情页面，将在阶段 1 完善" />
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped>
.meeting-detail {
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
