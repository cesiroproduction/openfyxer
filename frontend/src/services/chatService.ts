import api from './api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
  timestamp: string
}

export interface ChatSource {
  type: string
  id: string
  title: string
}

export interface ChatSuggestion {
  text: string
  category: string
}

export const chatService = {
  sendMessage: async (message: string): Promise<ChatMessage> => {
    const response = await api.post('/chat', { message })
    return response.data
  },

  getHistory: async (): Promise<ChatMessage[]> => {
    const response = await api.get('/chat/history')
    return response.data
  },

  clearHistory: async (): Promise<void> => {
    await api.delete('/chat/history')
  },

  getSuggestions: async (): Promise<ChatSuggestion[]> => {
    const response = await api.get('/chat/suggestions')
    return response.data
  },
}
