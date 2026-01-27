import React, { useState, useEffect } from 'react';
import { MessageSquare, Users, Clock, CheckCircle, ChevronRight, Copy, Check, X } from 'lucide-react';

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

  // Carregar resumo ao montar componente
  useEffect(() => {
    fetchSummary();
    fetchMonetizedChannels();
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await fetch('/api/comentarios/resumo');
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error('Erro ao buscar resumo:', error);
    }
  };

  const fetchMonetizedChannels = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/comentarios/monetizados');
      const data = await response.json();
      setChannels(data);
    } catch (error) {
      console.error('Erro ao buscar canais:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchVideos = async (channelId: number) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/canais/${channelId}/videos-com-comentarios`);
      const data = await response.json();
      setVideos(data);
    } catch (error) {
      console.error('Erro ao buscar vídeos:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async (videoId: string, page: number = 1) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/videos/${videoId}/comentarios-paginados?page=${page}`);
      const data: CommentsResponse = await response.json();
      setComments(data.comments);
      setCurrentPage(data.page);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('Erro ao buscar comentários:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, commentId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(commentId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      console.error('Erro ao copiar:', error);
    }
  };

  const markAsResponded = async (commentId: string, actualResponse?: string) => {
    try {
      const response = await fetch(`/api/comentarios/${commentId}/marcar-respondido`, {
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
        // Atualizar resumo
        fetchSummary();
      }
    } catch (error) {
      console.error('Erro ao marcar como respondido:', error);
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
  };

  return (
    <div className="space-y-6">
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
              <p className="text-2xl font-bold">{summary?.total_comentarios || 0}</p>
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
              <p className="text-2xl font-bold">{summary?.aguardando_resposta || 0}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Lista de Canais Monetizados */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-xl font-semibold">Canais Monetizados</h2>
          <p className="text-gray-600 text-sm">Clique em um canal para ver os comentários</p>
        </div>

        <div className="p-6">
          {loading && !channels.length ? (
            <div className="text-center py-8">Carregando...</div>
          ) : channels.length > 0 ? (
            <div className="space-y-4">
              {channels.map((channel) => (
                <div
                  key={channel.id}
                  onClick={() => openChannel(channel)}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <div className="flex-1">
                    <h3 className="font-medium">{channel.nome_canal}</h3>
                    <div className="flex gap-4 mt-1 text-sm text-gray-600">
                      <span>{channel.total_comentarios} comentários</span>
                      <span>{channel.comentarios_sem_resposta} sem resposta</span>
                      <span>{channel.total_videos} vídeos</span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              Nenhum canal monetizado encontrado
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
                <p className="text-gray-600">Vídeos com comentários</p>
              </div>
              <button onClick={closeModal} className="text-gray-500 hover:text-gray-700">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {loading ? (
                <div className="text-center py-8">Carregando vídeos...</div>
              ) : videos.length > 0 ? (
                <div className="space-y-4">
                  {videos.map((video) => (
                    <div
                      key={video.video_id}
                      onClick={() => openVideo(video)}
                      className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                    >
                      <h4 className="font-medium mb-2">{video.titulo}</h4>
                      <div className="flex gap-4 text-sm text-gray-600">
                        <span>{video.total_comentarios} comentários</span>
                        <span>{video.comentarios_sem_resposta} sem resposta</span>
                        <span>{video.views_atuais.toLocaleString()} views</span>
                        <span>{new Date(video.data_publicacao).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  Nenhum vídeo com comentários encontrado
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
                  <h3 className="text-xl font-semibold mb-2">{selectedVideo.titulo}</h3>
                  <p className="text-gray-600">{selectedVideo.total_comentarios} comentários total</p>
                </div>
                <button onClick={closeModal} className="text-gray-500 hover:text-gray-700">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              {loading ? (
                <div className="text-center py-8">Carregando comentários...</div>
              ) : comments.length > 0 ? (
                <div className="space-y-6">
                  {comments.map((comment) => (
                    <div key={comment.id} className={`border rounded-lg p-4 ${comment.is_responded ? 'bg-green-50' : ''}`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="font-medium">{comment.author_name}</span>
                          <span className="text-gray-500 text-sm ml-2">
                            {new Date(comment.published_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-500">{comment.like_count} likes</span>
                          {comment.is_responded && (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                              Respondido
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="mb-3">
                        <p className="text-gray-700">{comment.comment_text_original}</p>
                        {comment.comment_text_pt && comment.comment_text_pt !== comment.comment_text_original && (
                          <p className="text-gray-600 text-sm mt-2 italic">
                            Tradução: {comment.comment_text_pt}
                          </p>
                        )}
                      </div>

                      {comment.suggested_response && !comment.is_responded && (
                        <div className="bg-blue-50 p-3 rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-sm font-medium text-blue-900">Resposta Sugerida:</span>
                            <button
                              onClick={() => copyToClipboard(comment.suggested_response, comment.id)}
                              className="text-blue-600 hover:text-blue-800"
                            >
                              {copiedId === comment.id ? (
                                <Check className="w-4 h-4" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </button>
                          </div>
                          <p className="text-sm text-gray-700">{comment.suggested_response}</p>
                          <button
                            onClick={() => markAsResponded(comment.id, comment.suggested_response)}
                            className="mt-2 text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                          >
                            Marcar como Respondido
                          </button>
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Paginação */}
                  {totalPages > 1 && (
                    <div className="flex justify-center gap-2 mt-6">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                        <button
                          key={page}
                          onClick={() => fetchComments(selectedVideo.video_id, page)}
                          className={`px-3 py-1 rounded ${
                            page === currentPage
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  Nenhum comentário encontrado para este vídeo
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