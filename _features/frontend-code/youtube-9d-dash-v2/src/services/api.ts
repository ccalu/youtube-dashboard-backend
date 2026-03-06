export const API_BASE_URL = '';

export interface Channel {
  id: number;
  nome_canal: string;
  url_canal: string;
  nicho: string;
  subnicho: string;
  lingua: string;
  tipo: 'minerado' | 'nosso';
  status: string;
  views_60d?: number;
  views_30d?: number;
  views_15d?: number;
  views_7d?: number;
  views_growth_7d?: number | null;
  views_growth_30d?: number | null;
  views_diff_7d?: number | null;
  views_diff_30d?: number | null;
  inscritos?: number;
  inscritos_diff?: number | null;
  videos_publicados_7d?: number;
  engagement_rate?: number;
  score_calculado?: number;
  growth_7d?: number;
  growth_30d?: number;
  total_videos?: number;
  total_views?: number;
}

export interface TopVideo {
  video_id: string;
  titulo: string;
  url_video: string;
  url_thumbnail: string;
  data_publicacao: string;
  views_atuais: number;
  likes: number;
  comentarios: number;
  duracao: number;
}

export interface TopVideosResponse {
  canal_id: number;
  canal_nome: string;
  top_videos: TopVideo[];
}

export interface Video {
  id: number;
  canal_id: number;
  video_id: string;
  titulo: string;
  url_video: string;
  data_publicacao: string;
  data_coleta: string;
  views_atuais: number;
  likes: number;
  comentarios: number;
  duracao: number;
  nome_canal?: string;
  nicho?: string;
  subnicho?: string;
  lingua?: string;
}

export interface FilterOptions {
  nichos: string[];
  subnichos: string[];
  linguas: string[];
  canais: string[];
}

export interface Notificacao {
  id: number;
  video_id: string;
  canal_id: number;
  nome_video: string;
  nome_canal: string;
  subnicho?: string;
  lingua?: string;
  views_atingidas: number;
  periodo_dias: number;
  tipo_alerta: string;
  mensagem: string;
  data_disparo: string;
  vista: boolean;
  data_vista: string | null;
  data_publicacao?: string;
  tipo_canal?: 'minerado' | 'nosso';
}

export interface NotificacaoStats {
  total: number;
  nao_vistas: number;
  vistas: number;
  hoje: number;
  esta_semana: number;
}

import type {
  KeywordsResponse,
  TitlePatternsResponse,
  TopChannelsResponse,
  SubnichesResponse,
  SubnicheTrendsResponse
} from '@/types/analysis';

