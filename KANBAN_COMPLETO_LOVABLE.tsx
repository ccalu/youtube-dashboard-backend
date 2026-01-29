/**
 * SISTEMA KANBAN - ARQUIVO COMPLETO PARA LOVABLE
 *
 * ⚠️ ATUALIZAÇÃO IMPORTANTE (29/01/2025):
 * - Adicionado CARD PRINCIPAL do canal (com borda especial e emoji do subnicho)
 * - O CARD PRINCIPAL define o status ao ser movido entre colunas
 * - As NOTAS agora podem estar em QUALQUER coluna (independente do status)
 * - Reinos Sombrios agora aparece nos MONETIZADOS (total: 10 canais)
 *
 * INSTRUÇÕES IMPORTANTES:
 * 1. Este componente deve ser adicionado em "Ferramentas", ABAIXO de "Histórico de Coletas"
 * 2. O LAYOUT DEVE SER IDÊNTICO À ABA "TABELA" - mesmos cards, cores, emojis, estrutura expansível
 * 3. Usar as MESMAS CORES dos subnichos que já existem na aba Tabela
 * 4. Mostrar BANDEIRAS dos idiomas (🇧🇷 pt, 🇺🇸 en, 🇪🇸 es, 🇫🇷 fr)
 * 5. Mostrar NOME COMPLETO dos canais
 * 6. Tags de status coloridas como: [🟡 Em Teste há 49d]
 *
 * ENDPOINTS DA API (todos em /api/kanban/):
 * - GET    /structure                          - Estrutura completa
 * - GET    /canal/{id}/board                   - Kanban individual
 * - PATCH  /canal/{id}/move-status            - Mudar status (body: {new_status})
 * - POST   /canal/{id}/note                   - Criar nota (body: {note_text, note_color})
 * - PATCH  /note/{id}                         - Editar nota (body: {note_text, note_color})
 * - DELETE /note/{id}                         - Deletar nota
 * - PATCH  /canal/{id}/reorder-notes          - Reordenar (body: {note_positions})
 * - GET    /canal/{id}/history                - Histórico do canal
 * - DELETE /history/{id}                      - Soft delete histórico
 */

import React, { useState, useEffect, useRef } from 'react';
import { ChevronRight, ChevronDown, Plus, Edit2, Trash2, GripVertical, X, Clock, Save, Circle, History as HistoryIcon } from 'lucide-react';

// =====================================================
// COMPONENTE PRINCIPAL - KANBAN COMPLETO
// =====================================================

