/**
 * 会议状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMeetingList, getMeetingDetail } from '@/api/meeting'

export const useMeetingStore = defineStore('meeting', () => {
  // 会议列表
  const meetingList = ref([])
  const total = ref(0)
  const loading = ref(false)

  // 当前会议详情
  const currentMeeting = ref(null)
  const transcripts = ref([])
  const speakers = ref([])
  const minutes = ref(null)

  /**
   * 获取会议列表
   */
  async function fetchMeetingList(params) {
    loading.value = true
    try {
      const data = await getMeetingList(params)
      meetingList.value = data.list
      total.value = data.total
      return data
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取会议详情
   */
  async function fetchMeetingDetail(id) {
    loading.value = true
    try {
      const data = await getMeetingDetail(id)
      currentMeeting.value = data.meeting
      transcripts.value = data.transcripts || []
      speakers.value = data.speakers || []
      minutes.value = data.minutes || null
      return data
    } finally {
      loading.value = false
    }
  }

  /**
   * 清空当前会议
   */
  function clearCurrentMeeting() {
    currentMeeting.value = null
    transcripts.value = []
    speakers.value = []
    minutes.value = null
  }

  return {
    meetingList,
    total,
    loading,
    currentMeeting,
    transcripts,
    speakers,
    minutes,
    fetchMeetingList,
    fetchMeetingDetail,
    clearCurrentMeeting,
  }
})
