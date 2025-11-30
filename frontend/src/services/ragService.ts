import api from './api'

export interface RAGQuery {
  query: string
  include_emails?: boolean
  include_documents?: boolean
  include_meetings?: boolean
  max_results?: number
}

export interface RAGResult {
  answer: string
  sources: RAGSource[]
  confidence: number
}

export interface RAGSource {
  type: string
  id: string
  title: string
  snippet: string
  relevance_score: number
}

export interface Document {
  id: string
  filename: string
  file_type: string
  file_size: number
  content_summary?: string
  word_count?: number
  page_count?: number
  indexed_at?: string
  created_at: string
}

export interface IndexingStatus {
  total_emails: number
  indexed_emails: number
  total_documents: number
  indexed_documents: number
  total_meetings: number
  indexed_meetings: number
  last_index_at?: string
}

export const ragService = {
  query: async (data: RAGQuery): Promise<RAGResult> => {
    const response = await api.post('/rag/query', data)
    return response.data
  },

  getDocuments: async (): Promise<Document[]> => {
    const response = await api.get('/rag/documents')
    return response.data
  },

  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/rag/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  deleteDocument: async (id: string): Promise<void> => {
    await api.delete(`/rag/documents/${id}`)
  },

  getIndexingStatus: async (): Promise<IndexingStatus> => {
    const response = await api.get('/rag/indexing-status')
    return response.data
  },

  reindexAll: async (): Promise<void> => {
    await api.post('/rag/reindex')
  },
}
