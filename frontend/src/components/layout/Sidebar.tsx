import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  HomeIcon,
  InboxIcon,
  PencilSquareIcon,
  CalendarIcon,
  BookOpenIcon,
  VideoCameraIcon,
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  ClipboardDocumentListIcon,
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface SidebarProps {
  collapsed: boolean
}

export default function Sidebar({ collapsed }: SidebarProps) {
  const { t } = useTranslation()

  const navigation = [
    { name: t('nav.dashboard'), href: '/', icon: HomeIcon },
    { name: t('nav.inbox'), href: '/inbox', icon: InboxIcon },
    { name: 'Drafts', href: '/drafts', icon: PencilSquareIcon },
    { name: t('nav.calendar'), href: '/calendar', icon: CalendarIcon },
    { name: t('nav.knowledgeBase'), href: '/knowledge-base', icon: BookOpenIcon },
    { name: t('nav.meetings'), href: '/meetings', icon: VideoCameraIcon },
    { name: t('nav.chat'), href: '/chat', icon: ChatBubbleLeftRightIcon },
    { name: t('nav.settings'), href: '/settings', icon: Cog6ToothIcon },
    { name: t('nav.audit'), href: '/audit', icon: ClipboardDocumentListIcon },
  ]

  return (
    <aside
      className={clsx(
        'bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-center h-16 border-b border-gray-200 dark:border-gray-700">
          {collapsed ? (
            <span className="text-2xl font-bold text-primary-600">OF</span>
          ) : (
            <span className="text-xl font-bold text-primary-600">OpenFyxer</span>
          )}
        </div>

        <nav className="flex-1 px-2 py-4 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                clsx(
                  'flex items-center px-3 py-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-200'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                )
              }
            >
              <item.icon className="w-6 h-6 flex-shrink-0" />
              {!collapsed && <span className="ml-3">{item.name}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          {!collapsed && (
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              OpenFyxer v1.0.0
            </p>
          )}
        </div>
      </div>
    </aside>
  )
}
