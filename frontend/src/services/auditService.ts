import api from './api'

export interface AuditLog {
  id: string
  user_id: string
  action: string
  entity_type?: string
  entity_id?: string
  details?: Record<string, unknown>
  status: string
  error_message?: string
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AuditStats {
  total_actions: number
  actions_today: number
  success_count: number
  error_count: number
  success_rate: number
  common_actions: { action: string; count: number }[]
}

export interface AuditFilters {
  action?: string
  entity_type?: string
  status?: string
  date_from?: string
  date_to?: string
  skip?: number
  limit?: number
}

export const auditService = {
  getLogs: async (filters: AuditFilters = {}): Promise<AuditLog[]> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value))
      }
    })
    const response = await api.get(`/audit?${params.toString()}`)
    return response.data
  },

  getStats: async (): Promise<AuditStats> => {
    const response = await api.get('/audit/stats')
    return response.data
  },

  getAvailableActions: async (): Promise<string[]> => {
    const response = await api.get('/audit/actions')
    return response.data
  },

  getEntityTypes: async (): Promise<string[]> => {
    const response = await api.get('/audit/entity-types')
    return response.data
  },
}
