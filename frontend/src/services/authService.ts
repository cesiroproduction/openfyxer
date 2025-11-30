import api from './api'

export interface LoginRequest {
  email: string
  password: string
  totp_code?: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    email: string
    full_name: string
    is_active: boolean
    two_factor_enabled: boolean
  }
}

export interface TwoFactorSetupResponse {
  secret: string
  qr_code: string
}

export const authService = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', data)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  refreshToken: async (): Promise<AuthResponse> => {
    const response = await api.post('/auth/refresh')
    return response.data
  },

  setup2FA: async (): Promise<TwoFactorSetupResponse> => {
    const response = await api.post('/auth/2fa/setup')
    return response.data
  },

  verify2FA: async (code: string): Promise<{ success: boolean }> => {
    const response = await api.post('/auth/2fa/verify', { code })
    return response.data
  },

  disable2FA: async (code: string): Promise<{ success: boolean }> => {
    const response = await api.post('/auth/2fa/disable', { code })
    return response.data
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    await api.post('/users/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
}
