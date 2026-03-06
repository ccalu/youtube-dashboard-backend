// =========================================================================
// CALENDAR TYPES & CONSTANTS
// =========================================================================

export interface CalendarEvent {
  id: number;
  title: string;
  description: string | null;
  event_date: string; // "YYYY-MM-DD"
  created_by: string; // socio key
  category: string | null;
  event_type: string; // "normal" | "monetizacao" | "desmonetizacao"
  author_name: string;
  author_emoji: string;
  created_at: string;
  updated_at: string;
}

export type CalendarMonthResponse = Record<string, CalendarEvent[]>;

export interface CalendarSearchRequest {
  query?: string;
  authors?: string[];
  categories?: string[];
  date_from?: string;
  date_to?: string;
}

export interface CalendarSearchResponse {
  events: CalendarEvent[];
  results?: CalendarEvent[];
  total: number;
}

export interface CreateEventRequest {
  title: string;
  description?: string;
  event_date: string;
  created_by: string;
  event_type?: string;
  category?: string;
}

export interface UpdateEventRequest {
  title?: string;
  description?: string;
  event_date?: string;
  created_by?: string;
  event_type?: string;
  category?: string;
}

// =========================================================================
// CONSTANTS
// =========================================================================

export const SOCIOS = [
  { key: 'cellibs', name: 'Cellibs', emoji: '🎭' },
  { key: 'arthur', name: 'Arthur', emoji: '📑' },
  { key: 'lucca', name: 'Lucca', emoji: '🎬' },
  { key: 'joao', name: 'João', emoji: '🎨' },
] as const;

export const CATEGORIAS = [
  { key: 'geral', label: 'Geral', emoji: '📋', color: 'yellow' },
  { key: 'desenvolvimento', label: 'Desenvolvimento', emoji: '💻', color: 'blue' },
  { key: 'financeiro', label: 'Financeiro', emoji: '💰', color: 'emerald' },
  { key: 'urgente', label: 'Urgente', emoji: '🚨', color: 'red' },
] as const;

export const EVENT_TYPES = [
  { key: 'normal', label: 'Normal', emoji: '📍' },
  { key: 'monetizacao', label: 'Monetização', emoji: '💸' },
  { key: 'desmonetizacao', label: 'Desmonetização', emoji: '❌' },
] as const;

export const MONTHS_PT = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
] as const;

export const WEEKDAYS_PT = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'] as const;

export const WEEKDAYS_PT_FULL = [
  'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
  'Quinta-feira', 'Sexta-feira', 'Sábado',
] as const;

export function getSocioByKey(key: string) {
  return SOCIOS.find(s => s.key === key);
}

export function getCategoriaByKey(key: string) {
  return CATEGORIAS.find(c => c.key === key);
}
