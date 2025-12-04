import api from './api'

export interface UserSettings {
  id: string
  user_id: string
  llm_provider: string
  llm_model?: string
  email_style: string
  email_signature?: string
  default_language: string
  timezone: string
  working_hours_start?: string
  working_hours_end?: string
  working_days?: number[]
  meeting_buffer_minutes?: number
  follow_up_days?: number
  notification_preferences?: Record<string, boolean>
  slack_webhook_url?: string
  sms_provider?: string
  sms_phone_number?: string
  notification_email?: string
  // Add index signature to allow loose typing if needed for partial updates
  [key: string]: any
}

export interface LLMProvider {
  id: string
  name: string
  type: string
  is_configured: boolean
  models?: string[]
}

export const settingsService = {
  getSettings: async (): Promise<UserSettings> => {
    const response = await api.get('/settings')
    return response.data
  },

  updateSettings: async (settings: Partial<UserSettings>): Promise<UserSettings> => {
    const response = await api.put('/settings', settings)
    return response.data
  },

  getLLMProviders: async (): Promise<LLMProvider[]> => {
    const response = await api.get('/settings/llm-providers')
    return response.data
  },

  setLLMApiKey: async (provider: string, apiKey: string): Promise<void> => {
    await api.post('/settings/llm-api-key', { provider, api_key: apiKey })
  },

  deleteLLMApiKey: async (provider: string): Promise<void> => {
    await api.delete(`/settings/api-key/${provider}`)
  },

  testNotification: async (channel: string): Promise<{ success: boolean }> => {
    const response = await api.post('/settings/test-notification', { channel })
    return response.data
  },

  analyzeEmailStyle: async (): Promise<{ style_profile: string }> => {
    const response = await api.post('/settings/analyze-style', { analyze_sent_emails: true })
    return response.data
  },
}