const KanbanCompleto = () => {
  const [estrutura, setEstrutura] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedCards, setExpandedCards] = useState({});
  const [expandedSubnichos, setExpandedSubnichos] = useState({});
  const [selectedCanal, setSelectedCanal] = useState(null);
  const [kanbanData, setKanbanData] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  // Buscar estrutura inicial
  useEffect(() => {
    fetchEstrutura();
  }, []);

  const fetchEstrutura = async () => {
    try {
      const response = await fetch('/api/kanban/structure');
      const data = await response.json();
      setEstrutura(data);
    } catch (error) {
      console.error('Erro ao buscar estrutura:', error);
    } finally {
      setLoading(false);
    }
  };

  // Buscar dados do kanban individual
  const fetchKanbanBoard = async (canalId) => {
    try {
      const response = await fetch(`/api/kanban/canal/${canalId}/board`);
      const data = await response.json();
      setKanbanData(data);
      setSelectedCanal(canalId);
    } catch (error) {
      console.error('Erro ao buscar kanban:', error);
    }
  };

  // Função para obter bandeira do idioma
  const getBandeira = (lingua) => {
    const bandeiras = {
      'portuguese': '🇧🇷',
      'english': '🇺🇸',
      'spanish': '🇪🇸',
      'french': '🇫🇷'
    };
    return bandeiras[lingua] || '🏳️';
  };

  // Função para obter cor do status
  const getStatusColor = (color) => {
    const colors = {
      'yellow': 'bg-yellow-100 text-yellow-800',
      'green': 'bg-green-100 text-green-800',
      'orange': 'bg-orange-100 text-orange-800',
      'blue': 'bg-blue-100 text-blue-800',
      'gray': 'bg-gray-100 text-gray-800'
    };
    return colors[color] || 'bg-gray-100 text-gray-800';
  };

  // Função para obter cor do subnicho (IGUAL À ABA TABELA)
  const getSubnichoColor = (subnicho) => {
    // IMPORTANTE: Use as MESMAS cores que a aba Tabela usa
    // Se Terror é roxo na Tabela, use roxo aqui também
    const lowerSubnicho = subnicho?.toLowerCase() || '';

    if (lowerSubnicho.includes('terror')) return 'bg-purple-50 text-purple-900';
    if (lowerSubnicho.includes('guerra')) return 'bg-red-50 text-red-900';
    if (lowerSubnicho.includes('mistério')) return 'bg-blue-50 text-blue-900';
    if (lowerSubnicho.includes('história')) return 'bg-amber-50 text-amber-900';
    if (lowerSubnicho.includes('crime')) return 'bg-gray-50 text-gray-900';
    if (lowerSubnicho.includes('paranormal')) return 'bg-indigo-50 text-indigo-900';

    return 'bg-gray-50 text-gray-900';
  };

  // Toggle expansão dos cards principais
  const toggleCard = (cardId) => {
    setExpandedCards(prev => ({
      ...prev,
      [cardId]: !prev[cardId]
    }));
  };

  // Toggle expansão dos subnichos
  const toggleSubnicho = (subnichoId) => {
    setExpandedSubnichos(prev => ({
      ...prev,
      [subnichoId]: !prev[subnichoId]
    }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Carregando sistema Kanban...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ESTRUTURA HIERÁRQUICA - IGUAL À ABA TABELA */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Card MONETIZADOS */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div
            className="p-4 cursor-pointer flex items-center justify-between hover:bg-gray-50"
            onClick={() => toggleCard('monetizados')}
          >
            <div className="flex items-center gap-2">
              <span className="text-2xl">💰</span>
              <div>
                <h3 className="font-semibold text-lg">MONETIZADOS</h3>
                <p className="text-sm text-gray-600">{estrutura?.monetizados?.total || 0} canais</p>
              </div>
            </div>
            {expandedCards.monetizados ? <ChevronDown /> : <ChevronRight />}
          </div>

          {expandedCards.monetizados && estrutura?.monetizados?.subnichos && (
            <div className="border-t border-gray-200 p-4 space-y-3">
              {Object.entries(estrutura.monetizados.subnichos).map(([subnicho, data]) => (
                <div key={subnicho}>
                  <div
                    className={`p-3 rounded-lg cursor-pointer ${getSubnichoColor(subnicho)}`}
                    onClick={() => toggleSubnicho(`mon-${subnicho}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {expandedSubnichos[`mon-${subnicho}`] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        <span className="font-medium">{subnicho}</span>
                        <span className="text-sm opacity-75">({data.total} canais)</span>
                      </div>
                    </div>
                  </div>

                  {expandedSubnichos[`mon-${subnicho}`] && (
                    <div className="mt-2 ml-6 space-y-2">
                      {data.canais?.map(canal => (
                        <div
                          key={canal.id}
                          className="p-3 bg-white rounded border border-gray-200 cursor-pointer hover:bg-gray-50 flex items-center justify-between"
                          onClick={() => fetchKanbanBoard(canal.id)}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{getBandeira(canal.lingua)}</span>
                            <span className="font-medium">{canal.nome}</span>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(canal.status_color)}`}>
                            {canal.status_emoji} {canal.status_label} há {canal.dias_no_status}d
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Card NÃO MONETIZADOS */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div
            className="p-4 cursor-pointer flex items-center justify-between hover:bg-gray-50"
            onClick={() => toggleCard('nao_monetizados')}
          >
            <div className="flex items-center gap-2">
              <span className="text-2xl">📍</span>
              <div>
                <h3 className="font-semibold text-lg">NÃO MONETIZADOS</h3>
                <p className="text-sm text-gray-600">{estrutura?.nao_monetizados?.total || 0} canais</p>
              </div>
            </div>
            {expandedCards.nao_monetizados ? <ChevronDown /> : <ChevronRight />}
          </div>

          {expandedCards.nao_monetizados && estrutura?.nao_monetizados?.subnichos && (
            <div className="border-t border-gray-200 p-4 space-y-3">
              {Object.entries(estrutura.nao_monetizados.subnichos).map(([subnicho, data]) => (
                <div key={subnicho}>
                  <div
                    className={`p-3 rounded-lg cursor-pointer ${getSubnichoColor(subnicho)}`}
                    onClick={() => toggleSubnicho(`nao-${subnicho}`)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {expandedSubnichos[`nao-${subnicho}`] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        <span className="font-medium">{subnicho}</span>
                        <span className="text-sm opacity-75">({data.total} canais)</span>
                      </div>
                    </div>
                  </div>

                  {expandedSubnichos[`nao-${subnicho}`] && (
                    <div className="mt-2 ml-6 space-y-2">
                      {data.canais?.map(canal => (
                        <div
                          key={canal.id}
                          className="p-3 bg-white rounded border border-gray-200 cursor-pointer hover:bg-gray-50 flex items-center justify-between"
                          onClick={() => fetchKanbanBoard(canal.id)}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{getBandeira(canal.lingua)}</span>
                            <span className="font-medium">{canal.nome}</span>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(canal.status_color)}`}>
                            {canal.status_emoji} {canal.status_label} há {canal.dias_no_status}d
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* MODAL DO KANBAN INDIVIDUAL */}
      {selectedCanal && kanbanData && (
        <KanbanBoard
          data={kanbanData}
          canalId={selectedCanal}
          onClose={() => {
            setSelectedCanal(null);
            setKanbanData(null);
            fetchEstrutura(); // Atualizar estrutura após mudanças
          }}
        />
      )}
    </div>
  );
};

// =====================================================
// COMPONENTE DO KANBAN INDIVIDUAL (MODAL)
// =====================================================

const KanbanBoard = ({ data, canalId, onClose }) => {
  const [colunas, setColunas] = useState(data.colunas);
  const [notas, setNotas] = useState(data.notas);
  const [historico, setHistorico] = useState(data.historico);
  const [showHistory, setShowHistory] = useState(false);
  const [draggedItem, setDraggedItem] = useState(null);
  const [draggedNote, setDraggedNote] = useState(null);
  const [creatingNote, setCreatingNote] = useState(null); // ID da coluna onde está criando
  const [newNoteText, setNewNoteText] = useState('');
  const [newNoteColor, setNewNoteColor] = useState('yellow');
  const [editingNote, setEditingNote] = useState(null);

  // Cores disponíveis para notas
  const noteColors = [
    { value: 'yellow', bg: 'bg-yellow-100', border: 'border-yellow-300', label: 'Amarelo' },
    { value: 'green', bg: 'bg-green-100', border: 'border-green-300', label: 'Verde' },
    { value: 'blue', bg: 'bg-blue-100', border: 'border-blue-300', label: 'Azul' },
    { value: 'purple', bg: 'bg-purple-100', border: 'border-purple-300', label: 'Roxo' },
    { value: 'red', bg: 'bg-red-100', border: 'border-red-300', label: 'Vermelho' },
    { value: 'orange', bg: 'bg-orange-100', border: 'border-orange-300', label: 'Laranja' }
  ];

  // Função para obter cores da nota
  const getNoteColor = (color) => {
    const colorMap = {
      'yellow': 'bg-yellow-100 border-yellow-300',
      'green': 'bg-green-100 border-green-300',
      'blue': 'bg-blue-100 border-blue-300',
      'purple': 'bg-purple-100 border-purple-300',
      'red': 'bg-red-100 border-red-300',
      'orange': 'bg-orange-100 border-orange-300'
    };
    return colorMap[color] || 'bg-gray-100 border-gray-300';
  };

  // Mudar status do canal (drag & drop do ponto azul)
  const handleStatusChange = async (newStatus) => {
    try {
      const response = await fetch(`/api/kanban/canal/${canalId}/move-status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_status: newStatus })
      });

      if (response.ok) {
        // Atualizar UI
        setColunas(colunas.map(col => ({
          ...col,
          is_current: col.id === newStatus
        })));

        // Atualizar histórico
        fetchHistory();
      }
    } catch (error) {
      console.error('Erro ao mudar status:', error);
    }
  };

  // Criar nova nota (com coluna específica)
  const handleCreateNote = async () => {
    if (!newNoteText.trim() || !creatingNote) return;

    try {
      const response = await fetch(`/api/kanban/canal/${canalId}/note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          note_text: newNoteText,
          note_color: newNoteColor,
          coluna_id: creatingNote // Passa a coluna onde a nota está sendo criada
        })
      });

      if (response.ok) {
        const newNote = await response.json();
        setNotas([...notas, { ...newNote, coluna_id: creatingNote }]);
        setNewNoteText('');
        setNewNoteColor('yellow');
        setCreatingNote(null);
        fetchHistory();
      }
    } catch (error) {
      console.error('Erro ao criar nota:', error);
    }
  };

  // Editar nota
  const handleEditNote = async (noteId, text, color) => {
    try {
      const response = await fetch(`/api/kanban/note/${noteId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          note_text: text,
          note_color: color
        })
      });

      if (response.ok) {
        setNotas(notas.map(n =>
          n.id === noteId ? { ...n, note_text: text, note_color: color } : n
        ));
        setEditingNote(null);
        fetchHistory();
      }
    } catch (error) {
      console.error('Erro ao editar nota:', error);
    }
  };

  // Deletar nota
  const handleDeleteNote = async (noteId) => {
    if (!confirm('Tem certeza que deseja deletar esta nota?')) return;

    try {
      const response = await fetch(`/api/kanban/note/${noteId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setNotas(notas.filter(n => n.id !== noteId));
        fetchHistory();
      }
    } catch (error) {
      console.error('Erro ao deletar nota:', error);
    }
  };

  // Reordenar notas (drag & drop)
  const handleReorderNotes = async (draggedId, targetId) => {
    const draggedIndex = notas.findIndex(n => n.id === draggedId);
    const targetIndex = notas.findIndex(n => n.id === targetId);

    if (draggedIndex === -1 || targetIndex === -1) return;

    const newNotas = [...notas];
    const [removed] = newNotas.splice(draggedIndex, 1);
    newNotas.splice(targetIndex, 0, removed);

    // Atualizar UI otimisticamente
    setNotas(newNotas);

    // Enviar para o backend
    try {
      const positions = newNotas.map((nota, index) => ({
        note_id: nota.id,
        position: index + 1
      }));

      await fetch(`/api/kanban/canal/${canalId}/reorder-notes`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note_positions: positions })
      });

      fetchHistory();
    } catch (error) {
      console.error('Erro ao reordenar notas:', error);
    }
  };

  // Buscar histórico
  const fetchHistory = async () => {
    try {
      const response = await fetch(`/api/kanban/canal/${canalId}/history`);
      const data = await response.json();
      setHistorico(data);
    } catch (error) {
      console.error('Erro ao buscar histórico:', error);
    }
  };

  // Soft delete item do histórico
  const handleDeleteHistory = async (historyId) => {
    try {
      await fetch(`/api/kanban/history/${historyId}`, {
        method: 'DELETE'
      });
      setHistorico(historico.filter(h => h.id !== historyId));
    } catch (error) {
      console.error('Erro ao deletar histórico:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl h-[90vh] flex flex-col">

        {/* Header do Modal */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">{data.canal.nome}</h2>
            <p className="text-sm text-gray-600">
              {data.canal.subnicho} •
              Status atual: <span className="font-medium">{data.canal.status_atual}</span> •
              Há {data.canal.dias_no_status} dias
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="p-2 hover:bg-gray-100 rounded-lg"
              title="Histórico"
            >
              <HistoryIcon size={20} />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">

          {/* Área do Kanban */}
          <div className="flex-1 p-4 overflow-auto">

            {/* Colunas do Kanban */}
            <div className="flex gap-4 min-h-full">
              {colunas.map(coluna => (
                <div
                  key={coluna.id}
                  className="flex-1 min-w-[250px]"
                >
                  {/* Header da Coluna */}
                  <div className={`p-3 rounded-t-lg ${coluna.is_current ? 'bg-blue-50' : 'bg-gray-50'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{coluna.emoji}</span>
                        <h3 className="font-medium">{coluna.label}</h3>
                      </div>

                    </div>
                    <p className="text-xs text-gray-600 mt-1">{coluna.descricao}</p>
                  </div>

                  {/* Área de Drop para Status */}
                  <div
                    className={`p-4 bg-gray-50 min-h-[200px] rounded-b-lg border-2 ${
                      draggedItem === 'canal' && !coluna.is_current
                        ? 'border-blue-400 border-dashed'
                        : 'border-transparent'
                    }`}
                    onDragOver={(e) => {
                      if (draggedItem === 'canal' && !coluna.is_current) {
                        e.preventDefault();
                      }
                    }}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (draggedItem === 'canal' && !coluna.is_current) {
                        handleStatusChange(coluna.id);
                      }
                    }}
                  >
                    {/* CARD PRINCIPAL DO CANAL - SEMPRE NA COLUNA ATUAL */}
                    {coluna.is_current && (
                      <div className="mb-4">
                        <div
                          className="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 shadow-sm cursor-move"
                          draggable
                          onDragStart={() => setDraggedItem('canal')}
                          onDragEnd={() => setDraggedItem(null)}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xl">
                              {data.canal.subnicho?.toLowerCase().includes('terror') && '🎭'}
                              {data.canal.subnicho?.toLowerCase().includes('guerra') && '⚔️'}
                              {data.canal.subnicho?.toLowerCase().includes('mistério') && '🔍'}
                              {data.canal.subnicho?.toLowerCase().includes('história') && '📚'}
                              {data.canal.subnicho?.toLowerCase().includes('crime') && '🔪'}
                              {data.canal.subnicho?.toLowerCase().includes('paranormal') && '👻'}
                              {!data.canal.subnicho?.toLowerCase().match(/(terror|guerra|mistério|história|crime|paranormal)/) && '📺'}
                            </span>
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-800">{data.canal.nome}</h4>
                              <p className="text-xs text-gray-600">Arraste para mudar status</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* ÁREA DE NOTAS - PODEM ESTAR EM QUALQUER COLUNA */}
                    <div className="space-y-3">
                      {/* Notas desta coluna (filtradas por coluna) */}
                      {notas.filter(n => n.coluna_id === coluna.id).map((nota, index) => (
                          <div
                            key={nota.id}
                            className={`p-3 rounded-lg border-2 ${getNoteColor(nota.note_color)}`}
                            draggable
                            onDragStart={() => setDraggedNote(nota.id)}
                            onDragEnd={() => setDraggedNote(null)}
                            onDragOver={(e) => {
                              if (draggedNote && draggedNote !== nota.id) {
                                e.preventDefault();
                              }
                            }}
                            onDrop={(e) => {
                              e.preventDefault();
                              if (draggedNote && draggedNote !== nota.id) {
                                handleReorderNotes(draggedNote, nota.id);
                              }
                            }}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-start gap-2 flex-1">
                                <GripVertical size={16} className="mt-1 cursor-move text-gray-400" />

                                {editingNote === nota.id ? (
                                  <div className="flex-1 space-y-2">
                                    <textarea
                                      value={nota.note_text}
                                      onChange={(e) => setNotas(notas.map(n =>
                                        n.id === nota.id ? { ...n, note_text: e.target.value } : n
                                      ))}
                                      className="w-full p-2 border rounded"
                                      rows={3}
                                    />
                                    <div className="flex items-center gap-2">
                                      {noteColors.map(color => (
                                        <button
                                          key={color.value}
                                          onClick={() => setNotas(notas.map(n =>
                                            n.id === nota.id ? { ...n, note_color: color.value } : n
                                          ))}
                                          className={`w-6 h-6 rounded ${color.bg} ${color.border} border-2 ${
                                            nota.note_color === color.value ? 'ring-2 ring-offset-1 ring-gray-400' : ''
                                          }`}
                                        />
                                      ))}
                                      <button
                                        onClick={() => handleEditNote(nota.id, nota.note_text, nota.note_color)}
                                        className="ml-auto px-3 py-1 bg-blue-500 text-white rounded text-sm"
                                      >
                                        Salvar
                                      </button>
                                      <button
                                        onClick={() => {
                                          setNotas(data.notas);
                                          setEditingNote(null);
                                        }}
                                        className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm"
                                      >
                                        Cancelar
                                      </button>
                                    </div>
                                  </div>
                                ) : (
                                  <p className="flex-1 text-sm">{nota.note_text}</p>
                                )}
                              </div>

                              {editingNote !== nota.id && (
                                <div className="flex gap-1">
                                  <button
                                    onClick={() => setEditingNote(nota.id)}
                                    className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                                  >
                                    <Edit2 size={14} />
                                  </button>
                                  <button
                                    onClick={() => handleDeleteNote(nota.id)}
                                    className="p-1 hover:bg-white hover:bg-opacity-50 rounded text-red-600"
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}

                      {/* Botão Adicionar Nota para esta coluna */}
                      {creatingNote === coluna.id ? (
                          <div className="p-3 bg-white rounded-lg border-2 border-dashed border-gray-300 space-y-2">
                            <textarea
                              value={newNoteText}
                              onChange={(e) => setNewNoteText(e.target.value)}
                              placeholder="Digite sua nota..."
                              className="w-full p-2 border rounded resize-none"
                              rows={3}
                              autoFocus
                            />
                            <div className="flex items-center gap-2">
                              {noteColors.map(color => (
                                <button
                                  key={color.value}
                                  onClick={() => setNewNoteColor(color.value)}
                                  className={`w-6 h-6 rounded ${color.bg} ${color.border} border-2 ${
                                    newNoteColor === color.value ? 'ring-2 ring-offset-1 ring-gray-400' : ''
                                  }`}
                                />
                              ))}
                              <button
                                onClick={handleCreateNote}
                                className="ml-auto px-3 py-1 bg-blue-500 text-white rounded text-sm"
                              >
                                Adicionar
                              </button>
                              <button
                                onClick={() => {
                                  setCreatingNote(null);
                                  setNewNoteText('');
                                  setNewNoteColor('yellow');
                                }}
                                className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm"
                              >
                                Cancelar
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={() => setCreatingNote(coluna.id)}
                            className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 hover:bg-white flex items-center justify-center gap-2 text-gray-600"
                          >
                            <Plus size={16} />
                            <span className="text-sm">Adicionar Nota</span>
                          </button>
                        )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Painel Lateral de Histórico */}
          {showHistory && (
            <div className="w-80 border-l border-gray-200 bg-gray-50 p-4 overflow-auto">
              <h3 className="font-semibold mb-3">Histórico</h3>
              <div className="space-y-2">
                {historico.slice(0, 50).map(item => (
                  <div key={item.id} className="bg-white p-2 rounded text-sm">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium">{item.description}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(item.performed_at).toLocaleString('pt-BR')}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteHistory(item.id)}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KanbanCompleto;

/**
 * NOTAS FINAIS PARA IMPLEMENTAÇÃO:
 *
 * 1. Este componente deve aparecer IGUAL à aba Tabela em termos visuais
 * 2. Adicionar rota em Ferramentas > Kanban
 * 3. Garantir que as cores dos subnichos sejam as mesmas da Tabela
 * 4. Mostrar bandeiras, nomes completos e tags de status coloridas
 * 5. O backend já está 100% pronto com os 10 endpoints funcionando
 *
 * NÃO ESQUECER:
 * - Layout hierárquico expansível igual Tabela
 * - Cores consistentes com o resto do dashboard
 * - Mobile responsivo
 * - Drag & drop funcionando (ponto azul e notas)
 */