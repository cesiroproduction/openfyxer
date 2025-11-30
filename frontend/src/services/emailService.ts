import api from './api'

export interface Email {
  id: string
  account_id: string
  message_id: string
  thread_id?: string
  subject?: string
  sender?: string
  recipients: string[]
  cc?: string[]
  bcc?: string[]
  body_text?: string
  body_html?: string
  received_at: string
  is_read: boolean
  is_starred: boolean
  is_archived: boolean
  category?: string
  priority_score?: number
  language?: string
  sentiment?: string
  has_attachments: boolean
  attachments?: Attachment[]
}

export interface Attachment {
  id: string
  filename: string
  content_type: string
  size: number
}

export interface EmailAccount {
  id: string
  provider: string
  email_address: string
  display_name?: string
  is_active: boolean
  sync_enabled: boolean
  last_sync_at?: string
}

export interface Draft {
  id: string
  email_id: string
  subject: string
  content: string
  status: string
  tone?: string
  language?: string
  created_at: string
  updated_at: string
}

export interface EmailFilters {
  category?: string
  is_read?: boolean
  is_starred?: boolean
  is_archived?: boolean
  search?: string
  account_id?: string
  skip?: number
  limit?: number
}

export const emailService = {
  getEmails: async (filters: EmailFilters = {}): Promise<Email[]> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value))
      }
    })
    const response = await api.get(`/emails?${params.toString()}`)
    return response.data
  },

  getEmail: async (id: string): Promise<Email> => {
    const response = await api.get(`/emails/${id}`)
    return response.data
  },

  markAsRead: async (id: string): Promise<void> => {
    await api.post(`/emails/${id}/read`)
  },

  markAsUnread: async (id: string): Promise<void> => {
    await api.post(`/emails/${id}/unread`)
  },

  toggleStar: async (id: string): Promise<void> => {
    await api.post(`/emails/${id}/star`)
  },

  archive: async (id: string): Promise<void> => {
    await api.post(`/emails/${id}/archive`)
  },

  categorize: async (id: string, category: string): Promise<void> => {
    await api.post(`/emails/${id}/categorize`, { category })
  },

  getAccounts: async (): Promise<EmailAccount[]> => {
    const response = await api.get('/email-accounts')
    return response.data
  },

  addAccount: async (data: {
    provider: string
    email_address: string
    display_name?: string
  }): Promise<EmailAccount> => {
    const response = await api.post('/email-accounts', data)
    return response.data
  },

  removeAccount: async (id: string): Promise<void> => {
    await api.delete(`/email-accounts/${id}`)
  },

  syncAccount: async (id: string): Promise<void> => {
    await api.post(`/email-accounts/${id}/sync`)
  },

  getOAuthUrl: async (provider: string): Promise<{ url: string }> => {
    const response = await api.get(`/email-accounts/oauth/${provider}/url`)
    return response.data
  },

  getDrafts: async (): Promise<Draft[]> => {
    const response = await api.get('/drafts')
    return response.data
  },

  getDraft: async (id: string): Promise<Draft> => {
    const response = await api.get(`/drafts/${id}`)
    return response.data
  },

  generateDraft: async (emailId: string, tone?: string): Promise<Draft> => {
    const response = await api.post('/drafts', { email_id: emailId, tone })
    return response.data
  },

  updateDraft: async (id: string, content: string): Promise<Draft> => {
    const response = await api.put(`/drafts/${id}`, { content })
    return response.data
  },

  approveDraft: async (id: string): Promise<void> => {
    await api.post(`/drafts/${id}/approve`)
  },

  sendDraft: async (id: string): Promise<void> => {
    await api.post(`/drafts/${id}/send`)
  },

  regenerateDraft: async (id: string, tone?: string): Promise<Draft> => {
    const response = await api.post(`/drafts/${id}/regenerate`, { tone })
    return response.data
  },
}
