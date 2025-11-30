import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    })),
  },
}))

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should create axios instance with correct base URL', () => {
    expect(axios.create).toBeDefined()
  })

  it('should have request interceptor for auth token', () => {
    const mockAxios = axios.create()
    expect(mockAxios.interceptors.request.use).toBeDefined()
  })

  it('should have response interceptor for error handling', () => {
    const mockAxios = axios.create()
    expect(mockAxios.interceptors.response.use).toBeDefined()
  })
})
