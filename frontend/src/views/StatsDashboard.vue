<template>
  <div class="stats-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>{{ isSuperAdmin ? '全局统计' : '我的统计' }}</h2>
        <p class="subtitle">
          {{ isSuperAdmin ? '全企业会议数据概览' : '仅统计您创建的会议' }}
        </p>
      </div>
      <el-button :loading="loading" @click="loadStats">刷新数据</el-button>
    </div>

    <!-- KPI 卡片 -->
    <div class="kpi-grid">
      <div v-for="item in kpis" :key="item.key" class="kpi-card">
        <div class="kpi-icon" :style="{ color: item.color, background: item.bg }">
          <el-icon :size="20"><component :is="item.icon" /></el-icon>
        </div>
        <div class="kpi-body">
          <div class="kpi-value">{{ item.value }}</div>
          <div class="kpi-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="10">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>会议状态分布</span>
              <span class="chart-hint">共 {{ cards.total }} 场</span>
            </div>
          </template>

          <div v-if="hasStatusData" ref="statusChartRef" class="chart"></div>
          <el-empty v-else description="暂无会议数据" :image-size="72" />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="14">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>近 7 天新增会议</span>
              <span class="chart-hint">按创建时间统计</span>
            </div>
          </template>

          <div ref="weekChartRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="isSuperAdmin" class="chart-card dept-card">
      <template #header>
        <div class="chart-header">
          <span>各部门会议数量</span>
          <span class="chart-hint">全部部门</span>
        </div>
      </template>

      <div
        v-if="deptData.length"
        ref="deptChartRef"
        class="chart"
        :style="{ height: deptChartHeight + 'px' }"
      ></div>
      <el-empty v-else description="暂无部门数据" :image-size="72" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import {
  CircleCheck,
  CircleClose,
  Document,
  Loading,
  Timer
} from '@element-plus/icons-vue'
import { getStats } from '@/api/stats'
import { useAuthStore } from '@/store/auth'

echarts.use([
  BarChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer
])

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.isSuperAdmin)

const loading = ref(false)
const data = ref(null)

const statusChartRef = ref(null)
const weekChartRef = ref(null)
const deptChartRef = ref(null)

const chartColors = {
  blue: '#2a78d6',
  blueDark: '#256abf',
  green: '#0ca30c',
  red: '#d03b3b',
  textSecondary: '#52514e',
  muted: '#898781',
  grid: '#e1e0d9',
  axis: '#c3c2b7'
}

// 饼图配色：已通过色盲/对比度校验（直接标签 + 图例作为辅助编码）
const pieColors = {
  done: '#1baf7a',
  processing: '#eda100',
  pending: '#2a78d6',
  failed: '#e34948'
}

const cards = computed(() => data.value?.cards || {
  total: 0,
  done: 0,
  processing: 0,
  failed: 0,
  total_duration: 0
})

const formatDuration = (seconds) => {
  const value = Number(seconds) || 0
  if (value <= 0) return '0 分钟'

  const hours = Math.floor(value / 3600)
  const minutes = Math.floor((value % 3600) / 60)
  const secs = value % 60

  if (hours > 0) return `${hours} 小时 ${minutes} 分钟`
  if (minutes > 0) return `${minutes} 分钟`
  return `${secs} 秒`
}

const kpis = computed(() => [
  {
    key: 'total',
    label: '会议总数',
    value: cards.value.total,
    icon: Document,
    color: chartColors.blue,
    bg: 'rgba(42, 120, 214, 0.12)'
  },
  {
    key: 'done',
    label: '已完成',
    value: cards.value.done,
    icon: CircleCheck,
    color: chartColors.green,
    bg: 'rgba(12, 163, 12, 0.12)'
  },
  {
    key: 'processing',
    label: '处理中 / 待处理',
    value: cards.value.processing,
    icon: Loading,
    color: '#a8760a',
    bg: 'rgba(250, 178, 25, 0.16)'
  },
  {
    key: 'failed',
    label: '失败',
    value: cards.value.failed,
    icon: CircleClose,
    color: chartColors.red,
    bg: 'rgba(208, 59, 59, 0.12)'
  },
  {
    key: 'duration',
    label: '累计音频时长',
    value: formatDuration(cards.value.total_duration),
    icon: Timer,
    color: '#6250d6',
    bg: 'rgba(98, 80, 214, 0.12)'
  }
])

const statusGroups = computed(() => {
  const distribution = data.value?.status_distribution || []
  const map = Object.fromEntries(
    distribution.map(item => [item.status, item.count])
  )

  return [
    { name: '已完成', value: map.done || 0, color: pieColors.done },
    {
      name: '处理中',
      value: (map.transcribing || 0) + (map.summarizing || 0),
      color: pieColors.processing
    },
    {
      name: '待处理',
      value: (map.uploaded || 0) + (map.transcribed || 0),
      color: pieColors.pending
    },
    { name: '失败', value: map.failed || 0, color: pieColors.failed }
  ]
})

const hasStatusData = computed(() =>
  statusGroups.value.some(item => item.value > 0)
)

const weekData = computed(() => data.value?.last_7_days || [])
const weekLabels = computed(() => weekData.value.map(item => item.date.slice(5)))
const weekCounts = computed(() => weekData.value.map(item => item.count))

