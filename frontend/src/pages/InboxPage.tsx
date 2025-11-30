import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowPathIcon,
  StarIcon,
  ArchiveBoxIcon,
  EnvelopeOpenIcon,
  EnvelopeIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { emailService, Email, EmailFilters } from '../services/emailService'
import { format } from 'date-fns'

const categories = [
  { id: 'all', label: 'allEmails' },
  { id: 'urgent', label: 'urgent' },
  { id: 'to_respond', label: 'toRespond' },
  { id: 'fyi', label: 'fyi' },
  { id: 'newsletter', label: 'newsletter' },
  { id: 'spam', label: 'spam' },
]

export default function InboxPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)
  const [syncing, setSyncing] = useState(false)

  const filters: EmailFilters = {
    category: selectedCategory === 'all' ? undefined : selectedCategory,
    is_archived: false,
    limit: 50,
  }

  const { data: emails, isLoading } = useQuery({
    queryKey: ['emails', filters],
    queryFn: () => emailService.getEmails(filters),
  })

  const { data: accounts } = useQuery({
    queryKey: ['email-accounts'],
    queryFn: emailService.getAccounts,
  })

  const markAsReadMutation = useMutation({
    mutationFn: (id: string) => emailService.markAsRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['emails'] }),
  })

  const toggleStarMutation = useMutation({
    mutationFn: (id: string) => emailService.toggleStar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['emails'] }),
  })

  const archiveMutation = useMutation({
    mutationFn: (id: string) => emailService.archive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emails'] })
      setSelectedEmail(null)
      toast.success('Email archived')
    },
  })

  const generateDraftMutation = useMutation({
    mutationFn: (emailId: string) => emailService.generateDraft(emailId),
    onSuccess: () => {
      toast.success('Draft generated')
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
    },
    onError: () => toast.error('Failed to generate draft'),
  })

  const handleSync = async () => {
    if (!accounts || accounts.length === 0) {
      toast.error('No email accounts configured')
      return
    }

    setSyncing(true)
    try {
      for (const account of accounts) {
        await emailService.syncAccount(account.id)
      }
      await queryClient.invalidateQueries({ queryKey: ['emails'] })
      toast.success('Emails synced')
    } catch {
      toast.error('Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  const handleEmailClick = (email: Email) => {
    setSelectedEmail(email)
    if (!email.is_read) {
      markAsReadMutation.mutate(email.id)
    }
  }

  const getCategoryBadge = (category?: string) => {
    switch (category) {
      case 'urgent':
        return <span className="badge badge-urgent">{t('inbox.urgent')}</span>
      case 'to_respond':
        return <span className="badge badge-to-respond">{t('inbox.toRespond')}</span>
      case 'fyi':
        return <span className="badge badge-fyi">{t('inbox.fyi')}</span>
      case 'newsletter':
        return <span className="badge badge-newsletter">{t('inbox.newsletter')}</span>
      default:
        return null
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('inbox.title')}
        </h1>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn btn-primary flex items-center"
        >
          <ArrowPathIcon className={clsx('w-5 h-5 mr-2', syncing && 'animate-spin')} />
          {syncing ? t('inbox.syncInProgress') : t('inbox.syncEmails')}
        </button>
      </div>

      <div className="flex space-x-2 mb-4 overflow-x-auto pb-2">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={clsx(
              'px-4 py-2 rounded-lg whitespace-nowrap transition-colors',
              selectedCategory === cat.id
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            )}
          >
            {t(`inbox.${cat.label}`)}
          </button>
        ))}
      </div>

      <div className="flex-1 flex bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">{t('common.loading')}</div>
          ) : emails && emails.length > 0 ? (
            <ul className="divide-y divide-gray-200 dark:divide-gray-700">
              {emails.map((email) => (
                <li
                  key={email.id}
                  onClick={() => handleEmailClick(email)}
                  className={clsx(
                    'p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700',
                    selectedEmail?.id === email.id && 'bg-gray-100 dark:bg-gray-700',
                    !email.is_read && 'font-semibold'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 dark:text-white truncate">
                        {email.sender}
                      </p>
                      <p className="text-sm text-gray-700 dark:text-gray-300 truncate">
                        {email.subject || 'No Subject'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-1">
                        {email.body_text?.substring(0, 100)}
                      </p>
                    </div>
                    <div className="ml-2 flex flex-col items-end">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {format(new Date(email.received_at), 'MMM d')}
                      </span>
                      {getCategoryBadge(email.category)}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-4 text-center text-gray-500">{t('inbox.noEmails')}</div>
          )}
        </div>

        <div className="flex-1 flex flex-col">
          {selectedEmail ? (
            <>
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedEmail.subject || 'No Subject'}
                  </h2>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => toggleStarMutation.mutate(selectedEmail.id)}
                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      {selectedEmail.is_starred ? (
                        <StarIconSolid className="w-5 h-5 text-yellow-500" />
                      ) : (
                        <StarIcon className="w-5 h-5 text-gray-400" />
                      )}
                    </button>
                    <button
                      onClick={() => archiveMutation.mutate(selectedEmail.id)}
                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <ArchiveBoxIcon className="w-5 h-5 text-gray-400" />
                    </button>
                    <button
                      onClick={() =>
                        selectedEmail.is_read
                          ? emailService.markAsUnread(selectedEmail.id)
                          : markAsReadMutation.mutate(selectedEmail.id)
                      }
                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      {selectedEmail.is_read ? (
                        <EnvelopeIcon className="w-5 h-5 text-gray-400" />
                      ) : (
                        <EnvelopeOpenIcon className="w-5 h-5 text-gray-400" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      From: {selectedEmail.sender}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      {format(new Date(selectedEmail.received_at), 'PPpp')}
                    </p>
                  </div>
                  {getCategoryBadge(selectedEmail.category)}
                </div>
              </div>

              <div className="flex-1 p-4 overflow-y-auto">
                <div className="prose dark:prose-invert max-w-none">
                  {selectedEmail.body_html ? (
                    <div
                      dangerouslySetInnerHTML={{ __html: selectedEmail.body_html }}
                    />
                  ) : (
                    <pre className="whitespace-pre-wrap font-sans">
                      {selectedEmail.body_text}
                    </pre>
                  )}
                </div>
              </div>

              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => generateDraftMutation.mutate(selectedEmail.id)}
                  disabled={generateDraftMutation.isPending}
                  className="btn btn-primary flex items-center"
                >
                  <SparklesIcon className="w-5 h-5 mr-2" />
                  {generateDraftMutation.isPending
                    ? t('common.loading')
                    : t('inbox.generateDraft')}
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              Select an email to view
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
