import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2, Clock, History, GripVertical, Save, XCircle } from 'lucide-react';

/**
 * Componente do Kanban Individual de cada canal
 *
 * Features:
 * - Drag & drop para mudar status
 * - CRUD de notas com cores
 * - Histórico de ações
 * - Drag & drop de notas para reordenar
 */

// Cores disponíveis para notas
const NOTE_COLORS = {
  yellow: { bg: 'bg-yellow-50', border: 'border-yellow-300', icon: '🟡' },
  green: { bg: 'bg-green-50', border: 'border-green-300', icon: '🟢' },
  blue: { bg: 'bg-blue-50', border: 'border-blue-300', icon: '🔵' },
  purple: { bg: 'bg-purple-50', border: 'border-purple-300', icon: '🟣' },
  red: { bg: 'bg-red-50', border: 'border-red-300', icon: '🔴' },
  orange: { bg: 'bg-orange-50', border: 'border-orange-300', icon: '🟠' }
};

const KanbanBoard = ({ board, onClose, onRefresh }) => {
  const [draggedStatus, setDraggedStatus] = useState(false);
  const [draggedNote, setDraggedNote] = useState(null);
  const [showNewNote, setShowNewNote] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [newNote, setNewNote] = useState({ text: '', color: 'yellow' });
  const [loading, setLoading] = useState(false);

  // Mudar status do canal
  const handleStatusChange = async (newStatus) => {
    if (board.canal.status_atual === newStatus) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/kanban/canal/${board.canal.id}/move-status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: newStatus })
      });

      if (!response.ok) throw new Error('Erro ao mudar status');
      onRefresh();
    } catch (err) {
      console.error('Erro ao mudar status:', err);
    } finally {
      setLoading(false);
      setDraggedStatus(false);
    }
  };

  // Criar nova nota
  const handleCreateNote = async () => {
    if (!newNote.text.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/kanban/canal/${board.canal.id}/note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          note_text: newNote.text,
          note_color: newNote.color
        })
      });

      if (!response.ok) throw new Error('Erro ao criar nota');
      setNewNote({ text: '', color: 'yellow' });
      setShowNewNote(false);
      onRefresh();
    } catch (err) {
      console.error('Erro ao criar nota:', err);
    } finally {
      setLoading(false);
    }
  };

  // Atualizar nota
  const handleUpdateNote = async (noteId, text, color) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/kanban/note/${noteId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          note_text: text,
          note_color: color
        })
      });

      if (!response.ok) throw new Error('Erro ao atualizar nota');
      setEditingNote(null);
      onRefresh();
    } catch (err) {
      console.error('Erro ao atualizar nota:', err);
    } finally {
      setLoading(false);
    }
  };

  // Deletar nota
  const handleDeleteNote = async (noteId) => {
    if (!confirm('Tem certeza que deseja deletar esta nota?')) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/kanban/note/${noteId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Erro ao deletar nota');
      onRefresh();
    } catch (err) {
      console.error('Erro ao deletar nota:', err);
    } finally {
      setLoading(false);
    }
  };

  // Reordenar notas
  const handleReorderNotes = async (notePositions) => {
    try {
      const response = await fetch(`/api/kanban/canal/${board.canal.id}/reorder-notes`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note_positions: notePositions })
      });

      if (!response.ok) throw new Error('Erro ao reordenar notas');
      onRefresh();
    } catch (err) {
      console.error('Erro ao reordenar notas:', err);
    }
  };

  // Formatar data
  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />

      <div className="absolute inset-4 md:inset-8 bg-white rounded-lg shadow-2xl flex flex-col max-w-6xl mx-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900 flex items-center gap-2">
                <span>📺</span>
                {board.canal.nome}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Status atual: <span className="font-medium">{board.canal.status_atual}</span>
                {board.canal.dias_no_status > 0 && (
                  <span className="ml-2">(há {board.canal.dias_no_status} dias)</span>
                )}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={24} className="text-gray-500" />
            </button>
          </div>
        </div>

        {/* Colunas do Kanban */}
        <div className="p-6 border-b border-gray-200">
          <div className="grid grid-cols-3 md:grid-cols-4 gap-4">
            {board.colunas.map(coluna => (
              <div
                key={coluna.id}
                className={`
                  relative p-4 rounded-lg border-2 transition-all cursor-pointer
                  ${coluna.is_current
                    ? 'bg-blue-50 border-blue-400 shadow-md'
                    : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                  }
                `}
                onClick={() => handleStatusChange(coluna.id)}
                onDragEnter={(e) => {
                  e.preventDefault();
                  if (draggedStatus) handleStatusChange(coluna.id);
                }}
                onDragOver={(e) => e.preventDefault()}
              >
                <div className="text-center">
                  <div className="text-2xl mb-2">{coluna.emoji}</div>
                  <div className="font-medium text-sm">{coluna.label}</div>
                  {coluna.is_current && (
                    <div
                      className="mt-2 w-6 h-6 bg-blue-600 rounded-full mx-auto cursor-move"
                      draggable
                      onDragStart={() => setDraggedStatus(true)}
                      onDragEnd={() => setDraggedStatus(false)}
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 text-center mt-3">
            ↑ Arraste o ponto azul ou clique na coluna para mudar o status
          </p>
        </div>

        {/* Notas */}
        <div className="flex-1 overflow-auto p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <span>📝</span>
              Notas
            </h3>
            <button
              onClick={() => setShowNewNote(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              <Plus size={16} />
              Nova Nota
            </button>
          </div>

          {/* Formulário de nova nota */}
          {showNewNote && (
            <div className="mb-4 p-4 border-2 border-blue-200 rounded-lg bg-blue-50">
              <div className="space-y-3">
                <div className="flex gap-2">
                  {Object.entries(NOTE_COLORS).map(([color, style]) => (
                    <button
                      key={color}
                      onClick={() => setNewNote({ ...newNote, color })}
                      className={`
                        p-2 rounded-lg border-2 transition-all
                        ${newNote.color === color
                          ? 'border-gray-800 shadow-md scale-110'
                          : 'border-gray-300 hover:border-gray-400'
                        }
                      `}
                    >
                      <span className="text-xl">{style.icon}</span>
                    </button>
                  ))}
                </div>
                <textarea
                  value={newNote.text}
                  onChange={(e) => setNewNote({ ...newNote, text: e.target.value })}
                  placeholder="Digite sua nota aqui..."
                  className="w-full p-3 border border-gray-300 rounded-lg resize-none"
                  rows="3"
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleCreateNote}
                    disabled={!newNote.text.trim() || loading}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Salvar
                  </button>
                  <button
                    onClick={() => {
                      setShowNewNote(false);
                      setNewNote({ text: '', color: 'yellow' });
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Lista de notas */}
          <div className="space-y-3">
            {board.notas.map((nota) => (
              <div
                key={nota.id}
                className={`
                  relative p-4 rounded-lg border-2 transition-all
                  ${NOTE_COLORS[nota.note_color]?.bg}
                  ${NOTE_COLORS[nota.note_color]?.border}
                `}
                draggable
                onDragStart={() => setDraggedNote(nota.id)}
                onDragEnd={() => setDraggedNote(null)}
              >
                {editingNote === nota.id ? (
                  <div className="space-y-3">
                    <textarea
                      defaultValue={nota.note_text}
                      className="w-full p-2 border border-gray-300 rounded"
                      rows="3"
                      id={`edit-${nota.id}`}
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          const text = document.getElementById(`edit-${nota.id}`).value;
                          handleUpdateNote(nota.id, text, nota.note_color);
                        }}
                        className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                      >
                        <Save size={14} className="inline mr-1" />
                        Salvar
                      </button>
                      <button
                        onClick={() => setEditingNote(null)}
                        className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>{NOTE_COLORS[nota.note_color]?.icon}</span>
                        <span>{formatDateTime(nota.created_at)}</span>
                        {nota.updated_at && (
                          <span className="italic">(editado)</span>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setEditingNote(nota.id)}
                          className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                        >
                          <Edit2 size={14} className="text-gray-600" />
                        </button>
                        <button
                          onClick={() => handleDeleteNote(nota.id)}
                          className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                        >
                          <Trash2 size={14} className="text-red-600" />
                        </button>
                        <GripVertical size={14} className="text-gray-400 cursor-move" />
                      </div>
                    </div>
                    <div className="mt-2 text-gray-700 whitespace-pre-wrap">
                      {nota.note_text}
                    </div>
                  </>
                )}
              </div>
            ))}

            {board.notas.length === 0 && !showNewNote && (
              <div className="text-center py-8 text-gray-500">
                <p>Nenhuma nota ainda.</p>
                <p className="text-sm">Clique em "Nova Nota" para adicionar.</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer com botão de histórico */}
        <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <History size={16} />
            {showHistory ? 'Ocultar Histórico' : 'Ver Histórico'}
          </button>
        </div>

        {/* Modal de Histórico */}
        {showHistory && (
          <KanbanHistory
            canalId={board.canal.id}
            onClose={() => setShowHistory(false)}
          />
        )}
      </div>
    </div>
  );
};

// Componente de Histórico (simplificado)
const KanbanHistory = ({ canalId, onClose }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch(`/api/kanban/canal/${canalId}/history`);
      const data = await response.json();
      setHistory(data);
    } catch (err) {
      console.error('Erro ao buscar histórico:', err);
    } finally {
      setLoading(false);
    }
  };

  const deleteHistoryItem = async (historyId) => {
    try {
      await fetch(`/api/kanban/history/${historyId}`, { method: 'DELETE' });
      fetchHistory();
    } catch (err) {
      console.error('Erro ao deletar item:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-60 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="absolute right-0 top-0 bottom-0 w-96 bg-white shadow-2xl">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Histórico</h3>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
              <X size={20} />
            </button>
          </div>
        </div>
        <div className="overflow-auto h-full pb-20">
          {loading ? (
            <div className="p-4">Carregando...</div>
          ) : (
            <div className="p-4 space-y-3">
              {history.map(item => (
                <div key={item.id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between">
                    <div className="text-sm">
                      <p className="font-medium">{item.description}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(item.performed_at).toLocaleString('pt-BR')}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteHistoryItem(item.id)}
                      className="p-1 hover:bg-gray-200 rounded"
                    >
                      <Trash2 size={14} className="text-gray-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KanbanBoard;