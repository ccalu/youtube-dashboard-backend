/**
 * TypeScript interfaces for Kanban system
 */

// =====================================================
// STRUCTURE DATA TYPES
// =====================================================

export interface KanbanChannel {
  id: number;
  nome: string;
  lingua: string;
  status_label: string;
  status_color: 'yellow' | 'green' | 'orange' | 'blue' | 'gray';
  status_emoji: string;
  dias_no_status: number;
}

export interface KanbanSubnicho {
  total: number;
  canais: KanbanChannel[];
}

export interface KanbanSection {
  total: number;
  subnichos: Record<string, KanbanSubnicho>;
}

export interface KanbanStructure {
  monetizados: KanbanSection;
  nao_monetizados: KanbanSection;
}

// =====================================================
// BOARD DATA TYPES
// =====================================================

export interface KanbanColuna {
  id: string;
  label: string;
  emoji: string;
  descricao: string;
  is_current: boolean;
}

export interface KanbanNota {
  id: number;
  note_text: string;
  note_color: NoteColor;
  position: number;
  stage_id: string | null; // coluna onde a nota está (independente do status do canal)
  created_at: string;
  updated_at: string;
}

export interface KanbanHistoryItem {
  id: number;
  action_type: string;
  description: string;
  details: Record<string, unknown> | null;
  performed_at: string;
  is_deleted: boolean;
}

export interface KanbanCanalInfo {
  id: number;
  nome: string;
  subnicho: string;
  lingua: string;
  status_atual: string;
  dias_no_status: number;
}

export interface KanbanBoardData {
  canal: KanbanCanalInfo;
  colunas: KanbanColuna[];
  notas: KanbanNota[];
  historico: KanbanHistoryItem[];
}

// =====================================================
// UI TYPES
// =====================================================

export type NoteColor = 'yellow' | 'green' | 'blue' | 'purple' | 'red' | 'orange';

export interface NoteColorConfig {
  value: NoteColor;
  bg: string;
  border: string;
  label: string;
}

export const NOTE_COLORS: NoteColorConfig[] = [
  { value: 'yellow', bg: 'bg-yellow-100', border: 'border-yellow-300', label: 'Amarelo' },
  { value: 'green', bg: 'bg-green-100', border: 'border-green-300', label: 'Verde' },
  { value: 'blue', bg: 'bg-blue-100', border: 'border-blue-300', label: 'Azul' },
  { value: 'purple', bg: 'bg-purple-100', border: 'border-purple-300', label: 'Roxo' },
  { value: 'red', bg: 'bg-red-100', border: 'border-red-300', label: 'Vermelho' },
  { value: 'orange', bg: 'bg-orange-100', border: 'border-orange-300', label: 'Laranja' },
];

// =====================================================
// API REQUEST/RESPONSE TYPES
// =====================================================

export interface MoveStatusRequest {
  new_status: string;
}

export interface CreateNoteRequest {
  note_text: string;
  note_color: NoteColor;
  stage_id?: string; // coluna destino da nota
}

export interface MoveNoteRequest {
  stage_id: string; // nova coluna da nota
}

export interface UpdateNoteRequest {
  note_text: string;
  note_color: NoteColor;
}

export interface ReorderNotesRequest {
  note_positions: { note_id: number; position: number }[];
}
