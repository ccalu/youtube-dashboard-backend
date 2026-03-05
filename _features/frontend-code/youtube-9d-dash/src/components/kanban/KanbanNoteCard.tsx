/**
 * Individual note card with edit modal and expand on click with scrolling
 */

import { useState } from 'react';
import { GripVertical, Edit2, Trash2, X } from 'lucide-react';
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
import { NOTE_COLORS, type KanbanNota, type NoteColor } from '@/types/kanban';

interface KanbanNoteCardProps {
  nota: KanbanNota;
  onEdit: (noteId: number, text: string, color: NoteColor) => void;
  onDelete: (noteId: number) => void;
  onDragStart: (e: React.DragEvent) => void;
  onDragEnd: (e: React.DragEvent) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  isDragging?: boolean;
}

const getNoteColorClasses = (color: NoteColor) => {
  const colorMap: Record<NoteColor, string> = {
    yellow: 'bg-yellow-100 border-yellow-300 dark:bg-yellow-900/30 dark:border-yellow-700',
    green: 'bg-green-100 border-green-300 dark:bg-green-900/30 dark:border-green-700',
    blue: 'bg-blue-100 border-blue-300 dark:bg-blue-900/30 dark:border-blue-700',
    purple: 'bg-purple-100 border-purple-300 dark:bg-purple-900/30 dark:border-purple-700',
    red: 'bg-red-100 border-red-300 dark:bg-red-900/30 dark:border-red-700',
    orange: 'bg-orange-100 border-orange-300 dark:bg-orange-900/30 dark:border-orange-700',
  };
  return colorMap[color] || colorMap.yellow;
};

export const KanbanNoteCard = ({
  nota,
  onEdit,
  onDelete,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
}: KanbanNoteCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editText, setEditText] = useState(nota.note_text);
  const [editColor, setEditColor] = useState<NoteColor>(nota.note_color);
  const [isDragging, setIsDragging] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleSave = () => {
    onEdit(nota.id, editText, editColor);
    setIsEditModalOpen(false);
  };

  const handleOpenEditModal = () => {
    setEditText(nota.note_text);
    setEditColor(nota.note_color);
    setIsEditModalOpen(true);
  };

  const handleCardClick = (e: React.MouseEvent) => {
    if (isDragging) return;
    const target = e.target as HTMLElement;
    if (target.closest('button') || target.closest('.grip-handle')) return;
    setIsExpanded(!isExpanded);
  };

  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('text/plain', String(nota.id));
    e.dataTransfer.setData('application/note-id', String(nota.id));
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.dropEffect = 'move';
    setIsDragging(true);
    onDragStart(e);
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    requestAnimationFrame(() => onDragEnd({} as React.DragEvent));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    onDragOver(e);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    onDrop(e);
  };

  // Keep preview compact so huge notes never break the board layout
  const previewText = nota.note_text.length > 100 
    ? nota.note_text.slice(0, 100) + '...' 
    : nota.note_text;

  return (
    <>
      {/* Collapsed Card */}
      <div
        className={`p-3 rounded-lg border-2 transition-all cursor-pointer hover:shadow-md select-none cursor-grab active:cursor-grabbing ${getNoteColorClasses(
          nota.note_color
        )} ${
          isDragging ? 'opacity-50 scale-95' : ''
        } ${isDragOver ? 'ring-2 ring-primary ring-offset-2 scale-[1.02]' : ''}`}
        draggable={!isExpanded && !isEditModalOpen}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleCardClick}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2 flex-1 min-w-0">
            <GripVertical className="grip-handle h-4 w-4 mt-1 cursor-move text-muted-foreground shrink-0" />
            <p className="flex-1 text-sm text-foreground line-clamp-2 break-words">
              {previewText}
            </p>
          </div>

          <div className="flex gap-1 shrink-0">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleOpenEditModal();
              }}
              className="p-1.5 hover:bg-background/50 rounded transition-colors"
              title="Editar"
            >
              <Edit2 className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(nota.id);
              }}
              className="p-1.5 hover:bg-background/50 rounded transition-colors text-destructive"
              title="Deletar"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Overlay - Read Only with Scroll */}
      {isExpanded && (
        <div 
          className="fixed inset-0 z-[60] flex items-center justify-center bg-background/90 backdrop-blur-sm animate-fade-in"
          onClick={() => setIsExpanded(false)}
        >
          <div 
            className={`relative w-[90vw] max-w-3xl p-6 rounded-xl border-2 shadow-2xl animate-scale-in ${getNoteColorClasses(nota.note_color)}`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setIsExpanded(false)}
              className="absolute top-3 right-3 p-1.5 hover:bg-background/50 rounded-full transition-colors"
            >
              <X className="h-5 w-5 text-muted-foreground" />
            </button>

            {/* Note content with styled scroll */}
            <div className="mt-8 max-h-[60vh] overflow-y-auto pr-3 scrollbar-thin scrollbar-thumb-foreground/20 scrollbar-track-transparent">
              <p className="text-base text-foreground whitespace-pre-wrap break-words leading-relaxed">
                {nota.note_text}
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex justify-end gap-2 mt-4 pt-4 border-t border-border/50">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setIsExpanded(false);
                  handleOpenEditModal();
                }}
              >
                <Edit2 className="h-4 w-4 mr-2" />
                Editar
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => {
                  setIsExpanded(false);
                  onDelete(nota.id);
                }}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Deletar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal - Large Dialog */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Editar Nota</DialogTitle>
            <DialogDescription>
              Edite o conteúdo e a cor da sua nota
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <Textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="min-h-[200px] resize-y"
              placeholder="Digite sua nota..."
              autoFocus
            />

            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-sm text-muted-foreground">Cor:</span>
              {NOTE_COLORS.map((color) => (
                <button
                  key={color.value}
                  onClick={() => setEditColor(color.value)}
                  className={`w-8 h-8 rounded-lg ${color.bg} ${color.border} border-2 transition-all hover:scale-110 ${
                    editColor === color.value
                      ? 'ring-2 ring-offset-2 ring-primary scale-110'
                      : ''
                  }`}
                  title={color.label}
                />
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSave}>
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
