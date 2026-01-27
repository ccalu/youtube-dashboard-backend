# 🚀 SISTEMA COMPLETO DE COMENTÁRIOS PARA LOVABLE

## ⚠️ SITUAÇÃO ATUAL DO BANCO DE DADOS

**IMPORTANTE:** A tabela `video_comments` está VAZIA (0 registros).
- Temos 9 canais com subnicho "Monetizados" configurados
- O sistema está pronto para coletar comentários
- Assim que os comentários forem coletados, tudo funcionará automaticamente

## ✅ CORREÇÕES JÁ APLICADAS NO BACKEND

1. **Endpoint `/api/canais/{id}/engagement`** - Corrigido para não dar erro quando canal não tem comentários
2. **Campo `created_at`** - Corrigido para `updated_at` na função get_comments_summary()
3. **5 novos endpoints criados e funcionando:**
   - `GET /api/comentarios/resumo`
   - `GET /api/comentarios/monetizados`
   - `GET /api/canais/{id}/videos-com-comentarios`
   - `GET /api/videos/{id}/comentarios-paginados`
   - `PATCH /api/comentarios/{id}/marcar-respondido`

## 📱 COMPONENTE REACT COMPLETO - CommentsTab.tsx

Copie este código EXATAMENTE como está para `src/components/CommentsTab.tsx`:

