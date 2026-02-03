import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  Users,
  Eye,
  Video,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Info
} from 'lucide-react';

interface ModalAnalyticsProps {
  canalId: number;
  isOpen: boolean;
  onClose: () => void;
}

interface AnalyticsData {
  canal_info: {
    id: number;
    nome: string;
    subnicho: string;
    lingua: string;
    tipo: string;
    url: string;
    criado_em: string | null;
    custom_url: string | null;
    inscritos: number;
    total_videos: number;
    total_views: number;
    frequencia_semanal: number;
  };
  metricas: {
    views_7d: number;
    views_15d: number;
    views_30d: number;
    growth_7d: number;
    growth_15d: number;
    growth_30d: number;
    engagement_rate: number;
    score: number;
    inscritos_diff: number;
    ranking_subnicho: number;
    percentil: number;
  };
  top_videos: Array<{
    video_id: string;
    titulo: string;
    url: string;
    thumbnail_url: string;
    views: number;
    likes: number;
    comentarios: number;
    duracao: number;
    publicado_ha_dias: number;
    engagement_rate: number;
    views_por_dia: number;
  }>;
  padroes: Array<{
    tipo: string;
    descricao: string;
    boost: string;
    evidencia: string;
    exemplos?: string[];
    keywords?: string[];
    range_ideal?: string;
  }>;
  clusters: Array<{
    tema: string;
    categoria: string;
    emoji: string;
    quantidade_videos: number;
    percentual_videos: number;
    media_views: number;
    percentual_views: number;
    roi: number;
  }>;
  anomalias: Array<{
    tipo: string;
    gravidade: string;
    emoji: string;
    descricao: string;
    detalhes: string;
    data?: string;
  }>;
  melhor_momento: {
    dia_semana: string | null;
    dia_numero: number | null;
    hora: number | null;
    boost: number;
    mensagem: string;
    ranking_dias?: Array<{
      dia: string;
      performance: number;
    }>;
  };
}

