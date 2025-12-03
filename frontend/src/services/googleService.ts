import api from './api'

export interface GoogleAccount {
  id: string
  email: string
  display_name?: string
  is_active: boolean
  last_sync?: string
}

export interface GoogleStatus {
  connected: boolean
  accounts: GoogleAccount[]
  oauth_configured: boolean
}

export interface GoogleAuthUrl {
  authorization_url: string
  state: string
}

export const googleService = {
  /**
   * Get Google OAuth authorization URL
   * User should be redirected to this URL to authorize the app
   */
  getAuthUrl: async (): Promise<GoogleAuthUrl> => {
    const response = await api.get('/integrations/google/authorize')
    return response.data
  },

  /**
   * Check Google connection status for current user
   */
  getStatus: async (): Promise<GoogleStatus> => {
    const response = await api.get('/integrations/google/status')
    return response.data
  },

  /**
   * Disconnect a Google account
   */
  disconnect: async (accountId: string): Promise<void> => {
    await api.delete(`/integrations/google/disconnect/${accountId}`)
  },

  /**
   * Start Google OAuth flow by redirecting to Google
   */
  connectGoogle: async (): Promise<void> => {
    const { authorization_url } = await googleService.getAuthUrl()
    window.location.href = authorization_url
  },
}