```tsx
import React, { useState, useEffect } from 'react';
import { MessageSquare, Users, Clock, CheckCircle, ChevronRight, Copy, Check, X, AlertCircle, RefreshCw } from 'lucide-react';

// IMPORTANTE: Use a URL do seu backend Railway
const API_URL = 'https://youtube-dashboard-backend-production.up.railway.app/api';

interface CommentsSummary {
  canais_monetizados: number;
  total_comentarios: number;
  novos_hoje: number;
  aguardando_resposta: number;
}

interface MonetizedChannel {
  id: number;
  nome_canal: string;
  total_comentarios: number;
  comentarios_sem_resposta: number;
  total_videos: number;
  engagement_rate: number;
}

interface VideoWithComments {
  video_id: string;
  titulo: string;
  data_publicacao: string;
  total_comentarios: number;
  comentarios_sem_resposta: number;
  views_atuais: number;
}

interface Comment {
  id: string;
  author_name: string;
  comment_text_original: string;
  comment_text_pt: string;
  suggested_response: string;
  like_count: number;
  published_at: string;
  is_responded: boolean;
}

interface CommentsResponse {
  comments: Comment[];
  total: number;
  page: number;
  total_pages: number;
}

const CommentsTab: React.FC = () => {
  const [summary, setSummary] = useState<CommentsSummary | null>(null);
  const [channels, setChannels] = useState<MonetizedChannel[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<MonetizedChannel | null>(null);
  const [videos, setVideos] = useState<VideoWithComments[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoWithComments | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCollecting, setIsCollecting] = useState(false);

  // Carregar resumo ao montar componente
  useEffect(() => {
    fetchSummary();
    fetchMonetizedChannels();
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_URL}/comentarios/resumo`);
      if (!response.ok) throw new Error('Erro ao buscar resumo');
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error('Erro ao buscar resumo:', error);
      setError('Erro ao carregar resumo dos comentários');
    }
  };

  const fetchMonetizedChannels = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/comentarios/monetizados`);
      if (!response.ok) throw new Error('Erro ao buscar canais');
      const data = await response.json();
      setChannels(data);
    } catch (error) {
      console.error('Erro ao buscar canais:', error);
      setError('Erro ao carregar canais monetizados');
    } finally {
      setLoading(false);
    }
  };

  const fetchVideos = async (channelId: number) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/canais/${channelId}/videos-com-comentarios`);
      if (!response.ok) throw new Error('Erro ao buscar vídeos');
      const data = await response.json();
      setVideos(data);
    } catch (error) {
      console.error('Erro ao buscar vídeos:', error);
      setError('Erro ao carregar vídeos do canal');
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async (videoId: string, page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/videos/${videoId}/comentarios-paginados?page=${page}`);
      if (!response.ok) throw new Error('Erro ao buscar comentários');
      const data: CommentsResponse = await response.json();
      setComments(data.comments || []);
      setCurrentPage(data.page || 1);
      setTotalPages(data.total_pages || 0);
    } catch (error) {
      console.error('Erro ao buscar comentários:', error);
      setError('Erro ao carregar comentários');
    } finally {
      setLoading(false);
    }
  };

  const collectComments = async (channelId: number) => {
    try {
      setIsCollecting(true);
      setError(null);
      const response = await fetch(`${API_URL}/collect-comments/${channelId}`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao coletar comentários');
      }

      const result = await response.json();

      // Atualizar dados após coleta
      await fetchSummary();
      await fetchMonetizedChannels();

      alert(`Coleta concluída! ${result.total_coletados || 0} comentários coletados.`);
    } catch (error: any) {
      console.error('Erro ao coletar comentários:', error);
      setError(error.message || 'Erro ao coletar comentários');
    } finally {
      setIsCollecting(false);
    }
  };

  const copyToClipboard = async (text: string, commentId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(commentId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      console.error('Erro ao copiar:', error);
      alert('Erro ao copiar resposta. Por favor, selecione e copie manualmente.');
    }
  };

  const markAsResponded = async (commentId: string, actualResponse?: string) => {
    try {
      const response = await fetch(`${API_URL}/comentarios/${commentId}/marcar-respondido`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ actual_response: actualResponse }),
      });

      if (response.ok) {
        // Atualizar o comentário localmente
        setComments(prev =>
          prev.map(c => (c.id === commentId ? { ...c, is_responded: true } : c))
        );
        // Atualizar resumo e contadores
        fetchSummary();

        // Atualizar contador do canal
        if (selectedChannel) {
          setSelectedChannel(prev => prev ? {
            ...prev,
            comentarios_sem_resposta: Math.max(0, prev.comentarios_sem_resposta - 1)
          } : null);
        }

        // Atualizar contador do vídeo
        if (selectedVideo) {
          setVideos(prev => prev.map(v =>
            v.video_id === selectedVideo.video_id
              ? { ...v, comentarios_sem_resposta: Math.max(0, v.comentarios_sem_resposta - 1) }
              : v
          ));
        }

        alert('Comentário marcado como respondido!');
      }
    } catch (error) {
      console.error('Erro ao marcar como respondido:', error);
      alert('Erro ao marcar comentário como respondido');
    }
  };

  const openChannel = (channel: MonetizedChannel) => {
    setSelectedChannel(channel);
    setSelectedVideo(null);
    setComments([]);
    fetchVideos(channel.id);
  };

  const openVideo = (video: VideoWithComments) => {
    setSelectedVideo(video);
    setCurrentPage(1);
    fetchComments(video.video_id, 1);
  };

  const closeModal = () => {
    setSelectedChannel(null);
    setSelectedVideo(null);
    setVideos([]);
    setComments([]);
    setError(null);
  };

  // Função para formatar números
  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Mensagem de erro global */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
          <button onClick={() => setError(null)} className="text-red-700 hover:text-red-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Cards de Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Canais Monetizados</p>
              <p className="text-2xl font-bold">{summary?.canais_monetizados || 0}</p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total de Comentários</p>
              <p className="text-2xl font-bold">{formatNumber(summary?.total_comentarios || 0)}</p>
            </div>
            <MessageSquare className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Novos Hoje</p>
              <p className="text-2xl font-bold">{summary?.novos_hoje || 0}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Aguardando Resposta</p>
              <p className="text-2xl font-bold text-red-600">{summary?.aguardando_resposta || 0}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Alerta se não há comentários */}
      {summary && summary.total_comentarios === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 mr-2 mt-0.5" />
            <div>
              <p className="font-semibold">Nenhum comentário coletado ainda</p>
              <p className="text-sm mt-1">
                O sistema está configurado mas ainda não há comentários na base de dados.
                Os comentários serão coletados automaticamente na próxima execução ou você pode coletar manualmente clicando no botão de coleta em cada canal.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Lista de Canais Monetizados */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold">Canais Monetizados</h2>
            <p className="text-gray-600 text-sm">Clique em um canal para ver os comentários</p>
          </div>
          <button
            onClick={() => fetchMonetizedChannels()}
            className="text-blue-600 hover:text-blue-800"
            disabled={loading}
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="p-6">
          {loading && !channels.length ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Carregando canais...</p>
            </div>
          ) : channels.length > 0 ? (
            <div className="space-y-4">
              {channels.map((channel) => (
                <div
                  key={channel.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => openChannel(channel)}
                  >
                    <h3 className="font-medium">{channel.nome_canal}</h3>
                    <div className="flex gap-4 mt-1 text-sm text-gray-600">
                      <span>{formatNumber(channel.total_comentarios)} comentários</span>
                      {channel.comentarios_sem_resposta > 0 && (
                        <span className="text-red-600 font-medium">
                          {channel.comentarios_sem_resposta} sem resposta
                        </span>
                      )}
                      <span>{channel.total_videos} vídeos</span>
                      {channel.engagement_rate > 0 && (
                        <span className="text-green-600">
                          {(channel.engagement_rate * 100).toFixed(2)}% engagement
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        collectComments(channel.id);
                      }}
                      disabled={isCollecting}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                      title="Coletar comentários deste canal"
                    >
                      {isCollecting ? 'Coletando...' : 'Coletar'}
                    </button>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="font-semibold">Nenhum canal monetizado encontrado</p>
              <p className="text-sm mt-2">
                Configure canais com subnicho "Monetizados" no sistema para que apareçam aqui.
              </p>
              <p className="text-sm mt-1 text-gray-400">
                Atualmente há {summary?.canais_monetizados || 0} canais configurados.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Modal de Vídeos */}
      {selectedChannel && !selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b flex justify-between items-center">
              <div>
                <h3 className="text-xl font-semibold">{selectedChannel.nome_canal}</h3>
                <p className="text-gray-600">
                  {selectedChannel.total_videos} vídeos • {formatNumber(selectedChannel.total_comentarios)} comentários
                </p>
              </div>
              <button onClick={closeModal} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-4 text-gray-600">Carregando vídeos...</p>
                </div>
              ) : videos.length > 0 ? (
                <div className="space-y-4">
                  {videos.map((video) => (
                    <div
                      key={video.video_id}
                      onClick={() => openVideo(video)}
                      className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                    >
                      <h4 className="font-medium mb-2 line-clamp-2">{video.titulo}</h4>
                      <div className="flex gap-4 text-sm text-gray-600">
                        <span>{video.total_comentarios} comentários</span>
                        {video.comentarios_sem_resposta > 0 && (
                          <span className="text-red-600 font-medium">
                            {video.comentarios_sem_resposta} sem resposta
                          </span>
                        )}
                        <span>{formatNumber(video.views_atuais)} views</span>
                        <span>{new Date(video.data_publicacao).toLocaleDateString('pt-BR')}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Nenhum vídeo com comentários encontrado</p>
                  <p className="text-sm mt-2">
                    Colete comentários primeiro usando o botão "Coletar" no canal.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal de Comentários */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold mb-2 line-clamp-2">{selectedVideo.titulo}</h3>
                  <p className="text-gray-600">
                    {selectedVideo.total_comentarios} comentários •
                    {selectedVideo.comentarios_sem_resposta > 0 && (
                      <span className="text-red-600 ml-1">
                        {selectedVideo.comentarios_sem_resposta} aguardando resposta
                      </span>
                    )}
                  </p>
                </div>
                <button onClick={closeModal} className="text-gray-500 hover:text-gray-700 ml-4">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-4 text-gray-600">Carregando comentários...</p>
                </div>
              ) : comments.length > 0 ? (
                <div className="space-y-6">
                  {comments.map((comment) => (
                    <div
                      key={comment.id}
                      className={`border rounded-lg p-4 ${
                        comment.is_responded ? 'bg-green-50 border-green-200' : 'bg-white'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="font-medium">@{comment.author_name}</span>
                          <span className="text-gray-500 text-sm ml-2">
                            {new Date(comment.published_at).toLocaleString('pt-BR')}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-500">👍 {comment.like_count}</span>
                          {comment.is_responded && (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                              ✅ Respondido
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="mb-3">
                        <p className="text-gray-700 whitespace-pre-wrap">{comment.comment_text_original}</p>
                        {comment.comment_text_pt && comment.comment_text_pt !== comment.comment_text_original && (
                          <div className="mt-2 p-2 bg-gray-50 rounded">
                            <p className="text-gray-600 text-sm italic">
                              <strong>Tradução:</strong> {comment.comment_text_pt}
                            </p>
                          </div>
                        )}
                      </div>

                      {comment.suggested_response && !comment.is_responded && (
                        <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-sm font-medium text-blue-900">
                              💡 Resposta Sugerida:
                            </span>
                            <button
                              onClick={() => copyToClipboard(comment.suggested_response, comment.id)}
                              className="text-blue-600 hover:text-blue-800 transition-colors"
                              title="Copiar resposta"
                            >
                              {copiedId === comment.id ? (
                                <Check className="w-4 h-4 text-green-600" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                          <p className="text-sm text-gray-700 whitespace-pre-wrap mb-3">
                            {comment.suggested_response}
                          </p>
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                copyToClipboard(comment.suggested_response, comment.id);
                                markAsResponded(comment.id, comment.suggested_response);
                              }}
                              className="text-sm bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                            >
                              Copiar e Marcar como Respondido
                            </button>
                            <button
                              onClick={() => markAsResponded(comment.id)}
                              className="text-sm bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors"
                            >
                              Apenas Marcar como Respondido
                            </button>
                          </div>
                        </div>
                      )}

                      {!comment.suggested_response && !comment.is_responded && (
                        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <p className="text-sm text-yellow-800">
                            ⏳ Aguardando geração de resposta automática...
                          </p>
                        </div>
                      )}

                      {comment.is_responded && (
                        <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                          <p className="text-sm text-green-800">
                            ✅ Este comentário já foi respondido
                          </p>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Paginação */}
                  {totalPages > 1 && (
                    <div className="flex justify-center gap-2 mt-6 pb-4">
                      <button
                        onClick={() => currentPage > 1 && fetchComments(selectedVideo.video_id, currentPage - 1)}
                        disabled={currentPage === 1}
                        className={`px-3 py-1 rounded ${
                          currentPage === 1
                            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        Anterior
                      </button>

                      <span className="px-3 py-1">
                        Página {currentPage} de {totalPages}
                      </span>

                      <button
                        onClick={() => currentPage < totalPages && fetchComments(selectedVideo.video_id, currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className={`px-3 py-1 rounded ${
                          currentPage === totalPages
                            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        Próxima
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Nenhum comentário encontrado para este vídeo</p>
                  <p className="text-sm mt-2">
                    Use o botão "Coletar" no canal para buscar novos comentários.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommentsTab;
```

## 🔧 INTEGRAÇÃO NO DASHBOARD PRINCIPAL

### 1. Adicione o ícone e a aba no menu:

```tsx
// Importe o ícone
import { Settings, MessageSquare } from 'lucide-react';

// Adicione a nova aba
const tabs = [
  // ... outras abas existentes
  { id: 'tools', label: 'Tools', icon: Settings },
  { id: 'comments', label: 'Comentários', icon: MessageSquare }, // NOVA ABA
];
```

### 2. Importe e renderize o componente:

```tsx
// Importe o componente
import CommentsTab from '@/components/CommentsTab';

// Adicione no switch de renderização
{activeTab === 'comments' && <CommentsTab />}
```

## 📊 FUNCIONALIDADES IMPLEMENTADAS

### ✅ Interface Completa:
1. **Cards de Resumo** - Mostra estatísticas em tempo real
2. **Lista de Canais Monetizados** - Com botão de coleta manual
3. **Navegação em 3 Níveis** - Canal → Vídeos → Comentários
4. **Botão "Coletar"** - Coleta manual de comentários por canal
5. **Respostas Sugeridas** - Geradas automaticamente pela IA
6. **Copiar Resposta** - Com feedback visual
7. **Marcar como Respondido** - Atualiza em tempo real
8. **Paginação** - 10 comentários por página
9. **Mensagens Informativas** - Quando não há dados
10. **Tratamento de Erros** - Mensagens claras de erro

### 🎨 Design e UX:
- **Indicadores Visuais:**
  - Comentários respondidos em verde
  - Contador de não respondidos em vermelho
  - Loading states animados
  - Mensagens de erro com opção de fechar
  - Alertas informativos quando não há dados

- **Responsividade:**
  - Mobile-first design
  - Modais adaptativos
  - Scroll suave em listas longas

## 🚀 COMO FUNCIONA

### Fluxo de Uso:
1. **Primeiro Acesso:** Sistema mostra que não há comentários
2. **Coletar Comentários:** Clique em "Coletar" em cada canal monetizado
3. **Navegar:** Canal → Vídeos → Comentários
4. **Responder:** Copiar resposta sugerida → Colar no YouTube → Marcar como respondido

### Coleta de Comentários:
- **Manual:** Botão "Coletar" em cada canal
- **Automática:** Diariamente às 5h da manhã (configurado no backend)
- **Endpoint:** POST `/api/collect-comments/{canal_id}`

## 📝 ENDPOINTS DA API

Todos funcionando em produção:

1. `GET /api/comentarios/resumo`
2. `GET /api/comentarios/monetizados`
3. `GET /api/canais/{id}/videos-com-comentarios`
4. `GET /api/videos/{id}/comentarios-paginados?page=1`
5. `PATCH /api/comentarios/{id}/marcar-respondido`
6. `POST /api/collect-comments/{canal_id}` - Coleta manual

## ⚠️ OBSERVAÇÕES IMPORTANTES

### Sobre os Dados:
- **Tabela Vazia:** A tabela `video_comments` está vazia atualmente
- **9 Canais Configurados:** Existem 9 canais com subnicho "Monetizados"
- **Pronto para Uso:** Assim que coletar comentários, tudo funcionará

### Configurações Necessárias:
- Canais precisam ter `subnicho = "Monetizados"`
- Comentários são filtrados por `is_responded = false`
- Respostas são geradas automaticamente após coleta

### Próximos Passos:
1. Integrar o componente no Lovable
2. Testar a interface
3. Coletar comentários usando o botão "Coletar"
4. Começar a responder comentários

## 🔍 TESTE RÁPIDO

Para verificar se está funcionando:
```
https://youtube-dashboard-backend-production.up.railway.app/api/comentarios/resumo
```

Deve retornar:
```json
{
  "canais_monetizados": 9,
  "total_comentarios": 0,
  "novos_hoje": 0,
  "aguardando_resposta": 0
}
```

## 📦 RESUMO FINAL

**Backend:** ✅ 100% Pronto e em produção
**Frontend:** ✅ Componente completo fornecido
**Dados:** ⏳ Aguardando coleta (tabela vazia)
**Canais:** ✅ 9 canais monetizados configurados

---

**Este arquivo contém TUDO necessário para implementar o sistema de comentários no Lovable. O backend está funcionando, apenas aguardando dados.**