import api from './api'

export interface Meeting {
  id: string
  title: string
  description?: string
  meeting_date?: string
  participants?: string[]
  audio_file_path?: string
  audio_duration_seconds?: number
  transcript?: string
  transcript_language?: string
  summary?: string
  action_items?: string[]
  key_decisions?: string[]
  topics?: string[]
  status: string
  transcribed_at?: string
  summarized_at?: string
  created_at: string
}

export interface MeetingFilters {
  status?: string
  search?: string
  skip?: number
  limit?: number
}

export const meetingService = {
  getMeetings: async (filters: MeetingFilters = {}): Promise<Meeting[]> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value))
      }
    })
    const response = await api.get(`/meetings?${params.toString()}`)
    return response.data
  },

  getMeeting: async (id: string): Promise<Meeting> => {
    const response = await api.get(`/meetings/${id}`)
    return response.data
  },

  createMeeting: async (data: {
    title: string
    description?: string
    meeting_date?: string
    participants?: string[]
  }): Promise<Meeting> => {
    const response = await api.post('/meetings', data)
    return response.data
  },

  updateMeeting: async (id: string, data: Partial<Meeting>): Promise<Meeting> => {
    const response = await api.put(`/meetings/${id}`, data)
    return response.data
  },

  deleteMeeting: async (id: string): Promise<void> => {
    await api.delete(`/meetings/${id}`)
  },

  uploadAudio: async (id: string, file: File): Promise<Meeting> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post(`/meetings/${id}/audio`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  transcribe: async (id: string, language?: string): Promise<void> => {
    await api.post(`/meetings/${id}/transcribe`, { language })
  },

  summarize: async (id: string): Promise<void> => {
    await api.post(`/meetings/${id}/summarize`)
  },

  generateFollowUpEmail: async (id: string): Promise<{ content: string }> => {
    const response = await api.post(`/meetings/${id}/follow-up-email`)
    return response.data
  },
}
