/**
 * Calendar Component
 *
 * Displays the user's Google Calendar events using react-big-calendar.
 *
 * FEATURES:
 * - Week view by default (as requested in requirements)
 * - Fetches events from Google Calendar API via /api/calendar/events
 * - Updates when user navigates to different dates
 * - Shows event details popup on click with formatted date/time
 * - Displays event time ranges in calendar blocks
 * - Responsive design matching dashboard aesthetic
 *
 * TECHNICAL DETAILS:
 * - Uses react-big-calendar for calendar UI
 * - Uses date-fns for date formatting (lightweight alternative to moment.js)
 * - Fetches events when date range changes (week/month navigation)
 * - Converts API response format to react-big-calendar format
 * - Custom event component shows title + time range
 * - Modal popup for event details with escape key support
 *
 * PROPS:
 * - onEventUpdate: Callback when an event is created/updated/deleted
 *   (allows Dashboard to refresh the calendar)
 */

import { useState, useEffect, useCallback } from 'react'
import { Calendar as BigCalendar, dateFnsLocalizer } from 'react-big-calendar'
import { format, parse, startOfWeek, getDay } from 'date-fns'
import enUS from 'date-fns/locale/en-US'
import api from '../utils/api'
import CustomToolbar from './CustomToolbar'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import './Calendar.css'

// Configure date-fns localizer for react-big-calendar
// This tells react-big-calendar how to format dates using date-fns
const locales = {
  'en-US': enUS,
}

const localizer = dateFnsLocalizer({
  format,           // Format dates for display (e.g., "January 2026")
  parse,            // Parse date strings into Date objects
  startOfWeek,      // Determine start of week (Sunday in US)
  getDay,           // Get day of week (0-6)
  locales,          // Locale data for formatting
})

