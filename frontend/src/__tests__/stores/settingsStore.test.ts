import { describe, it, expect, beforeEach } from 'vitest'
import { useSettingsStore } from '../../store/settingsStore'

describe('settingsStore', () => {
  beforeEach(() => {
    useSettingsStore.setState({
      theme: 'system',
      language: 'en',
      sidebarCollapsed: false,
    })
  })

  it('should initialize with default values', () => {
    const state = useSettingsStore.getState()

    expect(state.theme).toBe('system')
    expect(state.language).toBe('en')
    expect(state.sidebarCollapsed).toBe(false)
  })

  it('should set theme correctly', () => {
    useSettingsStore.getState().setTheme('dark')
    expect(useSettingsStore.getState().theme).toBe('dark')

    useSettingsStore.getState().setTheme('light')
    expect(useSettingsStore.getState().theme).toBe('light')
  })

  it('should set language correctly', () => {
    useSettingsStore.getState().setLanguage('ro')
    expect(useSettingsStore.getState().language).toBe('ro')

    useSettingsStore.getState().setLanguage('en')
    expect(useSettingsStore.getState().language).toBe('en')
  })

  it('should toggle sidebar correctly', () => {
    expect(useSettingsStore.getState().sidebarCollapsed).toBe(false)

    useSettingsStore.getState().toggleSidebar()
    expect(useSettingsStore.getState().sidebarCollapsed).toBe(true)

    useSettingsStore.getState().toggleSidebar()
    expect(useSettingsStore.getState().sidebarCollapsed).toBe(false)
  })
})
