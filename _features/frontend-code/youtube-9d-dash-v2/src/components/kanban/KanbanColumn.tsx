/**
 * Kanban column with status indicator, Card Principal, and notes area
 * 
 * UPDATED: 
 * - Card Principal do canal (arrastável, define status)
 * - Notas livres em qualquer coluna (filtradas por stage_id)
 * - Drop zone para receber notas de outras colunas
 * - Modal para criação de notas
 */

import { useState, type DragEvent } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';
import { KanbanNoteCard } from './KanbanNoteCard';
import { KanbanChannelCard } from './KanbanChannelCard';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { NOTE_COLORS, type KanbanColuna, type KanbanNota, type NoteColor, type KanbanCanalInfo } from '@/types/kanban';

const readDraggedNoteId = (e: DragEvent) => {
  const raw =
    e.dataTransfer.getData('application/note-id') || e.dataTransfer.getData('text/plain');
  const id = Number(raw);
  return Number.isFinite(id) && id > 0 ? id : null;
};

interface KanbanColumnProps {
  className?: string;
  coluna: KanbanColuna;
  notas: KanbanNota[];
  canalInfo?: KanbanCanalInfo;
  onStatusChange: (newStatus: string) => void;
  onCreateNote: (stageId: string, text: string, color: NoteColor) => void;
  onEditNote: (noteId: number, text: string, color: NoteColor) => void;
  onDeleteNote: (noteId: number) => void;
  onReorderNotes: (draggedId: number, targetId: number) => void;
  onMoveNoteToColumn?: (noteId: number, targetStageId: string) => void;
  draggedStatus: string | null;
  draggedNoteId: number | null;
  onDragStatusStart: () => void;
  onDragStatusEnd: () => void;
  onDragNoteStart: (noteId: number) => void;
  onDragNoteEnd: () => void;
}

