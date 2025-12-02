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
    return response.data.items || []
  },

  getStats: async (): Promise<AuditStats> => {
    const response = await api.get('/audit/stats')
    // Map API response to expected format
    const data = response.data
    return {
      total_actions: data.total_actions,
      actions_today: data.actions_today,
      success_count: data.success_count || 0,
      error_count: data.error_count || 0,
      success_rate: data.success_rate / 100, // API returns percentage, frontend expects decimal
      common_actions: data.most_common_actions || []
    }
  },

  getAvailableActions: async (): Promise<string[]> => {
    const response = await api.get('/audit/actions')
    return response.data.actions || []
  },

  getEntityTypes: async (): Promise<string[]> => {
    const response = await api.get('/audit/entity-types')
    return response.data.entity_types || []
  },
}
