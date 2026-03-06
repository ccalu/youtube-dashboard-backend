/**
 * Kanban API Service
 * All endpoints for the Kanban management system
 */

import { API_BASE_URL } from './api';
import type {
  KanbanStructure,
  KanbanBoardData,
  KanbanNota,
  KanbanHistoryItem,
  CreateNoteRequest,
  UpdateNoteRequest,
  ReorderNotesRequest,
  MoveNoteRequest,
} from '@/types/kanban';

export class KanbanApiError extends Error {
  status: number;
  endpoint: string;
  statusText: string;
  bodyText?: string;

  constructor(params: { endpoint: string; status: number; statusText: string; bodyText?: string }) {
    super(`API Error ${params.status}${params.statusText ? `: ${params.statusText}` : ''}`);
    this.name = 'KanbanApiError';
    this.status = params.status;
    this.endpoint = params.endpoint;
    this.statusText = params.statusText;
    this.bodyText = params.bodyText;
  }
}

class KanbanApiService {
  private fetchApi = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
    try {
      console.log('🎯 Kanban API:', `${API_BASE_URL}${endpoint}`);
      const { getAuthHeaders, handle401 } = await import('@/lib/authFetch');
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
          ...options?.headers,
        },
      });

      if (response.status === 401) { handle401(response); throw new Error('Session expired'); }
      if (!response.ok) {
        const errorText = await response.text();
        console.error('🎯 Kanban API Error:', response.status, errorText);
        throw new KanbanApiError({
          endpoint,
          status: response.status,
          statusText: response.statusText,
          bodyText: errorText,
        });
      }

      // Some endpoints may return 204 or an envelope like { success, message, data }
      const text = await response.text();
      if (!text) {
        console.log('🎯 Kanban API Success (empty body):', endpoint);
        return undefined as T;
      }

      const json = JSON.parse(text);

      // Unwrap common API envelope format
      if (
        json &&
        typeof json === 'object' &&
        'success' in json &&
        'data' in json
      ) {
        console.log('🎯 Kanban API Success (enveloped):', endpoint);
        return (json as any).data as T;
      }

      console.log('🎯 Kanban API Success:', endpoint);
      return json as T;
    } catch (error) {
      console.error('🎯 Kanban Fetch failed:', endpoint, error);
      throw error;
    }
  };

  // =========================================================================
  // STRUCTURE - Main hierarchical view
  // =========================================================================

  /**
   * Get complete Kanban structure (Monetizados/Não Monetizados grouped by subnicho)
   */
  async getStructure(): Promise<KanbanStructure> {
    return this.fetchApi<KanbanStructure>('/api/kanban/structure');
  }

  // =========================================================================
  // BOARD - Individual channel board
  // =========================================================================

  /**
   * Get individual channel Kanban board with columns, notes, and history
   */
  async getChannelBoard(canalId: number): Promise<KanbanBoardData> {
    return this.fetchApi<KanbanBoardData>(`/api/kanban/canal/${canalId}/board`);
  }

  /**
   * Move channel to a different status column
   */
  async moveStatus(canalId: number, newStatus: string): Promise<void> {
    await this.fetchApi(`/api/kanban/canal/${canalId}/move-status`, {
      method: 'PATCH',
      body: JSON.stringify({ new_status: newStatus }),
    });
  }

  // =========================================================================
  // NOTES - CRUD operations
  // =========================================================================

  /**
   * Create a new note for a channel
   */
  async createNote(canalId: number, data: CreateNoteRequest): Promise<KanbanNota> {
    return this.fetchApi<KanbanNota>(`/api/kanban/canal/${canalId}/note`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Update an existing note
   */
  async updateNote(noteId: number, data: UpdateNoteRequest): Promise<KanbanNota> {
    return this.fetchApi<KanbanNota>(`/api/kanban/note/${noteId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  /**
   * Delete a note
   */
  async deleteNote(noteId: number): Promise<void> {
    await this.fetchApi(`/api/kanban/note/${noteId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Move a note to a different column (stage)
   */
  async moveNote(noteId: number, stageId: string): Promise<KanbanNota> {
    return this.fetchApi<KanbanNota>(`/api/kanban/note/${noteId}/move`, {
      method: 'PATCH',
      body: JSON.stringify({ stage_id: stageId }),
    });
  }

  /**
   * Reorder notes (drag & drop)
   */
  async reorderNotes(canalId: number, data: ReorderNotesRequest): Promise<void> {
    await this.fetchApi(`/api/kanban/canal/${canalId}/reorder-notes`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // =========================================================================
  // HISTORY - Activity logs
  // =========================================================================

  /**
   * Get channel activity history
   */
  async getHistory(canalId: number): Promise<KanbanHistoryItem[]> {
    return this.fetchApi<KanbanHistoryItem[]>(`/api/kanban/canal/${canalId}/history`);
  }

  /**
   * Soft delete a history item
   */
  async deleteHistoryItem(historyId: number): Promise<void> {
    await this.fetchApi(`/api/kanban/history/${historyId}`, {
      method: 'DELETE',
    });
  }
}

export const kanbanApiService = new KanbanApiService();
