import api from './api'

export interface CalendarEvent {
  id: string
  title: string
  description?: string
  start_time: string
  end_time: string
  timezone?: string
  location?: string
  meeting_link?: string
  attendees?: string[]
  organizer?: string
  is_all_day: boolean
  is_recurring: boolean
  status: string
  color?: string
  reminder_minutes?: number
  provider?: string
}

export interface AvailableSlot {
  start_time: string
  end_time: string
  duration_minutes: number
}

export interface CalendarFilters {
  start_date?: string
  end_date?: string
  provider?: string
  skip?: number
  limit?: number
}

export const calendarService = {
  getEvents: async (filters: CalendarFilters = {}): Promise<CalendarEvent[]> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value))
      }
    })
    const response = await api.get(`/calendar/events?${params.toString()}`)
    // Handle paginated response
    return response.data.items || response.data
  },

  getEvent: async (id: string): Promise<CalendarEvent> => {
    const response = await api.get(`/calendar/events/${id}`)
    return response.data
  },

  createEvent: async (event: Partial<CalendarEvent>): Promise<CalendarEvent> => {
    const response = await api.post('/calendar/events', event)
    return response.data
  },

  updateEvent: async (id: string, event: Partial<CalendarEvent>): Promise<CalendarEvent> => {
    const response = await api.put(`/calendar/events/${id}`, event)
    return response.data
  },

  deleteEvent: async (id: string): Promise<void> => {
    await api.delete(`/calendar/events/${id}`)
  },

  getAvailableSlots: async (
    durationMinutes: number,
    dateFrom: string,
    dateTo: string
  ): Promise<AvailableSlot[]> => {
    const response = await api.get('/calendar/available-slots', {
      params: {
        duration_minutes: durationMinutes,
        date_from: dateFrom,
        date_to: dateTo,
      },
    })
    return response.data
  },

  checkConflicts: async (
    startTime: string,
    endTime: string,
    excludeEventId?: string
  ): Promise<CalendarEvent[]> => {
    const response = await api.post('/calendar/check-conflicts', {
      start_time: startTime,
      end_time: endTime,
      exclude_event_id: excludeEventId,
    })
    return response.data
  },

  syncCalendar: async (): Promise<void> => {
    await api.post('/calendar/sync')
  },
}