export function ModalAnalytics({ canalId, isOpen, onClose }: ModalAnalyticsProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (isOpen && canalId) {
      fetchAnalytics();
    }
  }, [isOpen, canalId]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/canais/${canalId}/analytics`);

      if (!response.ok) {
        throw new Error('Erro ao carregar analytics');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      month: 'long',
      year: 'numeric'
    });
  };

  const getGrowthIcon = (growth: number) => {
    if (growth > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (growth < 0) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return null;
  };

  const getGrowthColor = (growth: number): string => {
    if (growth > 0) return 'text-green-500';
    if (growth < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
      case 'success': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl h-[90vh] p-0 bg-gray-900 text-white">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-gray-800">
          <DialogTitle className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            Channel Analytics
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="p-6 space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        ) : error ? (
          <Alert className="m-6 bg-red-900 border-red-800">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : data ? (
          <div className="flex flex-col h-full">
            {/* Header com informações básicas */}
            <div className="px-6 py-4 bg-gray-800/50">
              <h3 className="text-xl font-semibold mb-2">
                📺 {data.canal_info.nome} ({data.canal_info.subnicho})
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">📅 Criado em:</span>
                  <span className="ml-2">{formatDate(data.canal_info.criado_em)}</span>
                </div>
                <div>
                  <span className="text-gray-400">🎬 Vídeos:</span>
                  <span className="ml-2">{data.canal_info.total_videos} | {data.canal_info.frequencia_semanal?.toFixed(1)}/sem</span>
                </div>
                <div>
                  <span className="text-gray-400">👥 Inscritos:</span>
                  <span className="ml-2">
                    {formatNumber(data.canal_info.inscritos)}
                    {data.metricas.inscritos_diff !== 0 && (
                      <span className={`ml-1 text-xs ${getGrowthColor(data.metricas.inscritos_diff)}`}>
                        ({data.metricas.inscritos_diff > 0 ? '+' : ''}{data.metricas.inscritos_diff})
                      </span>
                    )}
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">👁️ Views totais:</span>
                  <span className="ml-2">{formatNumber(data.canal_info.total_views)}</span>
                </div>
              </div>
              {data.melhor_momento.dia_semana && (
                <div className="mt-3 p-2 bg-blue-900/30 rounded-lg">
                  <span className="text-sm">
                    📅 Melhor momento para postar:
                    <span className="font-semibold ml-2">
                      {data.melhor_momento.mensagem}
                    </span>
                    <Badge className="ml-2 bg-green-600">
                      +{data.melhor_momento.boost}% views
                    </Badge>
                  </span>
                </div>
              )}
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
              <TabsList className="grid grid-cols-5 w-full px-6 bg-gray-800 border-b border-gray-700">
                <TabsTrigger value="overview">Visão Geral</TabsTrigger>
                <TabsTrigger value="metrics">Métricas</TabsTrigger>
                <TabsTrigger value="videos">Top Vídeos</TabsTrigger>
                <TabsTrigger value="patterns">Padrões</TabsTrigger>
                <TabsTrigger value="diagnostics">Diagnóstico</TabsTrigger>
              </TabsList>

              <ScrollArea className="flex-1">
                {/* Tab: Visão Geral */}
                <TabsContent value="overview" className="p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className="bg-gray-800 border-gray-700">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-400">
                          Score de Performance
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{data.metricas.score}/100</div>
                        <p className="text-xs text-gray-500 mt-1">Baseado em views/inscrito</p>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-800 border-gray-700">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-400">
                          Engagement Rate
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">{data.metricas.engagement_rate}%</div>
                        <p className="text-xs text-gray-500 mt-1">Likes + Comments / Views</p>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-800 border-gray-700">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-gray-400">
                          Frequência
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold">
                          {data.canal_info.frequencia_semanal?.toFixed(1) || '0'}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Vídeos por semana</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Quick Stats */}
                  <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                      <CardTitle>📊 Estatísticas Rápidas</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Média de views por vídeo:</span>
                        <span className="font-semibold">
                          {data.top_videos.length > 0
                            ? formatNumber(Math.round(
                                data.top_videos.reduce((acc, v) => acc + v.views, 0) / data.top_videos.length
                              ))
                            : '0'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Duração média:</span>
                        <span className="font-semibold">
                          {data.top_videos.length > 0
                            ? formatDuration(Math.round(
                                data.top_videos.reduce((acc, v) => acc + v.duracao, 0) / data.top_videos.length
                              ))
                            : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Melhor engagement:</span>
                        <span className="font-semibold">
                          {data.top_videos.length > 0
                            ? `${Math.max(...data.top_videos.map(v => v.engagement_rate)).toFixed(2)}%`
                            : 'N/A'}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Tab: Métricas */}
                <TabsContent value="metrics" className="p-6 space-y-4">
                  <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                      <CardTitle>📈 Views por Período</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-gray-400">Últimos 7 dias:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-2xl font-bold">{formatNumber(data.metricas.views_7d)}</span>
                            <Badge className={data.metricas.growth_7d > 0 ? 'bg-green-600' : 'bg-red-600'}>
                              {data.metricas.growth_7d > 0 ? '+' : ''}{data.metricas.growth_7d.toFixed(1)}%
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-gray-400">Últimos 15 dias:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-2xl font-bold">{formatNumber(data.metricas.views_15d)}</span>
                            <Badge className={data.metricas.growth_15d > 0 ? 'bg-green-600' : 'bg-red-600'}>
                              {data.metricas.growth_15d > 0 ? '+' : ''}{data.metricas.growth_15d.toFixed(1)}%
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-gray-400">Últimos 30 dias:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-2xl font-bold">{formatNumber(data.metricas.views_30d)}</span>
                            <Badge className={data.metricas.growth_30d > 0 ? 'bg-green-600' : 'bg-red-600'}>
                              {data.metricas.growth_30d > 0 ? '+' : ''}{data.metricas.growth_30d.toFixed(1)}%
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-2 gap-4">
                    <Card className="bg-gray-800 border-gray-700">
                      <CardHeader>
                        <CardTitle className="text-sm">💬 Engagement</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{data.metricas.engagement_rate}%</div>
                      </CardContent>
                    </Card>

                    <Card className="bg-gray-800 border-gray-700">
                      <CardHeader>
                        <CardTitle className="text-sm">🏆 Score</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{data.metricas.score}/100</div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* Tab: Top Vídeos */}
                <TabsContent value="videos" className="p-6">
                  <div className="space-y-3">
                    {data.top_videos.map((video, index) => (
                      <Card key={video.video_id} className="bg-gray-800 border-gray-700">
                        <CardContent className="p-4">
                          <div className="flex gap-4">
                            <img
                              src={video.thumbnail_url}
                              alt={video.titulo}
                              className="w-32 h-20 object-cover rounded"
                            />
                            <div className="flex-1">
                              <h4 className="font-semibold mb-1 line-clamp-2">
                                {index + 1}. {video.titulo}
                              </h4>
                              <div className="flex gap-4 text-sm text-gray-400">
                                <span>{formatNumber(video.views)} views</span>
                                <span>há {video.publicado_ha_dias} dias</span>
                              </div>
                              <div className="flex gap-4 mt-2 text-sm">
                                <span>❤️ {formatNumber(video.likes)}</span>
                                <span>💬 {formatNumber(video.comentarios)}</span>
                                <span>⏱️ {formatDuration(video.duracao)}</span>
                                <Badge className="bg-blue-600">
                                  {video.engagement_rate.toFixed(2)}% engagement
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                {/* Tab: Padrões */}
                <TabsContent value="patterns" className="p-6 space-y-4">
                  {/* Padrões de Sucesso */}
                  <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                      <CardTitle>🧠 Padrões Identificados</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {data.padroes.length > 0 ? (
                        data.padroes.map((padrao, index) => (
                          <div key={index} className="p-3 bg-gray-900 rounded-lg">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-semibold">✅ {padrao.descricao}</h4>
                              <Badge className="bg-green-600">{padrao.boost} views</Badge>
                            </div>
                            <p className="text-sm text-gray-400 mb-2">{padrao.evidencia}</p>
                            {padrao.exemplos && padrao.exemplos.length > 0 && (
                              <div className="text-sm">
                                <span className="text-gray-500">Exemplos:</span>
                                <ul className="mt-1 space-y-1">
                                  {padrao.exemplos.slice(0, 2).map((ex, i) => (
                                    <li key={i} className="text-gray-400 truncate">• {ex}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {padrao.range_ideal && (
                              <p className="text-sm text-blue-400 mt-2">
                                💡 Ideal: {padrao.range_ideal}
                              </p>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-gray-500">Dados insuficientes para identificar padrões</p>
                      )}
                    </CardContent>
                  </Card>

                  {/* Clustering */}
                  <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                      <CardTitle>🎯 Agrupamento por Performance</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {data.clusters.map((cluster, index) => (
                        <div key={index} className="p-3 bg-gray-900 rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <span className="text-lg mr-2">{cluster.emoji}</span>
                              <span className="font-semibold">{cluster.tema}</span>
                            </div>
                            <Badge className={
                              cluster.categoria === 'alto' ? 'bg-green-600' :
                              cluster.categoria === 'medio' ? 'bg-yellow-600' :
                              'bg-red-600'
                            }>
                              ROI: {cluster.roi}x
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                            <span>• {cluster.quantidade_videos} vídeos ({cluster.percentual_videos}%)</span>
                            <span>• {cluster.percentual_views}% das views</span>
                            <span>• Média: {formatNumber(cluster.media_views)} views</span>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Tab: Diagnóstico */}
                <TabsContent value="diagnostics" className="p-6 space-y-4">
                  <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                      <CardTitle>🔍 Análise Inteligente</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {data.anomalias.length > 0 ? (
                        data.anomalias.map((anomalia, index) => (
                          <Alert key={index} className={`${getSeverityColor(anomalia.gravidade)} bg-opacity-20 border-0`}>
                            <div className="flex items-start gap-3">
                              <span className="text-2xl">{anomalia.emoji}</span>
                              <div>
                                <p className="font-semibold">{anomalia.descricao}</p>
                                <p className="text-sm mt-1">{anomalia.detalhes}</p>
                                {anomalia.data && (
                                  <p className="text-xs text-gray-400 mt-1">Data: {anomalia.data}</p>
                                )}
                              </div>
                            </div>
                          </Alert>
                        ))
                      ) : (
                        <Alert className="bg-green-900/20 border-green-800">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <AlertDescription>
                            Nenhuma anomalia detectada. Canal operando normalmente.
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>

                  {/* Status da Coleta */}
                  <Card className="bg-gray-800 border-gray-700">
                    <CardHeader>
                      <CardTitle>✅ Status de Saúde</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Tipo de canal:</span>
                          <Badge>{data.canal_info.tipo}</Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Língua:</span>
                          <span>{data.canal_info.lingua}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Score de performance:</span>
                          <span className="font-semibold">{data.metricas.score}/100</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </ScrollArea>
            </Tabs>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}