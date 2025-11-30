import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { FunnelIcon } from '@heroicons/react/24/outline'
import { auditService, AuditLog, AuditFilters } from '../services/auditService'
import { format } from 'date-fns'

export default function AuditPage() {
  const { t } = useTranslation()
  const [filters, setFilters] = useState<AuditFilters>({})

  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit-logs', filters],
    queryFn: () => auditService.getLogs(filters),
  })

  const { data: stats } = useQuery({
    queryKey: ['audit-stats'],
    queryFn: auditService.getStats,
  })

  const { data: availableActions } = useQuery({
    queryKey: ['audit-actions'],
    queryFn: auditService.getAvailableActions,
  })

  const { data: entityTypes } = useQuery({
    queryKey: ['audit-entity-types'],
    queryFn: auditService.getEntityTypes,
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <span className="badge bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
            {t('audit.success')}
          </span>
        )
      case 'error':
        return (
          <span className="badge bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
            {t('audit.error')}
          </span>
        )
      default:
        return (
          <span className="badge bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
            {status}
          </span>
        )
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
        {t('audit.title')}
      </h1>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('audit.totalActions')}
            </p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.total_actions}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('audit.actionsToday')}
            </p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.actions_today}
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {t('audit.successRate')}
            </p>
            <p className="text-2xl font-bold text-green-600">
              {(stats.success_rate * 100).toFixed(1)}%
            </p>
          </div>
          <div className="card">
            <p className="text-sm text-gray-600 dark:text-gray-400">Errors</p>
            <p className="text-2xl font-bold text-red-600">{stats.error_count}</p>
          </div>
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Logs
          </h2>
          <div className="flex items-center space-x-2">
            <FunnelIcon className="w-5 h-5 text-gray-400" />
            <select
              value={filters.action || ''}
              onChange={(e) =>
                setFilters({ ...filters, action: e.target.value || undefined })
              }
              className="input py-1 text-sm"
            >
              <option value="">{t('audit.filterByAction')}</option>
              {availableActions?.map((action: string) => (
                <option key={action} value={action}>
                  {action}
                </option>
              ))}
            </select>
            <select
              value={filters.entity_type || ''}
              onChange={(e) =>
                setFilters({ ...filters, entity_type: e.target.value || undefined })
              }
              className="input py-1 text-sm"
            >
              <option value="">Entity Type</option>
              {entityTypes?.map((type: string) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
            <select
              value={filters.status || ''}
              onChange={(e) =>
                setFilters({ ...filters, status: e.target.value || undefined })
              }
              className="input py-1 text-sm"
            >
              <option value="">{t('audit.filterByStatus')}</option>
              <option value="success">{t('audit.success')}</option>
              <option value="error">{t('audit.error')}</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-4 text-gray-500">{t('common.loading')}</div>
        ) : logs && logs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('audit.timestamp')}
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('audit.action')}
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('audit.entityType')}
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('audit.status')}
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500 dark:text-gray-400">
                    {t('audit.details')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log: AuditLog) => (
                  <tr
                    key={log.id}
                    className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {format(new Date(log.created_at), 'MMM d, HH:mm:ss')}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900 dark:text-white">
                      {log.action}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {log.entity_type || '-'}
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(log.status)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {log.error_message ? (
                        <span className="text-red-600">{log.error_message}</span>
                      ) : log.details ? (
                        <span className="truncate max-w-xs block">
                          {JSON.stringify(log.details).substring(0, 50)}...
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center py-4 text-gray-500">{t('audit.noLogs')}</p>
        )}
      </div>

      {stats?.common_actions && stats.common_actions.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Common Actions
          </h2>
          <div className="space-y-2">
            {stats.common_actions.map(
              (item: { action: string; count: number }, idx: number) => (
                <div key={idx} className="flex items-center justify-between">
                  <span className="text-gray-700 dark:text-gray-300">{item.action}</span>
                  <div className="flex items-center">
                    <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full mr-2">
                      <div
                        className="h-full bg-primary-600 rounded-full"
                        style={{
                          width: `${
                            (item.count / stats.total_actions) * 100
                          }%`,
                        }}
                      />
                    </div>
                    <span className="text-sm text-gray-500">{item.count}</span>
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )
}