class ApiService {
  private fetchApi = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
    try {
      const { getAuthHeaders, handle401 } = await import('@/lib/authFetch');
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...getAuthHeaders(),
          ...(options?.headers as Record<string, string>),
        },
      });

      if (response.status === 401) {
        handle401(response);
        throw new Error('Session expired');
      }

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      throw error;
    }
  }

  getChannels = async (params?: {
    nicho?: string;
    subnicho?: string;
    lingua?: string;
    tipo?: string;
  }): Promise<{ canais: Channel[]; total: number }> => {
    const queryParams = new URLSearchParams();
    if (params?.nicho) queryParams.append('nicho', params.nicho);
    if (params?.subnicho) queryParams.append('subnicho', params.subnicho);
    if (params?.lingua) queryParams.append('lingua', params.lingua);
    if (params?.tipo) queryParams.append('tipo', params.tipo);

    return this.fetchApi(`/api/canais?${queryParams.toString()}`);
  }

  getOurChannels = async (params?: {
    nicho?: string;
    subnicho?: string;
    lingua?: string;
  }): Promise<{ canais: Channel[]; total: number }> => {
    const queryParams = new URLSearchParams();
    if (params?.nicho) queryParams.append('nicho', params.nicho);
    if (params?.subnicho) queryParams.append('subnicho', params.subnicho);
    if (params?.lingua) queryParams.append('lingua', params.lingua);

    return this.fetchApi(`/api/nossos-canais?${queryParams.toString()}`);
  }

  getVideos = async (params?: {
    nicho?: string;
    subnicho?: string;
    lingua?: string;
    canal?: string;
    periodo_publicacao?: string;
  }): Promise<{ videos: Video[]; total: number }> => {
    const queryParams = new URLSearchParams();
    if (params?.nicho) queryParams.append('nicho', params.nicho);
    if (params?.subnicho) queryParams.append('subnicho', params.subnicho);
    if (params?.lingua) queryParams.append('lingua', params.lingua);
    if (params?.canal) queryParams.append('canal', params.canal);
    if (params?.periodo_publicacao)
      queryParams.append('periodo_publicacao', params.periodo_publicacao);

    return this.fetchApi(`/api/videos?${queryParams.toString()}`);
  }

  getFilterOptions = async (): Promise<FilterOptions> => {
    return this.fetchApi<FilterOptions>('/api/filtros');
  }

  addFavorito = async (tipo: 'canal' | 'video', itemId: number): Promise<void> => {
    await this.fetchApi(`/api/favoritos/adicionar?tipo=${tipo}&item_id=${itemId}`, {
      method: 'POST',
    });
  }

  removeFavorito = async (tipo: 'canal' | 'video', itemId: number): Promise<void> => {
    await this.fetchApi(`/api/favoritos/remover?tipo=${tipo}&item_id=${itemId}`, {
      method: 'DELETE',
    });
  }

  getFavoritosCanais = async (): Promise<{ canais: Channel[]; total: number }> => {
    return this.fetchApi('/api/favoritos/canais');
  }

  getFavoritosVideos = async (): Promise<{ videos: Video[]; total: number }> => {
    return this.fetchApi('/api/favoritos/videos');
  }

  addCanal = async (data: {
    nome_canal: string;
    url_canal: string;
    nicho: string;
    subnicho?: string;
    lingua: string;
    tipo: 'minerado' | 'nosso';
    status?: string;
  }): Promise<void> => {
    const queryParams = new URLSearchParams({
      nome_canal: data.nome_canal,
      url_canal: data.url_canal,
      nicho: data.nicho,
      subnicho: data.subnicho || '',
      lingua: data.lingua,
      tipo: data.tipo,
      status: data.status || 'ativo',
    });

    await this.fetchApi(`/api/add-canal?${queryParams.toString()}`, {
      method: 'POST',
    });
  }

  updateCanal = async (
    id: number,
    data: {
      nome_canal: string;
      url_canal: string;
      nicho: string;
      subnicho?: string;
      lingua: string;
      tipo: 'minerado' | 'nosso';
      status?: string;
    }
  ): Promise<void> => {
    const queryParams = new URLSearchParams({
      nome_canal: data.nome_canal,
      url_canal: data.url_canal,
      nicho: data.nicho,
      subnicho: data.subnicho || '',
      lingua: data.lingua,
      tipo: data.tipo,
      status: data.status || 'ativo',
    });

    await this.fetchApi(`/api/canais/${id}?${queryParams.toString()}`, {
      method: 'PUT',
    });
  }

  deleteCanal = async (id: number, permanent: boolean = true): Promise<void> => {
    await this.fetchApi(`/api/canais/${id}?permanent=${permanent}`, {
      method: 'DELETE',
    });
  }

  deactivateCanal = async (id: number): Promise<void> => {
    return this.deleteCanal(id, false);
  }

  // Notificações
  getNotificacoes = async (): Promise<{ notificacoes: Notificacao[]; total: number }> => {
    return this.fetchApi('/api/notificacoes');
  }

  getTodasNotificacoes = async (params?: {
    limit?: number;
    offset?: number;
    vista?: boolean;
    dias?: number;
    tipo_canal?: 'minerado' | 'nosso';
  }): Promise<{ notificacoes: Notificacao[]; total: number }> => {
    const queryParams = new URLSearchParams();
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params?.vista !== undefined) queryParams.append('vista', params.vista.toString());
    if (params?.dias !== undefined) queryParams.append('dias', params.dias.toString());
    if (params?.tipo_canal) queryParams.append('tipo_canal', params.tipo_canal);

    return this.fetchApi(`/api/notificacoes/todas?${queryParams.toString()}`);
  }

  getNotificacoesStats = async (): Promise<NotificacaoStats> => {
    return this.fetchApi('/api/notificacoes/stats');
  }

  marcarNotificacaoVista = async (id: number): Promise<void> => {
    await this.fetchApi(`/api/notificacoes/${id}/marcar-vista`, {
      method: 'PUT',
    });
  }

  desmarcarNotificacaoVista = async (id: number): Promise<void> => {
    await this.fetchApi(`/api/notificacoes/${id}/desmarcar-vista`, {
      method: 'PUT',
    });
  }

  marcarTodasNotificacoesVistas = async (params?: {
    lingua?: string;
    tipo_canal?: 'minerado' | 'nosso';
    subnicho?: string;
    periodo_dias?: number;
  }): Promise<{ message: string; count: number }> => {
    const queryParams = new URLSearchParams();
    if (params?.lingua) queryParams.append('lingua', params.lingua);
    if (params?.tipo_canal) queryParams.append('tipo_canal', params.tipo_canal);
    if (params?.subnicho) queryParams.append('subnicho', params.subnicho);
    if (params?.periodo_dias) queryParams.append('periodo_dias', params.periodo_dias.toString());

    const url = queryParams.toString() 
      ? `/api/notificacoes/marcar-todas?${queryParams.toString()}`
      : '/api/notificacoes/marcar-todas';

    return this.fetchApi(url, {
      method: 'POST',
    });
  }

  // =========================================================================
  // ANALYSIS TAB - New Methods
  // =========================================================================

  async getSubniches(): Promise<SubnichesResponse> {
    return this.fetchApi<SubnichesResponse>('/api/analysis/subniches');
  }

  async getKeywords(subniche: string, days: 7 | 15 | 30 = 30): Promise<KeywordsResponse> {
    const encodedSubniche = encodeURIComponent(subniche);
    return this.fetchApi<KeywordsResponse>(`/api/analysis/keywords?subniche=${encodedSubniche}&days=${days}`);
  }

  async getTitlePatterns(subniche: string, days: 7 | 15 | 30 = 30): Promise<TitlePatternsResponse> {
    const encodedSubniche = encodeURIComponent(subniche);
    return this.fetchApi<TitlePatternsResponse>(`/api/analysis/title-patterns?subniche=${encodedSubniche}&days=${days}`);
  }

  async getTopChannels(subniche: string, days: 7 | 15 | 30 = 30): Promise<TopChannelsResponse> {
    const encodedSubniche = encodeURIComponent(subniche);
    return this.fetchApi<TopChannelsResponse>(`/api/analysis/top-channels?subniche=${encodedSubniche}&days=${days}`);
  }

  async getSubnicheTrends(): Promise<SubnicheTrendsResponse> {
    return this.fetchApi<SubnicheTrendsResponse>('/api/analysis/subniche-trends');
  }

  // =========================================================================
  // CHANNEL TOP VIDEOS
  // =========================================================================

  async getTopVideos(canalId: number): Promise<TopVideosResponse> {
    return this.fetchApi<TopVideosResponse>(`/api/canais/${canalId}/top-videos`);
  }

  // =========================================================================
  // CHANNEL ENGAGEMENT - Comments Analytics
  // =========================================================================

  async getChannelEngagement(canalId: number, page: number = 1, limit: number = 10): Promise<EngagementData> {
    return this.fetchApi<EngagementData>(`/api/canais/${canalId}/engagement?page=${page}&limit=${limit}`);
  }

  // =========================================================================
  // COMMENTS MANAGEMENT - Monetized Channels
  // =========================================================================

  async getCommentsSummary(): Promise<CommentsSummary> {
    return this.fetchApi<CommentsSummary>('/api/comentarios/resumo');
  }

  async getMonetizedChannelsComments(): Promise<MonetizedChannelComments[]> {
    return this.fetchApi<MonetizedChannelComments[]>('/api/comentarios/monetizados');
  }

  async getVideosWithComments(channelId: number): Promise<VideoWithComments[]> {
    return this.fetchApi<VideoWithComments[]>(`/api/canais/${channelId}/videos-com-comentarios`);
  }

  async getCommentsPaginated(videoId: string, page: number = 1, limit: number = 10): Promise<CommentsResponse> {
    return this.fetchApi<CommentsResponse>(`/api/videos/${videoId}/comentarios-paginados?page=${page}&limit=${limit}`);
  }

  async markCommentAsResponded(commentId: string, actualResponse?: string): Promise<void> {
    const body = actualResponse ? JSON.stringify({ actual_response: actualResponse }) : undefined;
    await this.fetchApi(`/api/comentarios/${commentId}/marcar-respondido`, {
      method: 'PATCH',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body,
    });
  }

  async generateCommentResponse(commentId: string): Promise<{ suggested_response: string; response_generated_at: string }> {
    return this.fetchApi<{ suggested_response: string; response_generated_at: string }>(
      `/api/comentarios/${commentId}/gerar-resposta`,
      { method: 'POST' }
    );
  }

  async collectChannelComments(channelId: number): Promise<{ total_coletados: number }> {
    return this.fetchApi<{ total_coletados: number }>(`/api/collect-comments/${channelId}`, {
      method: 'POST',
    });
  }

  // =========================================================================
  // CACHE MANAGEMENT
  // =========================================================================

  clearCache = async (): Promise<{ message: string }> => {
    return this.fetchApi('/api/cache/clear', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}

// =========================================================================
// TYPES - Comments Management
// =========================================================================

export interface CommentsSummary {
  canais_monetizados: number;
  total_comentarios: number;
  novos_hoje: number;
  aguardando_resposta: number;
}

export interface MonetizedChannelComments {
  id: number;
  nome_canal: string;
  subnicho: string;
  lingua: string;
  url_canal?: string;
  total_comentarios: number;
  comentarios_sem_resposta: number;
  total_videos: number;
  engagement_rate: number;
}

export interface VideoWithComments {
  video_id: string;
  titulo: string;
  data_publicacao: string;
  total_comentarios: number;
  comentarios_sem_resposta: number;
  views: number;  // API retorna 'views', não 'views_atuais'
  thumbnail?: string;
}

export interface Comment {
  id: string;
  author_name: string;
  comment_text_original: string;
  comment_text_pt: string | null;
  suggested_response: string;
  like_count: number;
  published_at: string;
  is_responded: boolean;
}

export interface CommentsResponse {
  comments: Comment[];  // Backend atualizado retorna 'comments'
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

import type { EngagementData } from '@/types/comments';

export const apiService = new ApiService();
