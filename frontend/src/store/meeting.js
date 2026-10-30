/**
 * 会议管理 Pinia Store
 */
import { defineStore } from 'pinia'
import {
  getMeetingList,
  getMeetingDetail,
  deleteMeeting,
  triggerProcess,
  renameSpeakers,
  getMarkdown,
  updateShareSetting
} from '@/api/meeting'

export const useMeetingStore = defineStore('meeting', {
  state: () => ({
    // 会议列表
    meetingList: [],
    total: 0,
    currentPage: 1,
    pageSize: 10,

    // 当前会议详情
    currentMeeting: null,
    transcripts: [],
    speakers: [],
    minutes: null,

    // 加载状态
    loading: false,
    detailLoading: false
  }),

  actions: {
    /**
     * 获取会议列表
     */
    async fetchMeetingList(params = {}) {
      this.loading = true
      try {
        const response = await getMeetingList({
          page: params.page || this.currentPage,
          page_size: params.page_size || this.pageSize,
          title: params.title,
          status: params.status,
          dept_id: params.dept_id,
          user_id: params.user_id
        })

        if (response.code === 200) {
          this.meetingList = response.data.list
          this.total = response.data.total
          this.currentPage = response.data.page
          this.pageSize = response.data.page_size
        }

        return response
      } catch (error) {
        console.error('获取会议列表失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取会议详情
     */
    async fetchMeetingDetail(meetingId) {
      this.detailLoading = true
      try {
        const response = await getMeetingDetail(meetingId)

        if (response.code === 200) {
          this.currentMeeting = response.data.meeting
          this.transcripts = response.data.transcripts
          this.speakers = response.data.speakers
          this.minutes = response.data.minutes
        }

        return response
      } catch (error) {
        console.error('获取会议详情失败:', error)
        throw error
      } finally {
        this.detailLoading = false
      }
    },

    /**
     * 删除会议
     */
    async removeMeeting(meetingId) {
      try {
        const response = await deleteMeeting(meetingId)

        if (response.code === 200) {
          // 从列表中移除
          this.meetingList = this.meetingList.filter(m => m.meeting_id !== meetingId)
          this.total -= 1
        }

        return response
      } catch (error) {
        console.error('删除会议失败:', error)
        throw error
      }
    },

    /**
     * 触发处理
     */
    async processMeeting(meetingId) {
      try {
        const response = await triggerProcess(meetingId)
        return response
      } catch (error) {
        console.error('触发处理失败:', error)
        throw error
      }
    },

    /**
     * 重命名发言人
     */
    async updateSpeakers(meetingId, updates) {
      try {
        const response = await renameSpeakers(meetingId, updates)

        if (response.code === 200) {
          // 更新本地发言人列表
          updates.forEach(update => {
            const speaker = this.speakers.find(s => s.speaker_id === update.speaker_id)
            if (speaker) {
              speaker.speaker_name = update.speaker_name
            }
          })
        }

        return response
      } catch (error) {
        console.error('重命名发言人失败:', error)
        throw error
      }
    },

    /**
     * 修改部门分享设置
     */
    async updateShare(meetingId, shareDept) {
      const response = await updateShareSetting(meetingId, shareDept)

      if (response.code === 200) {
        if (this.currentMeeting && this.currentMeeting.meeting_id === meetingId) {
          this.currentMeeting.share_dept = shareDept ? 1 : 0
        }
        const item = this.meetingList.find(m => m.meeting_id === meetingId)
        if (item) {
          item.share_dept = shareDept ? 1 : 0
        }
      }

      return response
    },

    /**
     * 下载 Markdown
     */
    async downloadMarkdown(meetingId, title) {
      try {
        const response = await getMarkdown(meetingId)

        if (response.code === 200) {
          const markdown = response.data.markdown
          const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `${title || '会议纪要'}.md`
          link.click()
          URL.revokeObjectURL(url)
        }

        return response
      } catch (error) {
        console.error('下载 Markdown 失败:', error)
        throw error
      }
    },

    /**
     * 清空当前会议详情
     */
    clearCurrentMeeting() {
      this.currentMeeting = null
      this.transcripts = []
      this.speakers = []
      this.minutes = null
    }
  }
})
