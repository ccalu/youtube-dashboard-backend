import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Channel, apiService } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Video, 
  Eye, 
  TrendingUp, 
  BarChart3, 
  Target, 
  Play,
  ThumbsUp,
  MessageSquare,
  ExternalLink,
  Clock
} from 'lucide-react';
import { formatNumber } from '@/utils/formatters';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface TopVideosTabProps {
  canal: Channel;
}

// Cores dos cards
const CORES_CARDS = {
  videos: { fundo: '#F59E0B', texto: 'text-yellow-200' },
  views: { fundo: '#059669', texto: 'text-green-200' },
  media: { fundo: '#3B82F6', texto: 'text-blue-200' },
  performance: {
    excelente: { fundo: '#059669', label: 'Excelente' },
    muitoBom: { fundo: '#10B981', label: 'Muito Bom' },
    bom: { fundo: '#F59E0B', label: 'Bom' },
    regular: { fundo: '#F97316', label: 'Regular' },
    emDev: { fundo: '#6B7280', label: 'Em desenvolvimento' }
  }
};

// Formatar duração em mm:ss ou hh:mm:ss
const formatDuration = (seconds: number): string => {
  if (!seconds) return '--:--';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

export const TopVideosTab: React.FC<TopVideosTabProps> = ({ canal }) => {
  // Buscar top videos do canal
  const { data: topVideosData, isLoading } = useQuery({
    queryKey: ['topVideos', canal.id],
    queryFn: () => apiService.getTopVideos(canal.id),
    enabled: !!canal.id
  });

  const topVideos = topVideosData?.top_videos || [];

  // Métricas calculadas com dados totais
  const totalVideos = canal.total_videos || 0;
  const totalViews = canal.total_views || 0;
  const avgViewsPerVideo = totalVideos > 0 ? Math.round(totalViews / totalVideos) : 0;

  // Análise de performance
  const getPerformanceStyle = () => {
    if (avgViewsPerVideo > 100000) return CORES_CARDS.performance.excelente;
    if (avgViewsPerVideo > 50000) return CORES_CARDS.performance.muitoBom;
    if (avgViewsPerVideo > 20000) return CORES_CARDS.performance.bom;
    if (avgViewsPerVideo > 5000) return CORES_CARDS.performance.regular;
    return CORES_CARDS.performance.emDev;
  };

  const performance = getPerformanceStyle();

  return (
    <div className="space-y-4 fade-in">
      {/* Stats Summary - 3 Cards */}
      <div className="grid grid-cols-3 gap-3">
        {/* Vídeos Totais - Amarelo */}
        <Card className="border-0" style={{ backgroundColor: CORES_CARDS.videos.fundo + '5E' }}>
          <CardContent className="pt-4 pb-3">
            <div className={`flex items-center gap-2 ${CORES_CARDS.videos.texto} mb-1`}>
              <Video className="h-4 w-4" />
              <span className="text-xs">Vídeos Totais</span>
            </div>
            <p className="text-xl font-bold text-white">
              {totalVideos}
            </p>
          </CardContent>
        </Card>

        {/* Views Totais - Verde */}
        <Card className="border-0" style={{ backgroundColor: CORES_CARDS.views.fundo + '5E' }}>
          <CardContent className="pt-4 pb-3">
            <div className={`flex items-center gap-2 ${CORES_CARDS.views.texto} mb-1`}>
              <Eye className="h-4 w-4" />
              <span className="text-xs">Views Totais</span>
            </div>
            <p className="text-xl font-bold text-white">
              {formatNumber(totalViews)}
            </p>
          </CardContent>
        </Card>

        {/* Média por Vídeo - Azul */}
        <Card className="border-0" style={{ backgroundColor: CORES_CARDS.media.fundo + '5E' }}>
          <CardContent className="pt-4 pb-3">
            <div className={`flex items-center gap-2 text-blue-200 mb-1`}>
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs">Média/Vídeo</span>
            </div>
            <p className="text-xl font-bold text-white">
              {formatNumber(avgViewsPerVideo)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Card de Performance - Cor Dinâmica */}
      <Card className="border-0" style={{ backgroundColor: performance.fundo + '3D' }}>
        <CardHeader className="py-3 pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2 text-white">
            <BarChart3 className="h-4 w-4" />
            Análise de Performance de Vídeos
          </CardTitle>
        </CardHeader>
        <CardContent className="py-3">
          {/* Performance Badge */}
          <div 
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full"
            style={{ backgroundColor: performance.fundo + '60' }}
          >
            <Target className="h-4 w-4 text-white" />
            <span className="text-sm font-medium text-white">{performance.label}</span>
          </div>
          
          <p className="text-xs text-white/70 mt-2">
            Baseado na média de {formatNumber(avgViewsPerVideo)} views por vídeo
          </p>
        </CardContent>
      </Card>

      {/* Top 5 Vídeos Mais Vistos */}
      <Card>
        <CardHeader className="py-3 pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Play className="h-4 w-4" />
            Top 5 Vídeos Mais Vistos
          </CardTitle>
        </CardHeader>
        <CardContent className="py-3">
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex gap-3 p-2">
                  <Skeleton className="w-24 h-16 rounded flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : topVideos.length > 0 ? (
            <div className="space-y-3">
              {topVideos.map((video, index) => (
                <div 
                  key={video.video_id} 
                  className="flex items-start gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                  {/* Ranking + Thumbnail */}
                  <div className="relative flex-shrink-0">
                    <img 
                      src={video.url_thumbnail} 
                      alt={video.titulo}
                      className="w-24 h-16 object-cover rounded"
                      loading="lazy"
                    />
                    <span className="absolute -top-2 -left-2 bg-primary text-primary-foreground w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-md">
                      {index + 1}
                    </span>
                    {/* Duração overlay */}
                    <span className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] px-1 rounded">
                      {formatDuration(video.duracao)}
                    </span>
                  </div>
                  
                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <a 
                      href={video.url_video} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="font-medium hover:underline line-clamp-2 text-sm text-foreground"
                    >
                      {video.titulo}
                    </a>
                    <div className="flex flex-wrap items-center gap-2 mt-1.5 text-[11px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {format(new Date(video.data_publicacao), 'dd MMM yyyy', { locale: ptBR })}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="h-3 w-3" />
                        {formatNumber(video.views_atuais)}
                      </span>
                      <span className="flex items-center gap-1">
                        <ThumbsUp className="h-3 w-3" />
                        {formatNumber(video.likes)}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" />
                        {formatNumber(video.comentarios)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Link externo */}
                  <a 
                    href={video.url_video} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-shrink-0 p-1 hover:bg-muted rounded"
                  >
                    <ExternalLink className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors" />
                  </a>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">
              Nenhum vídeo encontrado para este canal
            </p>
          )}
        </CardContent>
      </Card>

    </div>
  );
};
