import { describe, it, expect } from 'vitest'

// Helper functions to test
function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    urgent: 'red',
    to_respond: 'yellow',
    fyi: 'blue',
    newsletter: 'gray',
    spam: 'gray',
  }
  return colors[category] || 'gray'
}

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

describe('Helper Functions', () => {
  describe('formatDate', () => {
    it('should format date correctly', () => {
      const date = new Date('2024-01-15')
      const formatted = formatDate(date)
      expect(formatted).toContain('Jan')
      expect(formatted).toContain('15')
      expect(formatted).toContain('2024')
    })
  })

  describe('truncateText', () => {
    it('should not truncate short text', () => {
      const text = 'Hello'
      expect(truncateText(text, 10)).toBe('Hello')
    })

    it('should truncate long text', () => {
      const text = 'This is a very long text that should be truncated'
      const truncated = truncateText(text, 20)
      expect(truncated.length).toBe(23) // 20 + '...'
      expect(truncated.endsWith('...')).toBe(true)
    })
  })

  describe('getCategoryColor', () => {
    it('should return correct color for urgent', () => {
      expect(getCategoryColor('urgent')).toBe('red')
    })

    it('should return correct color for to_respond', () => {
      expect(getCategoryColor('to_respond')).toBe('yellow')
    })

    it('should return gray for unknown category', () => {
      expect(getCategoryColor('unknown')).toBe('gray')
    })
  })

  describe('isValidEmail', () => {
    it('should validate correct email', () => {
      expect(isValidEmail('test@example.com')).toBe(true)
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true)
    })

    it('should reject invalid email', () => {
      expect(isValidEmail('invalid')).toBe(false)
      expect(isValidEmail('invalid@')).toBe(false)
      expect(isValidEmail('@domain.com')).toBe(false)
    })
  })

  describe('formatFileSize', () => {
    it('should format bytes correctly', () => {
      expect(formatFileSize(0)).toBe('0 Bytes')
      expect(formatFileSize(500)).toBe('500 Bytes')
    })

    it('should format KB correctly', () => {
      expect(formatFileSize(1024)).toBe('1 KB')
      expect(formatFileSize(2048)).toBe('2 KB')
    })

    it('should format MB correctly', () => {
      expect(formatFileSize(1048576)).toBe('1 MB')
    })
  })
})
