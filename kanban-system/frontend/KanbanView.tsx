import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, Plus, Trash2, Edit2, Clock, StickyNote, History } from 'lucide-react';

/**
 * Componente Principal do Sistema Kanban
 *
 * IMPORTANTE: Este componente segue o mesmo layout da aba Tabela
 * - Dois cards principais (Monetizados e Não Monetizados)
 * - Expansível por subnicho
 * - Lista de canais com tags de status
 * - Modal do Kanban individual
 */

// Mapeamento de línguas para bandeiras
const LANGUAGE_FLAGS = {
  'portuguese': '🇧🇷',
  'english': '🇺🇸',
  'spanish': '🇪🇸',
  'french': '🇫🇷',
  'german': '🇩🇪',
  'italian': '🇮🇹',
  'russian': '🇷🇺',
  'japanese': '🇯🇵'
};

// Cores dos status
const STATUS_COLORS = {
  // Não monetizados
  'em_teste_inicial': { bg: 'bg-yellow-100', text: 'text-yellow-800', emoji: '🟡' },
  'demonstrando_tracao': { bg: 'bg-green-100', text: 'text-green-800', emoji: '🟢' },
  'em_andamento': { bg: 'bg-orange-100', text: 'text-orange-800', emoji: '🟠' },
  'monetizado': { bg: 'bg-blue-100', text: 'text-blue-800', emoji: '🔵' },
  // Monetizados
  'em_crescimento': { bg: 'bg-green-100', text: 'text-green-800', emoji: '🟢' },
  'em_testes_novos': { bg: 'bg-yellow-100', text: 'text-yellow-800', emoji: '🟡' },
  'canal_constante': { bg: 'bg-blue-100', text: 'text-blue-800', emoji: '🔵' }
};