function Calendar({ onEventUpdate }) {
  // ==================== State Management ====================

  // Events fetched from Google Calendar
  // Each event has: { id, title, start (Date), end (Date), description }
  const [events, setEvents] = useState([])

  // Loading state while fetching events
  const [loading, setLoading] = useState(true)

  // Error message if fetch fails
  const [error, setError] = useState(null)

  // Current view type - default to 'week' per requirements
  const [view, setView] = useState('week')

  // Current date being viewed (used to calculate date range for API call)
  const [date, setDate] = useState(new Date())

  // Selected event for popup display
  const [selectedEvent, setSelectedEvent] = useState(null)

  // ==================== Helper Functions ====================

  /**
   * Format a date object as "March 4th, 2026"
   */
  const formatDateForPopup = (dateObj) => {
    if (!dateObj) return ''

    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    const day = dateObj.getDate()
    const month = months[dateObj.getMonth()]
    const year = dateObj.getFullYear()

    // Add ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
    const suffix = (day % 10 === 1 && day !== 11) ? 'st' :
                   (day % 10 === 2 && day !== 12) ? 'nd' :
                   (day % 10 === 3 && day !== 13) ? 'rd' : 'th'

    return `${month} ${day}${suffix}, ${year}`
  }

  /**
   * Format a date object as "12:00 PM"
   */
  const formatTimeForPopup = (dateObj) => {
    if (!dateObj) return ''

    let hours = dateObj.getHours()
    const minutes = dateObj.getMinutes()
    const ampm = hours >= 12 ? 'PM' : 'AM'

    hours = hours % 12
    hours = hours ? hours : 12 // 0 should be 12

    const minutesStr = minutes < 10 ? '0' + minutes : minutes

    return `${hours}:${minutesStr} ${ampm}`
  }

  /**
   * Format time range as "12:00 PM - 1:00 PM"
   */
  const formatTimeRange = (startDate, endDate) => {
    return `${formatTimeForPopup(startDate)} - ${formatTimeForPopup(endDate)}`
  }

  /**
   * Calculate the date range to fetch events for based on current view.
   *
   * For week view: Get start of week to end of week
   * For month view: Get start of month to end of month
   * For day view: Get start of day to end of day
   * For agenda view: Get current date to 30 days in future
   *
   * @param {Date} date - The current date being viewed
   * @param {string} viewType - The current view type (week/month/day/agenda)
   * @returns {Object} { start: Date, end: Date }
   */
  const getDateRange = (date, viewType) => {
    const start = new Date(date)
    const end = new Date(date)

    switch (viewType) {
      case 'week':
        // Get start of week (Sunday) and end of week (Saturday)
        start.setDate(date.getDate() - date.getDay())
        end.setDate(start.getDate() + 6)
        break

      case 'month':
        // Get first day of month and last day of month
        start.setDate(1)
        end.setMonth(date.getMonth() + 1)
        end.setDate(0)
        break

      case 'day':
        // Just the current day
        break

      case 'agenda':
        // Current date to 30 days in future
        end.setDate(date.getDate() + 30)
        break

      default:
        break
    }

    // Set time to start/end of day for clean API calls
    start.setHours(0, 0, 0, 0)
    end.setHours(23, 59, 59, 999)

    return { start, end }
  }

  /**
   * Convert API event format to react-big-calendar format.
   *
   * API format: { id, title, start: "ISO string", end: "ISO string", description }
   * Calendar format: { id, title, start: Date object, end: Date object, description }
   *
   * @param {Array} apiEvents - Events from /api/calendar/events
   * @returns {Array} Events formatted for react-big-calendar
   */
  const formatEventsForCalendar = (apiEvents) => {
    return apiEvents.map(event => ({
      id: event.id,
      title: event.title,
      start: new Date(event.start),  // Convert ISO string to Date object
      end: new Date(event.end),      // Convert ISO string to Date object
      description: event.description || ''
    }))
  }

  // ==================== API Calls ====================

  /**
   * Fetch events from Google Calendar API for the specified date range.
   *
   * Calls /api/calendar/events with start and end query parameters.
   * Converts the response to react-big-calendar format and updates state.
   *
   * @param {Date} start - Start of date range
   * @param {Date} end - End of date range
   */
  const fetchEvents = useCallback(async (start, end) => {
    try {
      setLoading(true)
      setError(null)

      // Format dates as ISO strings for API call
      const startISO = start.toISOString()
      const endISO = end.toISOString()

      // Call backend API to fetch events
      // This endpoint queries Google Calendar API and returns events
      // Note: axios instance already has baseURL '/api', so we just use '/calendar/events'
      const response = await api.get('/calendar/events', {
        params: {
          start: startISO,
          end: endISO
        }
      })

      if (response.data.success) {
        // Convert API format to calendar format and update state
        const formattedEvents = formatEventsForCalendar(response.data.events)
        setEvents(formattedEvents)
      } else {
        // API returned success: false
        setError(response.data.error || 'Failed to fetch events')
      }

      setLoading(false)
    } catch (err) {
      // Network error or API error
      console.error('Error fetching calendar events:', err)
      setError('Failed to load calendar events. Please try again.')
      setLoading(false)
    }
  }, [])

  // ==================== Effects ====================

  /**
   * Fetch events when component mounts or when date/view changes.
   *
   * This ensures the calendar always shows events for the current view.
   */
  useEffect(() => {
    const { start, end } = getDateRange(date, view)
    fetchEvents(start, end)
  }, [date, view, fetchEvents])

  // ==================== Event Handlers ====================

  /**
   * Handle view change (week/month/day/agenda).
   *
   * Updates the view state, which triggers useEffect to fetch new events.
   *
   * @param {string} newView - The new view type
   */
  const handleViewChange = (newView) => {
    setView(newView)
  }

  /**
   * Handle navigation (prev/next/today buttons).
   *
   * Updates the date state, which triggers useEffect to fetch new events.
   *
   * @param {Date} newDate - The new date to navigate to
   */
  const handleNavigate = (newDate) => {
    setDate(newDate)
  }

  /**
   * Handle event selection (user clicks on an event).
   *
   * Shows event details in a popup.
   *
   * @param {Object} event - The clicked event
   */
  const handleSelectEvent = (event) => {
    setSelectedEvent(event)
  }

  /**
   * Close the event details popup
   */
  const closeEventPopup = () => {
    setSelectedEvent(null)
  }

  // Close popup on Escape key press
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && selectedEvent) {
        closeEventPopup()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [selectedEvent])

  /**
   * Handle slot selection (user clicks on empty time slot).
   *
   * This could be used to create a new event at the clicked time.
   * For now, we just log it - event creation happens via chat interface.
   *
   * @param {Object} slotInfo - Info about the selected slot
   */
  const handleSelectSlot = (slotInfo) => {
    console.log('Selected slot:', slotInfo)
    // TODO: Could trigger event creation modal here
  }

  /**
   * Refresh calendar events (called after creating/editing/deleting via chat).
   *
   * This is exposed to parent component (Dashboard) so it can refresh
   * the calendar after a successful chat command.
   */
  const refreshCalendar = useCallback(() => {
    const { start, end } = getDateRange(date, view)
    fetchEvents(start, end)
  }, [date, view, fetchEvents])

  // Expose refresh function to parent via callback
  useEffect(() => {
    if (onEventUpdate) {
      onEventUpdate(refreshCalendar)
    }
  }, [refreshCalendar, onEventUpdate])

  // ==================== Render ====================

  // Show loading state
  if (loading && events.length === 0) {
    return (
      <div className="calendar-loading">
        <p>Loading calendar...</p>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="calendar-error">
        <p>⚠️ {error}</p>
        <button onClick={() => fetchEvents(...getDateRange(date, view))}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="calendar-container">
      <BigCalendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        style={{ height: '100%', width: '100%' }}
        view={view}
        onView={handleViewChange}
        date={date}
        onNavigate={handleNavigate}
        onSelectEvent={handleSelectEvent}
        onSelectSlot={handleSelectSlot}
        selectable
        popup
        defaultView="week"  // Default to week view per requirements
        views={['month', 'week', 'day', 'agenda']}
        scrollToTime={new Date(1970, 1, 1, 8, 0, 0)}  // Scroll to 8:00 AM by default
        components={{
          toolbar: CustomToolbar  // Use custom toolbar instead of default
        }}
      />

      {/* Event Details Popup */}
      {selectedEvent && (
        <div className="event-popup-overlay" onClick={closeEventPopup}>
          <div className="event-popup" onClick={(e) => e.stopPropagation()}>
            {/* Close button */}
            <button className="event-popup-close" onClick={closeEventPopup}>
              ×
            </button>

            {/* Event details */}
            <div className="event-popup-content">
              <h3 className="event-popup-title">{selectedEvent.title}</h3>
              <div className="event-popup-detail">
                <span className="event-popup-label">Date:</span>
                <span className="event-popup-value">
                  {formatDateForPopup(selectedEvent.start)}
                </span>
              </div>
              <div className="event-popup-detail">
                <span className="event-popup-label">Time:</span>
                <span className="event-popup-value">
                  {formatTimeRange(selectedEvent.start, selectedEvent.end)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Calendar