export const KanbanColumn = ({
  className,
  coluna,
  notas,
  canalInfo,
  onStatusChange,
  onCreateNote,
  onEditNote,
  onDeleteNote,
  onReorderNotes,
  onMoveNoteToColumn,
  draggedStatus,
  draggedNoteId,
  onDragStatusStart,
  onDragStatusEnd,
  onDragNoteStart,
  onDragNoteEnd,
}: KanbanColumnProps) => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newNoteText, setNewNoteText] = useState('');
  const [newNoteColor, setNewNoteColor] = useState<NoteColor>('yellow');
  const [isDragOverColumn, setIsDragOverColumn] = useState(false);

  const handleCreateNote = () => {
    if (!newNoteText.trim()) return;
    onCreateNote(coluna.id, newNoteText, newNoteColor);
    setNewNoteText('');
    setNewNoteColor('yellow');
    setIsCreateModalOpen(false);
  };

  const handleCloseCreateModal = () => {
    setIsCreateModalOpen(false);
    setNewNoteText('');
    setNewNoteColor('yellow');
  };

  // Can drop status indicator here (only non-current columns)
  const canDropStatus = !coluna.is_current && Boolean(draggedStatus);
  // Can drop notes here from any column
  const canDropNote = Boolean(draggedNoteId);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault();
    if (draggedNoteId || draggedStatus) {
      setIsDragOverColumn(true);
    }
  };

  const handleDragLeave = (e: DragEvent) => {
    // Only reset if leaving the column entirely
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const { clientX, clientY } = e;
    if (
      clientX < rect.left ||
      clientX > rect.right ||
      clientY < rect.top ||
      clientY > rect.bottom
    ) {
      setIsDragOverColumn(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOverColumn(false);

    // Read noteId directly from dataTransfer (most reliable)
    const noteIdFromTransfer = readDraggedNoteId(e);

    // Dropping a NOTE to this column = move note to this stage
    if (noteIdFromTransfer && onMoveNoteToColumn) {
      onMoveNoteToColumn(noteIdFromTransfer, coluna.id);
      onDragNoteEnd();
      return;
    }

    // Dropping the status indicator (Card Principal) = change channel status
    if (!coluna.is_current && draggedStatus) {
      onStatusChange(coluna.id);
    }
  };

  const emoji = canalInfo ? getSubnichoEmoji(canalInfo.subnicho) : '📺';

  return (
    <div className={cn('min-w-0 flex flex-col', className)}>
      {/* Column Header */}
      <div
        className={`p-3 rounded-t-lg transition-colors ${
          coluna.is_current ? 'bg-primary/10' : 'bg-muted/50'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{coluna.emoji}</span>
            <h3 className="font-medium text-sm text-foreground">{coluna.label}</h3>
          </div>
        </div>
        <p className="text-[10px] text-muted-foreground mt-1">{coluna.descricao}</p>
      </div>

      {/* Drop zone for status and notes */}
      <div
        className={`flex-1 p-3 bg-muted/30 min-h-[200px] rounded-b-lg border-2 transition-all duration-200 ${
          isDragOverColumn && (canDropStatus || canDropNote)
            ? 'border-primary border-dashed bg-primary/10 scale-[1.01]'
            : 'border-transparent'
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
      <div className="space-y-3">
          {/* CARD PRINCIPAL DO CANAL - Apenas na coluna atual */}
          {coluna.is_current && canalInfo && (
            <div
              className={cn(
                "p-4 rounded-lg border-2 shadow-sm cursor-grab active:cursor-grabbing transition-all hover:shadow-md",
                // Cores dinâmicas baseadas no emoji da coluna
                // 🟡 Amarelo - Em Teste Inicial, Em Testes Novos
                coluna.emoji === '🟡' || coluna.id === 'em_teste_inicial' || coluna.id === 'em_testes' || coluna.id === 'em_testes_novos'
                  ? 'bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20 border-yellow-400 dark:border-yellow-600'
                // 🟢 Verde - Demonstrando Tração, Em Crescimento
                : coluna.emoji === '🟢' || coluna.id === 'demonstrando_tracao' || coluna.id === 'em_crescimento'
                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-400 dark:border-green-600'
                // 🟠 Laranja - Em Andamento p/ Monetizar
                : coluna.emoji === '🟠' || coluna.id === 'em_andamento' || coluna.id === 'em_andamento_monetizar'
                  ? 'bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 border-orange-400 dark:border-orange-600'
                // 🔵 Azul - Monetizado, Canal Constante
                : coluna.emoji === '🔵' || coluna.id === 'monetizado' || coluna.id === 'canal_constante' || coluna.id === 'constante'
                  ? 'bg-gradient-to-r from-blue-50 to-sky-50 dark:from-blue-900/20 dark:to-sky-900/20 border-blue-400 dark:border-blue-600'
                // 🔴 Vermelho - Sem Tração, Pausado
                : coluna.emoji === '🔴' || coluna.id === 'sem_tracao' || coluna.id === 'pausado'
                  ? 'bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20 border-red-400 dark:border-red-600'
                // Default - Azul
                : 'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-300 dark:border-blue-600'
              )}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('text/plain', 'kanban-status');
                e.dataTransfer.effectAllowed = 'move';
                onDragStatusStart();
              }}
              onDragEnd={onDragStatusEnd}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{emoji}</span>
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-foreground truncate">{canalInfo.nome}</h4>
                  <p className="text-xs text-muted-foreground">Arraste para mudar status</p>
                </div>
              </div>
            </div>
          )}

          {/* NOTAS - Filtradas por stage_id para esta coluna */}
          {notas.map((nota) => (
            <KanbanNoteCard
              key={nota.id}
              nota={nota}
              onEdit={onEditNote}
              onDelete={onDeleteNote}
              onDragStart={(e) => {
                onDragNoteStart(nota.id);
              }}
              onDragEnd={(e) => {
                onDragNoteEnd();
              }}
              onDragOver={() => {}}
              onDrop={(e) => {
                const draggedId = readDraggedNoteId(e);
                // Only reorder if same column (stage_id matches)
                if (draggedId && draggedId !== nota.id) {
                  onReorderNotes(draggedId, nota.id);
                }
              }}
            />
          ))}

          {/* Add Note Button */}
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="w-full p-3 border-2 border-dashed border-border rounded-lg hover:border-primary/50 hover:bg-card/50 flex items-center justify-center gap-2 text-muted-foreground transition-all"
          >
            <Plus className="h-4 w-4" />
            <span className="text-sm">Adicionar Nota</span>
          </button>
        </div>
      </div>

      {/* Create Note Modal */}
      <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Nova Nota</DialogTitle>
            <DialogDescription>
              Adicionar nota na coluna: {coluna.emoji} {coluna.label}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <Textarea
              value={newNoteText}
              onChange={(e) => setNewNoteText(e.target.value)}
              className="min-h-[200px] resize-y"
              placeholder="Digite sua nota..."
              autoFocus
            />

            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-sm text-muted-foreground">Cor:</span>
              {NOTE_COLORS.map((color) => (
                <button
                  key={color.value}
                  onClick={() => setNewNoteColor(color.value)}
                  className={`w-8 h-8 rounded-lg ${color.bg} ${color.border} border-2 transition-all hover:scale-110 ${
                    newNoteColor === color.value
                      ? 'ring-2 ring-offset-2 ring-primary scale-110'
                      : ''
                  }`}
                  title={color.label}
                />
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCloseCreateModal}>
              Cancelar
            </Button>
            <Button onClick={handleCreateNote} disabled={!newNoteText.trim()}>
              Adicionar Nota
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
