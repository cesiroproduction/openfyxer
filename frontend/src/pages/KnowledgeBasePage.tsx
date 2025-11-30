import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  MagnifyingGlassIcon,
  DocumentArrowUpIcon,
  TrashIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { ragService, Document, RAGResult } from '../services/ragService'
import { format } from 'date-fns'

export default function KnowledgeBasePage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [query, setQuery] = useState('')
  const [searchResult, setSearchResult] = useState<RAGResult | null>(null)
  const [searching, setSearching] = useState(false)

  const { data: documents, isLoading: loadingDocs } = useQuery({
    queryKey: ['documents'],
    queryFn: ragService.getDocuments,
  })

  const { data: indexingStatus } = useQuery({
    queryKey: ['indexing-status'],
    queryFn: ragService.getIndexingStatus,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => ragService.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['indexing-status'] })
      toast.success('Document uploaded')
    },
    onError: () => toast.error('Upload failed'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => ragService.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['indexing-status'] })
      toast.success('Document deleted')
    },
  })

  const reindexMutation = useMutation({
    mutationFn: ragService.reindexAll,
    onSuccess: () => {
      toast.success('Reindexing started')
    },
  })

  const handleSearch = async () => {
    if (!query.trim()) return

    setSearching(true)
    try {
      const result = await ragService.query({
        query: query.trim(),
        include_emails: true,
        include_documents: true,
        include_meetings: true,
        max_results: 10,
      })
      setSearchResult(result)
    } catch {
      toast.error('Search failed')
    } finally {
      setSearching(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('knowledgeBase.title')}
        </h1>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => reindexMutation.mutate()}
            disabled={reindexMutation.isPending}
            className="btn btn-secondary flex items-center"
          >
            <ArrowPathIcon
              className={`w-5 h-5 mr-2 ${reindexMutation.isPending ? 'animate-spin' : ''}`}
            />
            {t('knowledgeBase.reindexAll')}
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="btn btn-primary flex items-center"
          >
            <DocumentArrowUpIcon className="w-5 h-5 mr-2" />
            {t('knowledgeBase.uploadDocument')}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('knowledgeBase.indexingStatus')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('knowledgeBase.indexedEmails')}
            </p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">
              {indexingStatus?.indexed_emails || 0} / {indexingStatus?.total_emails || 0}
            </p>
            <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-600"
                style={{
                  width: `${
                    indexingStatus?.total_emails
                      ? (indexingStatus.indexed_emails / indexingStatus.total_emails) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('knowledgeBase.indexedDocuments')}
            </p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">
              {indexingStatus?.indexed_documents || 0} / {indexingStatus?.total_documents || 0}
            </p>
            <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-600"
                style={{
                  width: `${
                    indexingStatus?.total_documents
                      ? (indexingStatus.indexed_documents / indexingStatus.total_documents) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('knowledgeBase.indexedMeetings')}
            </p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">
              {indexingStatus?.indexed_meetings || 0} / {indexingStatus?.total_meetings || 0}
            </p>
            <div className="mt-2 h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-600"
                style={{
                  width: `${
                    indexingStatus?.total_meetings
                      ? (indexingStatus.indexed_meetings / indexingStatus.total_meetings) * 100
                      : 0
                  }%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('knowledgeBase.askQuestion')}
        </h2>
        <div className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={t('knowledgeBase.searchKnowledge')}
            className="input flex-1"
          />
          <button
            onClick={handleSearch}
            disabled={searching}
            className="btn btn-primary flex items-center"
          >
            <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
            {searching ? t('common.loading') : t('common.search')}
          </button>
        </div>

        {searchResult && (
          <div className="mt-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">Answer</h3>
              <p className="text-gray-700 dark:text-gray-300">{searchResult.answer}</p>
              <p className="text-sm text-gray-500 mt-2">
                Confidence: {(searchResult.confidence * 100).toFixed(0)}%
              </p>
            </div>

            {searchResult.sources.length > 0 && (
              <div className="mt-4">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">Sources</h3>
                <ul className="space-y-2">
                  {searchResult.sources.map((source, idx) => (
                    <li
                      key={idx}
                      className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {source.title}
                        </span>
                        <span className="badge badge-fyi">{source.type}</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {source.snippet}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('knowledgeBase.documents')}
        </h2>
        {loadingDocs ? (
          <div className="text-center py-4 text-gray-500">{t('common.loading')}</div>
        ) : documents && documents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    Filename
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    Type
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    Size
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    Indexed
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc: Document) => (
                  <tr
                    key={doc.id}
                    className="border-b border-gray-200 dark:border-gray-700"
                  >
                    <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                      {doc.filename}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {doc.file_type.toUpperCase()}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {doc.indexed_at ? (
                        <span className="text-green-600">
                          {format(new Date(doc.indexed_at), 'MMM d, yyyy')}
                        </span>
                      ) : (
                        <span className="text-yellow-600">Pending</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => deleteMutation.mutate(doc.id)}
                        className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900 rounded"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center py-4 text-gray-500">{t('knowledgeBase.noDocuments')}</p>
        )}
      </div>
    </div>
  )
}
