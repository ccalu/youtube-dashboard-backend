import { API_BASE_URL } from './api';
import type {
  CalendarMonthResponse,
  CalendarEvent,
  CalendarSearchRequest,
  CalendarSearchResponse,
  CreateEventRequest,
  UpdateEventRequest,
} from '@/types/calendar';

class CalendarApiService {
  private async fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new Error(`Calendar API Error: ${errorText}`);
    }
    return response.json();
  }

  getMonth = async (year: number, month: number): Promise<CalendarMonthResponse> => {
    return this.fetchApi(`/api/calendar/month/${year}/${month}`);
  };

  getDay = async (date: string): Promise<CalendarEvent[]> => {
    return this.fetchApi(`/api/calendar/day/${date}`);
  };

  createEvent = async (data: CreateEventRequest): Promise<CalendarEvent> => {
    return this.fetchApi('/api/calendar/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  getEvent = async (id: number): Promise<CalendarEvent> => {
    return this.fetchApi(`/api/calendar/event/${id}`);
  };

  updateEvent = async (id: number, data: UpdateEventRequest): Promise<CalendarEvent> => {
    return this.fetchApi(`/api/calendar/event/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  };

  deleteEvent = async (id: number): Promise<void> => {
    await this.fetchApi(`/api/calendar/event/${id}`, {
      method: 'DELETE',
    });
  };

  searchEvents = async (filters: CalendarSearchRequest): Promise<CalendarSearchResponse> => {
    return this.fetchApi('/api/calendar/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters),
    });
  };
}

export const calendarApiService = new CalendarApiService();
