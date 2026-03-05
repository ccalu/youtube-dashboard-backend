/**
 * History panel showing channel activity logs
 * Shows note preview for note-related actions
 */

import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ConfirmDeleteDialog } from '@/components/ConfirmDeleteDialog';
import type { KanbanHistoryItem, KanbanNota } from '@/types/kanban';

interface KanbanHistoryPanelProps {
  historico: KanbanHistoryItem[];
  notas: KanbanNota[];
  onDeleteItem: (historyId: number) => void;
  onClearHistory: () => void;
  isDeletingItem?: boolean;
  isClearingHistory?: boolean;
}

const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
};

const getActionIcon = (actionType: string) => {
  switch (actionType) {
    case 'status_change':
      return '🔄';
    case 'note_created':
    case 'note_added':
      return '📝';
    case 'note_updated':
    case 'note_edited':
      return '✏️';
    case 'note_deleted':
      return '🗑️';
    case 'notes_reordered':
      return '↕️';
    default:
      return '📌';
  }
};

const truncateText = (text: string, maxLength: number = 30) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

const normalizeNoteId = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const n = Number(value);
    if (Number.isFinite(n)) return n;
  }
  return undefined;
};

const extractNoteTextFromDetails = (details: Record<string, unknown> | null): string | null => {
  if (!details) return null;

  // Common shapes we may receive from backend
  const directKeys = ['note_text', 'text', 'new_text', 'old_text', 'content', 'note_preview', 'notePreview'];
  for (const k of directKeys) {
    const v = details[k];
    if (typeof v === 'string' && v.trim()) return v;
  }

  // Sometimes the note can be nested
  const nested = details['note'];
  if (nested && typeof nested === 'object') {
    const nt = (nested as Record<string, unknown>)['note_text'];
    if (typeof nt === 'string' && nt.trim()) return nt;
  }

  return null;
};

export const KanbanHistoryPanel = ({
  historico,
  notas,
  onDeleteItem,
  onClearHistory,
  isDeletingItem = false,
  isClearingHistory = false,
}: KanbanHistoryPanelProps) => {
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);

  const getNotePreviewById = (noteId: number | undefined): string | null => {
    if (!noteId) return null;
    const nota = notas.find((n) => n.id === noteId);
    return nota ? truncateText(nota.note_text, 25) : null;
  };

  const getBestNotePreview = (item: KanbanHistoryItem): string | null => {
    const noteId = normalizeNoteId(item.details?.note_id);
    const fromState = getNotePreviewById(noteId);
    if (fromState) return fromState;

    const fromDetails = extractNoteTextFromDetails(item.details);
    return fromDetails ? truncateText(fromDetails, 25) : null;
  };

  // Build description with note preview
  const getEnhancedDescription = (item: KanbanHistoryItem): string => {
    const notePreview = getBestNotePreview(item);
    
    switch (item.action_type) {
      case 'note_edited':
      case 'note_updated':
        if (notePreview) {
          return `Nota editada: "${notePreview}"`;
        }
        return 'Nota editada';
      
      case 'note_added':
      case 'note_created':
        if (notePreview) {
          return `Nota criada: "${notePreview}"`;
        }
        return item.description;
      
      case 'note_deleted':
        if (notePreview) {
          return `Nota removida: "${notePreview}"`;
        }
        return 'Nota removida';
      
      default:
        return item.description;
    }
  };

  return (
    <div className="w-80 border-l border-border bg-muted/30 flex flex-col">
      <div className="p-4 border-b border-border">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-semibold text-foreground">Histórico</h3>
            <p className="text-xs text-muted-foreground mt-1">
              Últimas {Math.min(historico.length, 50)} ações
            </p>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setConfirmClearOpen(true)}
            disabled={historico.length === 0 || isClearingHistory}
            title="Limpar histórico"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-2">
          {historico.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Nenhum histórico registrado
            </p>
          ) : (
            historico.slice(0, 50).map((item) => (
              <div
                key={item.id}
                className="bg-card p-3 rounded-lg border border-border/50 group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm shrink-0">{getActionIcon(item.action_type)}</span>
                      <p className="text-sm font-medium text-foreground line-clamp-2">
                        {getEnhancedDescription(item)}
                      </p>
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {formatDate(item.performed_at)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteTargetId(item.id)}
                    disabled={isDeletingItem}
                    className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                    title="Remover do histórico"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Confirm dialogs */}
      <ConfirmDeleteDialog
        open={confirmClearOpen}
        onOpenChange={setConfirmClearOpen}
        title="Limpar histórico"
        description={`Isso vai remover ${historico.length} itens do histórico deste canal.`}
        confirmText={isClearingHistory ? 'Limpando...' : 'Confirmar'}
        onConfirm={() => {
          onClearHistory();
          setConfirmClearOpen(false);
        }}
      />

      <ConfirmDeleteDialog
        open={deleteTargetId !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTargetId(null);
        }}
        title="Remover item do histórico"
        description="Isso vai remover este item do histórico."
        confirmText={isDeletingItem ? 'Removendo...' : 'Confirmar'}
        onConfirm={() => {
          if (deleteTargetId !== null) onDeleteItem(deleteTargetId);
          setDeleteTargetId(null);
        }}
      />
    </div>
  );
};
