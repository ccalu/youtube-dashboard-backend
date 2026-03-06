/**
 * Individual channel Kanban board modal
 * Features: 5 status columns, notes with CRUD, drag & drop, history panel
 * Optimized for instant loading and smooth interactions
 * 
 * UPDATED: Card Principal do canal + Notas livres em qualquer coluna
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { History as HistoryIcon, RotateCcw } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { KanbanApiError, kanbanApiService } from '@/services/kanbanApi';
import { supabase } from '@/integrations/supabase/client';
import { getLanguageFlag } from '@/utils/languageFlags';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { cn } from '@/lib/utils';
import { KanbanColumn } from './KanbanColumn';
import { KanbanHistoryPanel } from './KanbanHistoryPanel';
import type { KanbanHistoryItem, KanbanNota, NoteColor } from '@/types/kanban';

type NoteStageOverrides = Record<number, string>;

// Generate temp IDs that are safe for integer range (max 2^31-1 = 2147483647)
// Use a counter + random to avoid collisions within a session
let tempIdCounter = 0;
const generateTempNoteId = () => {
  tempIdCounter += 1;
  // Use a high range but within safe integer bounds (900M-999M range)
  return 900_000_000 + (tempIdCounter % 99_000_000) + Math.floor(Math.random() * 1000);
};

const isTempNoteId = (id: number) => id >= 900_000_000 && id < 1_000_000_000;

const isPgrst116NotFound = (err: unknown) => {
  if (!(err instanceof KanbanApiError)) return false;
  return Boolean(err.bodyText && err.bodyText.includes('PGRST116'));
};

const noteStagesStorageKey = (canalId: number) => `kanban_note_stage_overrides:${canalId}`;

const readNoteStageOverrides = (canalId: number): NoteStageOverrides => {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(noteStagesStorageKey(canalId));
    if (!raw) return {};
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (!parsed || typeof parsed !== 'object') return {};
    const out: NoteStageOverrides = {};
    for (const [k, v] of Object.entries(parsed)) {
      const id = Number(k);
      if (!Number.isFinite(id) || id <= 0) continue;
      if (typeof v !== 'string' || !v.trim()) continue;
      out[id] = v;
    }
    return out;
  } catch {
    return {};
  }
};

const writeNoteStageOverrides = (canalId: number, overrides: NoteStageOverrides) => {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(noteStagesStorageKey(canalId), JSON.stringify(overrides));
  } catch {
    // ignore
  }
};

interface KanbanBoardModalProps {
  canalId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStatusChanged?: () => void;
}

export const KanbanBoardModal = ({
  canalId,
  open,
  onOpenChange,
  onStatusChanged,
}: KanbanBoardModalProps) => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [showHistory, setShowHistory] = useState(false);
  const [draggedStatus, setDraggedStatus] = useState<string | null>(null);
  const [draggedNoteId, setDraggedNoteId] = useState<number | null>(null);
  const [localNotas, setLocalNotas] = useState<KanbanNota[]>([]);
  const [localHistorico, setLocalHistorico] = useState<KanbanHistoryItem[]>([]);
  const [noteStageOverrides, setNoteStageOverrides] = useState<NoteStageOverrides>({});

  // Load persisted stage overrides per channel (so notes never “follow” the Card Principal on reopen/refresh)
  useEffect(() => {
    if (!open || canalId <= 0) return;
    setNoteStageOverrides(readNoteStageOverrides(canalId));
  }, [open, canalId]);

  const setNoteStageOverride = useCallback(
    (noteId: number, stageId: string | null | undefined) => {
      if (canalId <= 0) return;
      setNoteStageOverrides((prev) => {
        const next: NoteStageOverrides = { ...prev };
        if (stageId && stageId.trim()) next[noteId] = stageId;
        else delete next[noteId];
        writeNoteStageOverrides(canalId, next);
        return next;
      });
    },
    [canalId]
  );

  // IMPORTANT (backend shape): responses include BOTH:
  // - stage_id: the *independent* column of the note (what we want)
  // - coluna_id: the *status/current column* of the Card Principal (can change when moving status)
  // So we MUST prefer stage_id, otherwise notes will incorrectly “follow” the Card Principal.
  const getEffectiveStageId = useCallback((nota: KanbanNota): string | null => {
    if (typeof nota.stage_id === 'string' && nota.stage_id.trim()) return nota.stage_id;
    const colunaId = (nota as any)?.coluna_id;
    if (typeof colunaId === 'string' && colunaId.trim()) return colunaId;
    return null;
  }, []);

  const normalizeNota = useCallback(
    (nota: KanbanNota): KanbanNota => ({
      ...nota,
      stage_id: getEffectiveStageId(nota),
    }),
    [getEffectiveStageId]
  );

  // Fetch board data with optimized caching
  const { data, isLoading } = useQuery({
    queryKey: ['kanban-board', canalId],
    queryFn: () => kanbanApiService.getChannelBoard(canalId),
    enabled: open && canalId > 0,
    staleTime: 1000 * 60 * 5, // 5 min cache for instant re-opens
    gcTime: 1000 * 60 * 15,
  });

  // FIX: /api/kanban/canal/:id/board não devolve `lingua` hoje.
  // Buscamos no Supabase só para renderização da bandeira.
  const { data: canalLingua } = useQuery({
    queryKey: ['kanban-board-lingua', canalId],
    enabled: open && canalId > 0,
    staleTime: 1000 * 60 * 60,
    queryFn: async () => {
      const { data, error } = await supabase
        .from('canais_monitorados')
        .select('lingua')
        .eq('id', canalId)
        .maybeSingle();

      if (error) throw error;
      return data?.lingua ?? null;
    },
  });

  // Sync local notes state
  // IMPORTANT: notes are independent. We never allow server refreshes (or Card Principal status changes)
  // to override a note's locally-known stage.
  useEffect(() => {
    if (!open) return;
    if (!data?.notas) return;

    const currentColumnFromServer = (data?.colunas || []).find((c) => c.is_current)?.id ?? null;

    // Use functional setState to avoid stale closures resurrecting notes.
    setLocalNotas((prevLocalNotas) => {
      const previousById = new Map(prevLocalNotas.map((n) => [n.id, n] as const));

      const nextServerNotas = data.notas.map((nota) => {
        const normalized = normalizeNota(nota);
        const prevStage = previousById.get(normalized.id)?.stage_id ?? null;

        // Order of truth:
        // 1) persisted override (user moves/creates)
        // 2) current local stage
        // 3) server-reported stage (stage_id or fallback coluna_id)
        // 4) last resort: current column (do NOT persist this guess)
        const overrideStage = noteStageOverrides[normalized.id] ?? null;
        const resolvedStage =
          overrideStage ??
          prevStage ??
          normalized.stage_id ??
          currentColumnFromServer;

        return {
          ...normalized,
          stage_id: resolvedStage,
        };
      });

      const serverIds = new Set(nextServerNotas.map((n) => n.id));

      // Only keep truly optimistic (temp) notes that haven't been replaced by server yet.
      const optimisticOnly = prevLocalNotas.filter(
        (n) => isTempNoteId(n.id) && !serverIds.has(n.id)
      );

      return [...nextServerNotas, ...optimisticOnly];
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, data?.notas, data?.colunas, normalizeNota, noteStageOverrides]);

  // Sync local history state (so delete/clear happens instantly)
  useEffect(() => {
    if (!open) return;
    if (!data?.historico) return;
    setLocalHistorico(data.historico);
  }, [open, data?.historico]);

  // Move status mutation with optimistic update
  const moveStatusMutation = useMutation({
    mutationFn: (newStatus: string) => kanbanApiService.moveStatus(canalId, newStatus),
    onMutate: async (newStatus) => {
      // Optimistic: immediately update UI
      await queryClient.cancelQueries({ queryKey: ['kanban-board', canalId] });
      const previous = queryClient.getQueryData(['kanban-board', canalId]);
      queryClient.setQueryData(['kanban-board', canalId], (old: any) => ({
        ...old,
        canal: { ...old?.canal, status_atual: newStatus },
        colunas: old?.colunas?.map((col: any) => ({
          ...col,
          is_current: col.id === newStatus,
        })),
      }));
      return { previous };
    },
    onSuccess: () => {
      toast({ title: 'Status atualizado!' });
      // Background sync only - UI already updated optimistically
      queryClient.invalidateQueries({ queryKey: ['kanban-structure'] });
      onStatusChanged?.();
    },
    onError: (_err, _newStatus, context) => {
      queryClient.setQueryData(['kanban-board', canalId], context?.previous);
      toast({ title: 'Erro ao atualizar status', variant: 'destructive' });
    },
  });

  // Create note mutation with optimistic update
  const createNoteMutation = useMutation({
    mutationFn: (data: { text: string; color: NoteColor; stageId: string }) =>
      kanbanApiService.createNote(canalId, { note_text: data.text, note_color: data.color, stage_id: data.stageId }),
    onMutate: async (newNoteData) => {
      // Optimistic: add temp note immediately with safe integer ID
      const tempId = generateTempNoteId();
      const tempNote: KanbanNota = {
        id: tempId,
        note_text: newNoteData.text,
        note_color: newNoteData.color,
        position: localNotas.length + 1,
        stage_id: newNoteData.stageId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setLocalNotas((prev) => [...prev, tempNote]);
      return { tempId: tempNote.id, stageId: newNoteData.stageId };
    },
    onSuccess: (newNote, _vars, context) => {
      // Replace temp note with real one, preserving the column it was created in.
      const normalized = normalizeNota(newNote as any);
      const stageId = context?.stageId ?? normalized.stage_id;
      setLocalNotas((prev) =>
        prev.map((n) => (n.id === context?.tempId ? { ...normalized, stage_id: stageId } : n))
      );

      // Persist the stage so future refetches/reopens never snap this note to the Card Principal column.
      if (typeof (normalized as any)?.id === 'number' && stageId) {
        setNoteStageOverride((normalized as any).id, stageId);
      }

      // Backend may ignore stage_id on creation (returns stage_id/coluna_id null).
      // Persist intended column server-side via /move to avoid any snap to Card Principal.
      const realId = (normalized as any)?.id as number | undefined;
      const serverColunaId = (newNote as any)?.coluna_id as string | null | undefined;
      if (realId && stageId && !serverColunaId && !normalized.stage_id) {
        void kanbanApiService.moveNote(realId, stageId).catch(() => {
          // UI already correct via local override
        });
      }

      toast({ title: 'Nota criada!' });
    },
    onError: (_err, _vars, context) => {
      // Remove temp note on error
      setLocalNotas((prev) => prev.filter((n) => n.id !== context?.tempId));
      toast({ title: 'Erro ao criar nota', variant: 'destructive' });
    },
  });

  // Edit note mutation with optimistic update - preserves stage_id
  const editNoteMutation = useMutation({
    mutationFn: async (data: { noteId: number; text: string; color: NoteColor }) => {
      // Don't send temp IDs to the server - they don't exist yet
      if (isTempNoteId(data.noteId)) {
        // Just update locally, the real note will be created soon
        return null;
      }
      return kanbanApiService.updateNote(data.noteId, { note_text: data.text, note_color: data.color });
    },
    onMutate: async (variables) => {
      // Cancel any outgoing refetches to prevent overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: ['kanban-board', canalId] });
      const previous = [...localNotas];
      // Preserve the current stage_id when editing
      const currentNote = localNotas.find((n) => n.id === variables.noteId);
      setLocalNotas((prev) =>
        prev.map((n) =>
          n.id === variables.noteId
            ? { ...n, note_text: variables.text, note_color: variables.color, stage_id: currentNote?.stage_id ?? n.stage_id }
            : n
        )
      );
      return { previous, preservedStageId: currentNote?.stage_id };
    },
    onSuccess: (updatedNote, variables, context) => {
      // Ensure the note keeps its stage_id after server response
      if (context?.preservedStageId) {
        setLocalNotas((prev) =>
          prev.map((n) =>
            n.id === variables.noteId
              ? { ...n, stage_id: context.preservedStageId }
              : n
          )
        );
      }
      toast({ title: 'Nota atualizada!' });
    },
    onError: (err, vars, context) => {
      // Backend sometimes returns 500 PGRST116 when the row no longer exists.
      // Treat as reconciliation (note already removed) instead of failing.
      if (isPgrst116NotFound(err)) {
        setLocalNotas((prev) => prev.filter((n) => n.id !== vars.noteId));
        setNoteStageOverride(vars.noteId, null);
        toast({ title: 'Nota não encontrada (já removida)' });
        return;
      }

      setLocalNotas(context?.previous || []);
      toast({ title: 'Erro ao atualizar nota', variant: 'destructive' });
    },
  });

  // Delete note mutation with optimistic update
  const deleteNoteMutation = useMutation({
    mutationFn: async (noteId: number) => {
      // Don't send temp IDs to the server - they don't exist yet
      if (isTempNoteId(noteId)) {
        return; // Just remove locally
      }
      return kanbanApiService.deleteNote(noteId);
    },
    onMutate: async (noteId) => {
      const previous = [...localNotas];
      setLocalNotas((prev) => prev.filter((n) => n.id !== noteId));
      setNoteStageOverride(noteId, null);
      return { previous };
    },
    onSuccess: () => {
      toast({ title: 'Nota removida!' });
    },
    onError: (err, noteId, context) => {
      // If backend says PGRST116 (0 rows), the note is already gone.
      // Keep UI removed and avoid showing an error.
      if (isPgrst116NotFound(err)) {
        toast({ title: 'Nota removida!' });
        return;
      }

      setLocalNotas(context?.previous || []);
      const prevStage = context?.previous?.find?.((n: any) => n?.id === noteId)?.stage_id;
      if (typeof prevStage === 'string' && prevStage.trim()) setNoteStageOverride(noteId, prevStage);
      toast({ title: 'Erro ao remover nota', variant: 'destructive' });
    },
  });

  // Move note to different column mutation with optimistic update
  const moveNoteMutation = useMutation({
    mutationFn: async (data: { noteId: number; stageId: string }) => {
      // Don't send temp IDs to the server - they don't exist yet
      if (isTempNoteId(data.noteId)) {
        return null; // Just move locally
      }
      return kanbanApiService.moveNote(data.noteId, data.stageId);
    },
    onMutate: async (variables) => {
      const previous = [...localNotas];
      setLocalNotas((prev) =>
        prev.map((n) =>
          n.id === variables.noteId ? { ...n, stage_id: variables.stageId } : n
        )
      );

      // Persist user's explicit move as source of truth.
      setNoteStageOverride(variables.noteId, variables.stageId);

      return { previous };
    },
    onSuccess: () => {
      toast({ title: 'Nota movida!' });
    },
    onError: (err, vars, context) => {
      // If note doesn't exist (PGRST116), keep the UI state - note was probably just created
      if (isPgrst116NotFound(err)) {
        toast({ title: 'Nota movida!' });
        return;
      }
      setLocalNotas(context?.previous || []);
      toast({ title: 'Erro ao mover nota', variant: 'destructive' });
    },
  });

  // Reorder notes mutation - already optimistic via localNotas
  const reorderNotesMutation = useMutation({
    mutationFn: (positions: { note_id: number; position: number }[]) =>
      kanbanApiService.reorderNotes(canalId, { note_positions: positions }),
    onError: () => {
      toast({ title: 'Erro ao reordenar notas', variant: 'destructive' });
    },
  });

  // Delete history item mutation
  const deleteHistoryMutation = useMutation({
    mutationFn: (historyId: number) => kanbanApiService.deleteHistoryItem(historyId),
    onMutate: async (historyId) => {
      const previous = [...localHistorico];
      setLocalHistorico((prev) => prev.filter((h) => h.id !== historyId));
      return { previous };
    },
    onSuccess: () => {
      toast({ title: 'Item removido do histórico' });
    },
    onError: (err, _historyId, context) => {
      if (isPgrst116NotFound(err)) {
        toast({ title: 'Item removido do histórico' });
        queryClient.invalidateQueries({ queryKey: ['kanban-board', canalId] });
        return;
      }

      if (context?.previous) setLocalHistorico(context.previous);
      toast({ title: 'Erro ao remover item do histórico', variant: 'destructive' });
    },
  });

  // Clear all history (soft delete each item)
  const clearHistoryMutation = useMutation({
    mutationFn: async (historyIds: number[]) => {
      await Promise.all(historyIds.map((id) => kanbanApiService.deleteHistoryItem(id)));
    },
    onMutate: async () => {
      const previous = [...localHistorico];
      setLocalHistorico([]);
      return { previous };
    },
    onSuccess: () => {
      toast({ title: 'Histórico limpo!' });
    },
    onError: (err, _historyIds, context) => {
      if (isPgrst116NotFound(err)) {
        toast({ title: 'Histórico limpo!' });
        queryClient.invalidateQueries({ queryKey: ['kanban-board', canalId] });
        return;
      }

      if (context?.previous) setLocalHistorico(context.previous);
      toast({ title: 'Erro ao limpar histórico', variant: 'destructive' });
    },
  });

  // Reset status mutation - resets the days counter by re-applying current status
  const resetStatusMutation = useMutation({
    mutationFn: async () => {
      const currentStatus = data?.canal?.status_atual;
      if (!currentStatus) throw new Error('Status não encontrado');
      return kanbanApiService.moveStatus(canalId, currentStatus);
    },
    onSuccess: () => {
      toast({ title: 'Contador resetado!', description: 'Dias reiniciados para 0' });
      queryClient.invalidateQueries({ queryKey: ['kanban-board', canalId] });
      queryClient.invalidateQueries({ queryKey: ['kanban-structure'] });
      onStatusChanged?.();
    },
    onError: () => {
      toast({ title: 'Erro ao resetar', variant: 'destructive' });
    },
  });

  // Handle note reordering (within same column)
  const handleReorderNotes = useCallback(
    (draggedId: number, targetId: number) => {
      const draggedIndex = localNotas.findIndex((n) => n.id === draggedId);
      const targetIndex = localNotas.findIndex((n) => n.id === targetId);

      if (draggedIndex === -1 || targetIndex === -1) return;

      const newNotas = [...localNotas];
      const [removed] = newNotas.splice(draggedIndex, 1);
      newNotas.splice(targetIndex, 0, removed);

      setLocalNotas(newNotas);

      const positions = newNotas.map((nota, index) => ({
        note_id: nota.id,
        position: index + 1,
      }));

      reorderNotesMutation.mutate(positions);
    },
    [localNotas, reorderNotesMutation]
  );

  // Handle note moved to different column
  const handleMoveNoteToColumn = useCallback(
    (noteId: number, targetStageId: string) => {
      moveNoteMutation.mutate({ noteId, stageId: targetStageId });
    },
    [moveNoteMutation]
  );

  if (!open) return null;

  const canal = data?.canal;
  const historico = localHistorico;
  
  // Memoize column sorting for performance
  const colunas = useMemo(() => {
    const rawColunas = data?.colunas || [];
    const MONETIZED_ORDER = ['em_testes', 'constante', 'em_crescimento'];
    return rawColunas.length === 3
      ? [...rawColunas].sort((a, b) => {
          const aIdx = MONETIZED_ORDER.indexOf(a.id);
          const bIdx = MONETIZED_ORDER.indexOf(b.id);
          return aIdx - bIdx;
        })
      : rawColunas;
  }, [data?.colunas]);

  // Find current column for status indicator
  const currentColumnId = colunas.find((c) => c.is_current)?.id;

  const isThreeColumnLayout = colunas.length === 3;
  const isFourColumnLayout = colunas.length === 4;
  const columnsWrapperClass = isThreeColumnLayout || isFourColumnLayout ? 'w-full' : 'w-max';
  // Use basis-0 so gaps don't push the last column out of view (4-col layout was overflowing)
  const columnClassName = isThreeColumnLayout || isFourColumnLayout
    ? 'flex-1 basis-0 min-w-0'
    : 'w-[280px] shrink-0';

  const flag = canal ? getLanguageFlag((canal as any)?.lingua ?? canalLingua) : '';
  const emoji = canal ? getSubnichoEmoji(canal.subnicho) : '';
  const cores = canal ? obterCorSubnicho(canal.subnicho) : { fundo: '#6B7280', borda: '#9CA3AF' };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-6xl h-[90vh] p-0 overflow-hidden">
        {/* Header */}
        <DialogHeader
          className="p-4 border-b border-border pr-16"
          style={{ backgroundColor: cores.fundo + '15' }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{flag}</span>
              <div>
                <DialogTitle className="text-lg font-bold flex items-center gap-2">
                  {canal?.nome}
                </DialogTitle>
                <DialogDescription className="text-sm text-muted-foreground flex items-center gap-2 mt-1">
                  <span>{emoji}</span>
                  <span>{canal?.subnicho}</span>
                  <span className="mx-1">•</span>
                  <span>
                    Status: <span className="font-medium text-foreground">{canal?.status_atual}</span>
                  </span>
                  <span className="mx-1">•</span>
                  <span>Há {canal?.dias_no_status} dias</span>
                </DialogDescription>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  if (confirm('Resetar contador de dias do status atual?')) {
                    resetStatusMutation.mutate();
                  }
                }}
                disabled={resetStatusMutation.isPending}
                title="Resetar dias do status"
              >
                <RotateCcw className={cn("h-4 w-4", resetStatusMutation.isPending && "animate-spin")} />
              </Button>
              <Button
                variant={showHistory ? 'secondary' : 'ghost'}
                size="icon"
                onClick={() => setShowHistory(!showHistory)}
                title="Histórico"
              >
                <HistoryIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        {/* Body */}
        <div className="flex-1 flex overflow-hidden h-[calc(90vh-80px)]">
          {/* Kanban Columns */}
          <div className="flex-1 p-4 overflow-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-muted-foreground">Carregando...</div>
              </div>
            ) : (
              <div className={cn('flex flex-nowrap gap-3 min-h-full pb-4', columnsWrapperClass)}>
                {colunas.map((coluna, index) => {
                   // Notes are independent: strictly render by stage_id.
                   const notasDestaColuna = localNotas.filter((n) => n.stage_id === coluna.id);
                   
                   // FIX: O backend pode retornar is_current:false para todas as colunas
                   // quando status_atual não bate exatamente com nenhum coluna.id.
                   // Ex: "Reinos Sombrios" é monetizado mas tem status "em_teste_inicial" (não-monetizado)
                   // Nesse caso, mostrar o card principal na PRIMEIRA coluna como fallback.
                   const anyColumnIsCurrent = colunas.some((c) => c.is_current);
                   const statusMatchesThisColumn = coluna.id === canal?.status_atual;
                   const isFirstColumnFallback = !anyColumnIsCurrent && index === 0;
                   const isCurrentColumn = coluna.is_current || statusMatchesThisColumn || isFirstColumnFallback;
                   const colunaComIs_Current = { ...coluna, is_current: isCurrentColumn };

                  return (
                    <KanbanColumn
                      key={coluna.id}
                      className={columnClassName}
                      coluna={colunaComIs_Current}
                      notas={notasDestaColuna}
                      canalInfo={canal}
                      onStatusChange={(newStatus) => moveStatusMutation.mutate(newStatus)}
                      onCreateNote={(stageId: string, text: string, color: NoteColor) =>
                        createNoteMutation.mutate({ text, color, stageId })
                      }
                      onEditNote={(noteId, text, color) =>
                        editNoteMutation.mutate({ noteId, text, color })
                      }
                      onDeleteNote={(noteId) => {
                        if (confirm('Tem certeza que deseja deletar esta nota?')) {
                          deleteNoteMutation.mutate(noteId);
                        }
                      }}
                      onReorderNotes={handleReorderNotes}
                      onMoveNoteToColumn={handleMoveNoteToColumn}
                      draggedStatus={draggedStatus}
                      draggedNoteId={draggedNoteId}
                      onDragStatusStart={() => setDraggedStatus('status')}
                      onDragStatusEnd={() => setDraggedStatus(null)}
                      onDragNoteStart={(noteId) => setDraggedNoteId(noteId)}
                      onDragNoteEnd={() => setDraggedNoteId(null)}
                    />
                  );
                })}
              </div>
            )}
          </div>

          {/* History Panel */}
          {showHistory && (
            <KanbanHistoryPanel
              historico={historico}
              notas={localNotas}
              onDeleteItem={(id) => deleteHistoryMutation.mutate(id)}
              onClearHistory={() => clearHistoryMutation.mutate(historico.map((h) => h.id))}
              isDeletingItem={deleteHistoryMutation.isPending}
              isClearingHistory={clearHistoryMutation.isPending}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};