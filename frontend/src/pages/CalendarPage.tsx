import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import {
  PlusIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { calendarService, CalendarEvent } from '../services/calendarService'
import {
  format,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameDay,
  isSameMonth,
  addMonths,
  subMonths,
  addWeeks,
  subWeeks,
} from 'date-fns'

type ViewMode = 'week' | 'month'

interface EventFormData {
  title: string
  description?: string
  start_time: string
  end_time: string
  location?: string
  attendees?: string
  is_all_day: boolean
}

export default function CalendarPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [viewMode, setViewMode] = useState<ViewMode>('week')
  const [currentDate, setCurrentDate] = useState(new Date())
  const [showEventModal, setShowEventModal] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)

  const { register, handleSubmit, reset } = useForm<EventFormData>()

  const startDate =
    viewMode === 'week'
      ? startOfWeek(currentDate, { weekStartsOn: 1 })
      : startOfMonth(currentDate)
  const endDate =
    viewMode === 'week'
      ? endOfWeek(currentDate, { weekStartsOn: 1 })
      : endOfMonth(currentDate)

  const { data: events, isLoading } = useQuery({
    queryKey: ['calendar', startDate.toISOString(), endDate.toISOString()],
    queryFn: () =>
      calendarService.getEvents({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      }),
  })

  const syncCalendarMutation = useMutation({
    mutationFn: () => calendarService.syncCalendar(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.success('Calendar synced')
    },
    onError: () => toast.error('Failed to sync calendar'),
  })

  useEffect(() => {
    syncCalendarMutation.mutate()
  }, [])

  const createEventMutation = useMutation({
    mutationFn: (data: Partial<CalendarEvent>) => calendarService.createEvent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      setShowEventModal(false)
      reset()
      toast.success('Event created')
    },
    onError: () => toast.error('Failed to create event'),
  })

  const deleteEventMutation = useMutation({
    mutationFn: (id: string) => calendarService.deleteEvent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      setSelectedEvent(null)
      toast.success('Event deleted')
    },
  })

  const days = eachDayOfInterval({ start: startDate, end: endDate })

  const navigatePrev = () => {
    if (viewMode === 'week') {
      setCurrentDate(subWeeks(currentDate, 1))
    } else {
      setCurrentDate(subMonths(currentDate, 1))
    }
  }

  const navigateNext = () => {
    if (viewMode === 'week') {
      setCurrentDate(addWeeks(currentDate, 1))
    } else {
      setCurrentDate(addMonths(currentDate, 1))
    }
  }

  const getEventsForDay = (day: Date) => {
    return events?.filter((event) =>
      isSameDay(new Date(event.start_time), day)
    ) || []
  }

  const onSubmit = (data: EventFormData) => {
    createEventMutation.mutate({
      title: data.title,
      description: data.description,
      start_time: data.start_time,
      end_time: data.end_time,
      location: data.location,
      attendees: data.attendees?.split(',').map((a) => a.trim()),
      is_all_day: data.is_all_day,
    })
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('calendar.title')}
        </h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('week')}
              className={clsx(
                'px-3 py-1 rounded-lg',
                viewMode === 'week'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700'
              )}
            >
              {t('calendar.week')}
            </button>
            <button
              onClick={() => setViewMode('month')}
              className={clsx(
                'px-3 py-1 rounded-lg',
                viewMode === 'month'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700'
              )}
            >
              {t('calendar.month')}
            </button>
          </div>
          <button
            onClick={() => setShowEventModal(true)}
            className="btn btn-primary flex items-center"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            {t('calendar.newEvent')}
          </button>
          <button
            onClick={() => syncCalendarMutation.mutate()}
            className="btn btn-secondary flex items-center"
            disabled={syncCalendarMutation.isPending}
          >
            <ArrowPathIcon
              className={clsx('w-5 h-5 mr-2', {
                'animate-spin': syncCalendarMutation.isPending,
              })}
            />
            {syncCalendarMutation.isPending ? 'Syncing...' : 'Sync Calendar'}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={navigatePrev}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {format(currentDate, viewMode === 'week' ? 'MMMM yyyy' : 'MMMM yyyy')}
          </h2>
          <button
            onClick={navigateNext}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
        <button
          onClick={() => setCurrentDate(new Date())}
          className="btn btn-secondary"
        >
          {t('calendar.today')}
        </button>
      </div>

      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <ArrowPathIcon className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : (
          <div className="grid grid-cols-7 h-full">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
              <div
                key={day}
                className="p-2 text-center text-sm font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700"
              >
                {day}
              </div>
            ))}
            {days.map((day) => {
              const dayEvents = getEventsForDay(day)
              const isToday = isSameDay(day, new Date())
              const isCurrentMonth = isSameMonth(day, currentDate)

              return (
                <div
                  key={day.toISOString()}
                  className={clsx(
                    'border-b border-r border-gray-200 dark:border-gray-700 p-2 min-h-24',
                    !isCurrentMonth && 'bg-gray-50 dark:bg-gray-900'
                  )}
                >
                  <div
                    className={clsx(
                      'text-sm font-medium mb-1',
                      isToday
                        ? 'w-7 h-7 bg-primary-600 text-white rounded-full flex items-center justify-center'
                        : isCurrentMonth
                        ? 'text-gray-900 dark:text-white'
                        : 'text-gray-400 dark:text-gray-600'
                    )}
                  >
                    {format(day, 'd')}
                  </div>
                  <div className="space-y-1">
                    {dayEvents.slice(0, 3).map((event) => (
                      <div
                        key={event.id}
                        onClick={() => setSelectedEvent(event)}
                        className="text-xs p-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-200 rounded truncate cursor-pointer hover:bg-primary-200 dark:hover:bg-primary-800"
                      >
                        {format(new Date(event.start_time), 'HH:mm')} {event.title}
                      </div>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-xs text-gray-500">
                        +{dayEvents.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {showEventModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t('calendar.newEvent')}
            </h3>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('calendar.eventTitle')}
                </label>
                <input
                  type="text"
                  {...register('title', { required: true })}
                  className="input mt-1"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('calendar.startTime')}
                  </label>
                  <input
                    type="datetime-local"
                    {...register('start_time', { required: true })}
                    className="input mt-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    {t('calendar.endTime')}
                  </label>
                  <input
                    type="datetime-local"
                    {...register('end_time', { required: true })}
                    className="input mt-1"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('calendar.location')}
                </label>
                <input type="text" {...register('location')} className="input mt-1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('calendar.attendees')} (comma separated)
                </label>
                <input type="text" {...register('attendees')} className="input mt-1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('calendar.description')}
                </label>
                <textarea {...register('description')} className="input mt-1" rows={3} />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  {...register('is_all_day')}
                  className="mr-2"
                />
                <label className="text-sm text-gray-700 dark:text-gray-300">
                  {t('calendar.allDay')}
                </label>
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowEventModal(false)
                    reset()
                  }}
                  className="btn btn-secondary"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  disabled={createEventMutation.isPending}
                  className="btn btn-primary"
                >
                  {createEventMutation.isPending ? t('common.loading') : t('common.create')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {selectedEvent.title}
            </h3>
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <p>
                <strong>{t('calendar.startTime')}:</strong>{' '}
                {format(new Date(selectedEvent.start_time), 'PPpp')}
              </p>
              <p>
                <strong>{t('calendar.endTime')}:</strong>{' '}
                {format(new Date(selectedEvent.end_time), 'PPpp')}
              </p>
              {selectedEvent.location && (
                <p>
                  <strong>{t('calendar.location')}:</strong> {selectedEvent.location}
                </p>
              )}
              {selectedEvent.attendees && selectedEvent.attendees.length > 0 && (
                <p>
                  <strong>{t('calendar.attendees')}:</strong>{' '}
                  {selectedEvent.attendees.join(', ')}
                </p>
              )}
              {selectedEvent.description && (
                <p>
                  <strong>{t('calendar.description')}:</strong>{' '}
                  {selectedEvent.description}
                </p>
              )}
              {selectedEvent.meeting_link && (
                <p>
                  <a
                    href={selectedEvent.meeting_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:underline"
                  >
                    Join Meeting
                  </a>
                </p>
              )}
            </div>
            <div className="flex justify-end space-x-2 mt-4">
              <button
                onClick={() => deleteEventMutation.mutate(selectedEvent.id)}
                className="btn btn-danger"
              >
                {t('common.delete')}
              </button>
              <button
                onClick={() => setSelectedEvent(null)}
                className="btn btn-secondary"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