const KanbanView = () => {
  const [structure, setStructure] = useState(null);
  const [expandedCards, setExpandedCards] = useState({});
  const [expandedSubnichos, setExpandedSubnichos] = useState({});
  const [selectedCanal, setSelectedCanal] = useState(null);
  const [kanbanBoard, setKanbanBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Buscar estrutura inicial
  useEffect(() => {
    fetchStructure();
  }, []);

  const fetchStructure = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/kanban/structure');
      if (!response.ok) throw new Error('Erro ao buscar estrutura');
      const data = await response.json();
      setStructure(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchKanbanBoard = async (canalId) => {
    try {
      const response = await fetch(`/api/kanban/canal/${canalId}/board`);
      if (!response.ok) throw new Error('Erro ao buscar kanban');
      const data = await response.json();
      setKanbanBoard(data);
      setSelectedCanal(canalId);
    } catch (err) {
      console.error('Erro ao buscar kanban:', err);
    }
  };

  const toggleCard = (card) => {
    setExpandedCards(prev => ({
      ...prev,
      [card]: !prev[card]
    }));
  };

  const toggleSubnicho = (card, subnicho) => {
    const key = `${card}-${subnicho}`;
    setExpandedSubnichos(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };

  const formatDaysAgo = (days) => {
    if (days === 0) return 'hoje';
    if (days === 1) return 'há 1 dia';
    return `há ${days} dias`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        Erro: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Cards Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Card Monetizados */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div
            className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleCard('monetizados')}
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <span className="text-2xl">💰</span>
                  Monetizados
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  {structure?.monetizados?.total || 0} canais
                </p>
              </div>
              <div className="text-gray-400">
                {expandedCards.monetizados ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </div>
            </div>
          </div>

          {/* Subnichos Monetizados */}
          {expandedCards.monetizados && (
            <div className="border-t border-gray-200">
              {Object.entries(structure?.monetizados?.subnichos || {}).map(([subnicho, data]) => (
                <div key={subnicho} className="border-b border-gray-100 last:border-b-0">
                  <div
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => toggleSubnicho('monetizados', subnicho)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">📁</span>
                        <span className="font-medium text-gray-700">{subnicho}</span>
                        <span className="text-sm text-gray-500">({data.total} canais)</span>
                      </div>
                      <div className="text-gray-400">
                        {expandedSubnichos[`monetizados-${subnicho}`] ?
                          <ChevronDown size={20} /> : <ChevronRight size={20} />}
                      </div>
                    </div>
                  </div>

                  {/* Lista de Canais */}
                  {expandedSubnichos[`monetizados-${subnicho}`] && (
                    <div className="px-6 pb-4 space-y-2">
                      {data.canais.map(canal => (
                        <div
                          key={canal.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                          onClick={() => fetchKanbanBoard(canal.id)}
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-xl">
                              {LANGUAGE_FLAGS[canal.lingua] || '🌐'}
                            </span>
                            <span className="font-medium text-gray-700">
                              {canal.nome}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {canal.total_notas > 0 && (
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                <StickyNote size={14} />
                                {canal.total_notas}
                              </span>
                            )}
                            <div className={`
                              px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1
                              ${STATUS_COLORS[canal.kanban_status]?.bg || 'bg-gray-100'}
                              ${STATUS_COLORS[canal.kanban_status]?.text || 'text-gray-800'}
                            `}>
                              <span>{STATUS_COLORS[canal.kanban_status]?.emoji}</span>
                              <span>{canal.status_label}</span>
                              <span className="text-xs opacity-75">
                                ({formatDaysAgo(canal.dias_no_status)})
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Card Não Monetizados */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div
            className="p-6 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleCard('nao_monetizados')}
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <span className="text-2xl">📍</span>
                  Não Monetizados
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  {structure?.nao_monetizados?.total || 0} canais
                </p>
              </div>
              <div className="text-gray-400">
                {expandedCards.nao_monetizados ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
              </div>
            </div>
          </div>

          {/* Subnichos Não Monetizados */}
          {expandedCards.nao_monetizados && (
            <div className="border-t border-gray-200">
              {Object.entries(structure?.nao_monetizados?.subnichos || {}).map(([subnicho, data]) => (
                <div key={subnicho} className="border-b border-gray-100 last:border-b-0">
                  <div
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => toggleSubnicho('nao_monetizados', subnicho)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">📁</span>
                        <span className="font-medium text-gray-700">{subnicho}</span>
                        <span className="text-sm text-gray-500">({data.total} canais)</span>
                      </div>
                      <div className="text-gray-400">
                        {expandedSubnichos[`nao_monetizados-${subnicho}`] ?
                          <ChevronDown size={20} /> : <ChevronRight size={20} />}
                      </div>
                    </div>
                  </div>

                  {/* Lista de Canais */}
                  {expandedSubnichos[`nao_monetizados-${subnicho}`] && (
                    <div className="px-6 pb-4 space-y-2">
                      {data.canais.map(canal => (
                        <div
                          key={canal.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                          onClick={() => fetchKanbanBoard(canal.id)}
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-xl">
                              {LANGUAGE_FLAGS[canal.lingua] || '🌐'}
                            </span>
                            <span className="font-medium text-gray-700">
                              {canal.nome}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {canal.total_notas > 0 && (
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                <StickyNote size={14} />
                                {canal.total_notas}
                              </span>
                            )}
                            <div className={`
                              px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1
                              ${STATUS_COLORS[canal.kanban_status]?.bg || 'bg-gray-100'}
                              ${STATUS_COLORS[canal.kanban_status]?.text || 'text-gray-800'}
                            `}>
                              <span>{STATUS_COLORS[canal.kanban_status]?.emoji}</span>
                              <span>{canal.status_label}</span>
                              <span className="text-xs opacity-75">
                                desde {formatDate(canal.status_since)}
                              </span>
                            </div>
                          </div>
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

      {/* Modal do Kanban Individual (será implementado em KanbanBoard.tsx) */}
      {selectedCanal && kanbanBoard && (
        <KanbanBoard
          board={kanbanBoard}
          onClose={() => {
            setSelectedCanal(null);
            setKanbanBoard(null);
          }}
          onRefresh={() => fetchKanbanBoard(selectedCanal)}
        />
      )}
    </div>
  );
};

export default KanbanView;