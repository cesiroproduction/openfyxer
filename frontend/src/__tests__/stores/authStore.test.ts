import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../../store/authStore'

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })

  it('should initialize with default values', () => {
    const state = useAuthStore.getState()

    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should set auth state correctly', () => {
    const user = {
      id: 'user123',
      email: 'test@example.com',
      full_name: 'Test User',
      two_factor_enabled: false,
      is_active: true,
    }
    const token = 'jwt-token-123'

    useAuthStore.getState().setAuth(user, token)
    const state = useAuthStore.getState()

    expect(state.user).toEqual(user)
    expect(state.token).toBe(token)
    expect(state.isAuthenticated).toBe(true)
  })

  it('should logout correctly', () => {
    useAuthStore.getState().setAuth(
      { id: '1', email: 'test@example.com', full_name: 'Test', two_factor_enabled: false, is_active: true },
      'token'
    )

    useAuthStore.getState().logout()
    const state = useAuthStore.getState()

    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should update user correctly', () => {
    useAuthStore.getState().setAuth(
      { id: '1', email: 'test@example.com', full_name: 'Test', two_factor_enabled: false, is_active: true },
      'token'
    )

    useAuthStore.getState().updateUser({ two_factor_enabled: true })
    const state = useAuthStore.getState()

    expect(state.user?.two_factor_enabled).toBe(true)
    expect(state.user?.email).toBe('test@example.com')
  })

  it('should not update user if not authenticated', () => {
    useAuthStore.getState().updateUser({ two_factor_enabled: true })
    const state = useAuthStore.getState()

    expect(state.user).toBeNull()
  })
})