const deptData = computed(() => {
  const list = [...(data.value?.dept_distribution || [])]
  return list.sort((a, b) => b.count - a.count)
})

const deptChartHeight = computed(() =>
  Math.max(260, deptData.value.length * 46 + 40)
)

const getChart = (element) => {
  if (!element) return null
  return echarts.getInstanceByDom(element) || echarts.init(element)
}

const renderStatusChart = () => {
  const element = statusChartRef.value
  if (!element) return

  const items = statusGroups.value.filter(item => item.value > 0)
  const chart = getChart(element)

  chart.setOption({
    color: items.map(item => item.color),
    tooltip: {
      trigger: 'item',
      formatter: '{b}：{c} 场（{d}%）'
    },
    legend: {
      bottom: 0,
      left: 'center',
      icon: 'circle',
      itemWidth: 9,
      itemHeight: 9,
      itemGap: 18,
      textStyle: { color: chartColors.textSecondary, fontSize: 12 }
    },
    series: [
      {
        type: 'pie',
        radius: ['46%', '68%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: '#ffffff',
          borderWidth: 2,
          borderRadius: 4
        },
        label: {
          color: chartColors.textSecondary,
          fontSize: 12,
          lineHeight: 18,
          formatter: '{b}\n{c} 场'
        },
        labelLine: {
          length: 10,
          length2: 8,
          lineStyle: { color: chartColors.axis }
        },
        data: items.map(item => ({ name: item.name, value: item.value }))
      }
    ]
  }, true)
}

const renderWeekChart = () => {
  const element = weekChartRef.value
  if (!element) return

  const chart = getChart(element)

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = params[0]
        return `${item.axisValue}<br/>新增会议：${item.value} 场`
      }
    },
    grid: { left: 12, right: 18, top: 30, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: weekLabels.value,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: chartColors.axis } },
      axisLabel: { color: chartColors.muted, fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: chartColors.grid } },
      axisLabel: { color: chartColors.muted, fontSize: 12 }
    },
    series: [
      {
        type: 'bar',
        data: weekCounts.value,
        barMaxWidth: 28,
        itemStyle: {
          color: chartColors.blue,
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: { color: chartColors.blueDark }
        },
        label: {
          show: true,
          position: 'top',
          color: chartColors.textSecondary,
          fontSize: 12,
          formatter: (params) => (params.value ? params.value : '')
        }
      }
    ]
  }, true)
}

const renderDeptChart = () => {
  if (!isSuperAdmin.value) return
  const element = deptChartRef.value
  if (!element) return

  const chart = getChart(element)
  const items = deptData.value

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = params[0]
        return `${item.axisValue}<br/>会议数量：${item.value} 场`
      }
    },
    grid: { left: 10, right: 30, top: 12, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: chartColors.grid } },
      axisLabel: { color: chartColors.muted, fontSize: 12 }
    },
    yAxis: {
      type: 'category',
      data: items.map(item => item.dept_name),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: chartColors.axis } },
      axisLabel: { color: chartColors.textSecondary, fontSize: 12 }
    },
    series: [
      {
        type: 'bar',
        data: items.map(item => item.count),
        barMaxWidth: 22,
        itemStyle: {
          color: chartColors.blue,
          borderRadius: [0, 4, 4, 0]
        },
        emphasis: {
          itemStyle: { color: chartColors.blueDark }
        },
        label: {
          show: true,
          position: 'right',
          color: chartColors.textSecondary,
          fontSize: 12
        }
      }
    ]
  }, true)

  chart.resize()
}

const renderCharts = async () => {
  await nextTick()
  renderStatusChart()
  renderWeekChart()
  renderDeptChart()
}

const loadStats = async () => {
  loading.value = true
  try {
    const response = await getStats()
    data.value = response.data
    await renderCharts()
  } catch (error) {
    // 错误提示由 Axios 拦截器处理
  } finally {
    loading.value = false
  }
}

const resizeCharts = () => {
  ;[statusChartRef, weekChartRef, deptChartRef].forEach(refItem => {
    const element = refItem.value
    if (!element) return
    echarts.getInstanceByDom(element)?.resize()
  })
}

onMounted(async () => {
  window.addEventListener('resize', resizeCharts)
  await loadStats()
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  ;[statusChartRef, weekChartRef, deptChartRef].forEach(refItem => {
    const element = refItem.value
    if (!element) return
    echarts.getInstanceByDom(element)?.dispose()
  })
})
</script>

<style scoped>
.stats-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 600;
  color: #0b0b0b;
}

.subtitle {
  margin: 0;
  color: #52514e;
  font-size: 13px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #ffffff;
  border: 1px solid rgba(11, 11, 11, 0.08);
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(15, 40, 80, 0.05);
}

.kpi-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-body {
  min-width: 0;
}

.kpi-value {
  font-size: 24px;
  font-weight: 650;
  line-height: 1.2;
  color: #0b0b0b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-label {
  margin-top: 4px;
  font-size: 12px;
  color: #52514e;
  white-space: nowrap;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chart-header span:first-child {
  font-size: 15px;
  font-weight: 600;
  color: #0b0b0b;
}

.chart-hint {
  font-size: 12px;
  color: #898781;
}

.chart {
  width: 100%;
  height: 320px;
}

.dept-card .chart {
  height: auto;
  min-height: 260px;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart {
    height: 280px;
  }
}
</style>
