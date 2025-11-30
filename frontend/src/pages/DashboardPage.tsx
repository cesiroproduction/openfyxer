import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  ClockIcon,
  EnvelopeIcon,
  DocumentTextIcon,
  MicrophoneIcon,
  ExclamationCircleIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline'
import { useAuthStore } from '../store/authStore'
import { emailService } from '../services/emailService'
import { calendarService } from '../services/calendarService'
import { ragService } from '../services/ragService'
import { auditService } from '../services/auditService'

export default function DashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuthStore()

  const { data: emails } = useQuery({
    queryKey: ['emails', 'urgent'],
    queryFn: () => emailService.getEmails({ category: 'urgent', limit: 5 }),
  })

  const { data: events } = useQuery({
    queryKey: ['calendar', 'today'],
    queryFn: () => {
      const today = new Date().toISOString().split('T')[0]
      const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0]
      return calendarService.getEvents({ start_date: today, end_date: tomorrow })
    },
  })

  const { data: indexingStatus } = useQuery({
    queryKey: ['indexing-status'],
    queryFn: ragService.getIndexingStatus,
  })

  const { data: auditStats } = useQuery({
    queryKey: ['audit-stats'],
    queryFn: auditService.getStats,
  })

  const stats = [
    {
      name: t('dashboard.timeSaved'),
      value: '12.5h',
      icon: ClockIcon,
      color: 'bg-green-500',
    },
    {
      name: t('dashboard.emailsProcessed'),
      value: indexingStatus?.indexed_emails || 0,
      icon: EnvelopeIcon,
      color: 'bg-blue-500',
    },
    {
      name: t('dashboard.draftsGenerated'),
      value: auditStats?.total_actions || 0,
      icon: DocumentTextIcon,
      color: 'bg-purple-500',
    },
    {
      name: t('dashboard.meetingsTranscribed'),
      value: indexingStatus?.indexed_meetings || 0,
      icon: MicrophoneIcon,
      color: 'bg-orange-500',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('dashboard.title')}
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          {t('dashboard.welcome')}, {user?.full_name || user?.email}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {stat.name}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stat.value}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <ExclamationCircleIcon className="w-5 h-5 mr-2 text-red-500" />
            {t('dashboard.urgentEmails')}
          </h2>
          {emails && emails.length > 0 ? (
            <ul className="space-y-3">
              {emails.map((email) => (
                <li
                  key={email.id}
                  className="flex items-start p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {email.subject || 'No Subject'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                      {email.sender}
                    </p>
                  </div>
                  <span className="badge badge-urgent ml-2">Urgent</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-center py-4">
              No urgent emails
            </p>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <CalendarIcon className="w-5 h-5 mr-2 text-blue-500" />
            {t('dashboard.todaysMeetings')}
          </h2>
          {events && events.length > 0 ? (
            <ul className="space-y-3">
              {events.map((event) => (
                <li
                  key={event.id}
                  className="flex items-start p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {event.title}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(event.start_time).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                      {' - '}
                      {new Date(event.end_time).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                  {event.meeting_link && (
                    <a
                      href={event.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-primary text-xs py-1 px-2"
                    >
                      Join
                    </a>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-center py-4">
              No meetings today
            </p>
          )}
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
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('knowledgeBase.indexedDocuments')}
            </p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">
              {indexingStatus?.indexed_documents || 0} / {indexingStatus?.total_documents || 0}
            </p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('knowledgeBase.indexedMeetings')}
            </p>
            <p className="text-xl font-bold text-gray-900 dark:text-white">
              {indexingStatus?.indexed_meetings || 0} / {indexingStatus?.total_meetings || 0}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
