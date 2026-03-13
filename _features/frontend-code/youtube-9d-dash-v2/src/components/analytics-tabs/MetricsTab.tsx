import React from 'react';
import { Channel } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Eye, BarChart3, Zap, Target, Video, Calendar, Minus } from 'lucide-react';
import { formatNumber } from '@/utils/formatters';

interface MetricsTabProps {
  canal: Channel;
}

// Cores fixas para métricas
const CORES_METRICAS = {
  views: { fundo: '#059669', texto: 'text-green-200' },       // Verde
  engagement: { fundo: '#EA580C', texto: 'text-orange-200' }, // Laranja
  resumo: { fundo: '#3B82F6', texto: 'text-blue-200' }        // Azul
};

// Função para cor dinâmica do growth (aceita null)
const getGrowthCardColor = (value: number | null | undefined) => {
  if (value == null) return { fundo: '#6B7280', texto: 'text-gray-200' };  // Cinza
  if (value > 0) return { fundo: '#059669', texto: 'text-green-200' };     // Verde
  if (value < 0) return { fundo: '#DC2626', texto: 'text-red-200' };       // Vermelho
  return { fundo: '#6B7280', texto: 'text-gray-200' };                      // Cinza neutro
};

// Função para cor dinâmica do score
const getScoreCardColor = (value: number) => {
  if (value >= 80) return { fundo: '#059669', texto: 'text-green-200' };  // Verde
  if (value >= 60) return { fundo: '#F59E0B', texto: 'text-yellow-200' }; // Amarelo
  if (value >= 40) return { fundo: '#EA580C', texto: 'text-orange-200' }; // Laranja
  return { fundo: '#DC2626', texto: 'text-red-200' };                      // Vermelho
};

export const MetricsTab: React.FC<MetricsTabProps> = ({ canal }) => {
  // Não usar fallback ?? 0 para que null seja tratado corretamente
  const growth7d = canal.views_growth_7d;
  const growth30d = canal.views_growth_30d;
  const engagementRate = canal.engagement_rate ?? 0;
  const score = canal.score_calculado ?? 0;
  
  // Métricas calculadas
  const avgViewsPerVideo = canal.videos_publicados_7d && canal.videos_publicados_7d > 0
    ? Math.round((canal.views_7d || 0) / canal.videos_publicados_7d)
    : 0;
  const uploadFrequency = canal.videos_publicados_7d 
    ? (canal.videos_publicados_7d / 7).toFixed(1) 
    : '0';
  const views7dPct = canal.views_30d && canal.views_30d > 0 
    ? ((canal.views_7d || 0) / canal.views_30d * 100).toFixed(0)
    : '0';

  // Formata growth mostrando "—" quando null
  const formatGrowth = (value: number | null | undefined) => {
    if (value == null) return '—';
    const formatted = value.toFixed(1);
    return value >= 0 ? `+${formatted}%` : `${formatted}%`;
  };

  // Cores dinâmicas
  const growth7dColor = getGrowthCardColor(growth7d);
  const growth30dColor = getGrowthCardColor(growth30d);
  const scoreColor = getScoreCardColor(score);

  // Renderiza ícone correto baseado no valor
  const renderGrowthIcon = (value: number | null | undefined, className: string) => {
    if (value == null) return <Minus className={className} />;
    if (value >= 0) return <TrendingUp className={className} />;
    return <TrendingDown className={className} />;
  };

  return (
    <div className="space-y-4 fade-in">
      {/* Views Grid - 3 colunas */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3">
        <Card className="border-0" style={{ backgroundColor: CORES_METRICAS.views.fundo + '5E' }}>
          <CardContent className="pt-3 pb-2 sm:pt-4 sm:pb-3">
            <div className={`flex items-center gap-1.5 ${CORES_METRICAS.views.texto} mb-1`}>
              <Eye className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Views 7d</span>
            </div>
            <p className="text-base sm:text-lg font-bold text-white">
              {formatNumber(canal.views_7d || 0)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-0" style={{ backgroundColor: CORES_METRICAS.views.fundo + '5E' }}>
          <CardContent className="pt-3 pb-2 sm:pt-4 sm:pb-3">
            <div className={`flex items-center gap-1.5 ${CORES_METRICAS.views.texto} mb-1`}>
              <Eye className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Views 15d</span>
            </div>
            <p className="text-base sm:text-lg font-bold text-white">
              {formatNumber(canal.views_15d || 0)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-0" style={{ backgroundColor: CORES_METRICAS.views.fundo + '5E' }}>
          <CardContent className="pt-3 pb-2 sm:pt-4 sm:pb-3">
            <div className={`flex items-center gap-1.5 ${CORES_METRICAS.views.texto} mb-1`}>
              <Eye className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Views 30d</span>
            </div>
            <p className="text-base sm:text-lg font-bold text-white">
              {formatNumber(canal.views_30d || 0)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Growth & Performance */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3">
        {/* Growth 7d */}
        <Card className="border-0" style={{ backgroundColor: growth7dColor.fundo + '5E' }}>
          <CardContent className="pt-3 pb-2 sm:pt-4 sm:pb-3">
            <div className={`flex items-center gap-1.5 ${growth7dColor.texto} mb-1`}>
              {renderGrowthIcon(growth7d, "h-3.5 w-3.5 sm:h-4 sm:w-4")}
              <span className="text-[10px] sm:text-xs">Growth 7d</span>
            </div>
            <p className="text-base sm:text-lg font-bold text-white">
              {formatGrowth(growth7d)}
            </p>
          </CardContent>
        </Card>

        {/* Growth 30d */}
        <Card className="border-0" style={{ backgroundColor: growth30dColor.fundo + '5E' }}>
          <CardContent className="pt-3 pb-2 sm:pt-4 sm:pb-3">
            <div className={`flex items-center gap-1.5 ${growth30dColor.texto} mb-1`}>
              {renderGrowthIcon(growth30d, "h-3.5 w-3.5 sm:h-4 sm:w-4")}
              <span className="text-[10px] sm:text-xs">Growth 30d</span>
            </div>
            <p className="text-base sm:text-lg font-bold text-white">
              {formatGrowth(growth30d)}
            </p>
          </CardContent>
        </Card>

        {/* Engagement Rate - Laranja */}
        <Card className="border-0" style={{ backgroundColor: CORES_METRICAS.engagement.fundo + '5E' }}>
          <CardContent className="pt-3 pb-2 sm:pt-4 sm:pb-3">
            <div className={`flex items-center gap-1.5 ${CORES_METRICAS.engagement.texto} mb-1`}>
              <Zap className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Engagement</span>
            </div>
            <p className="text-base sm:text-lg font-bold text-white">
              {engagementRate.toFixed(2)}%
            </p>
          </CardContent>
        </Card>

        {/* Score - Cor dinâmica */}
        <Card className="border-0" style={{ backgroundColor: scoreColor.fundo + '5E' }}>
          <CardContent className="pt-3 pb-2 sm:pt-4 sm:pb-3">
            <div className={`flex items-center gap-1.5 ${scoreColor.texto} mb-1`}>
              <Target className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Score</span>
            </div>
            <p className="text-base sm:text-lg font-bold text-white">
              {score.toFixed(0)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Resumo de Performance - Azul com mini-cards */}
      <Card className="border-0" style={{ backgroundColor: CORES_METRICAS.resumo.fundo + '5E' }}>
        <CardHeader className="py-3 pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2 text-white">
            <BarChart3 className="h-4 w-4" />
            Resumo de Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="py-2 sm:py-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3">
            <div className="bg-white/10 rounded-lg p-2 sm:p-3 text-center">
              <Video className="h-4 w-4 sm:h-5 sm:w-5 text-blue-200 mx-auto mb-1" />
              <p className="text-[10px] sm:text-xs text-blue-200">Vídeos 7d</p>
              <p className="font-bold text-white text-base sm:text-lg">{canal.videos_publicados_7d ?? 0}</p>
            </div>

            <div className="bg-white/10 rounded-lg p-2 sm:p-3 text-center">
              <Eye className="h-4 w-4 sm:h-5 sm:w-5 text-blue-200 mx-auto mb-1" />
              <p className="text-[10px] sm:text-xs text-blue-200">Média/Vídeo</p>
              <p className="font-bold text-white text-base sm:text-lg">{formatNumber(avgViewsPerVideo)}</p>
            </div>

            <div className="bg-white/10 rounded-lg p-2 sm:p-3 text-center">
              <Calendar className="h-4 w-4 sm:h-5 sm:w-5 text-blue-200 mx-auto mb-1" />
              <p className="text-[10px] sm:text-xs text-blue-200">Freq. Upload</p>
              <p className="font-bold text-white text-base sm:text-lg">{uploadFrequency}/dia</p>
            </div>

            <div className="bg-white/10 rounded-lg p-2 sm:p-3 text-center">
              <TrendingUp className="h-4 w-4 sm:h-5 sm:w-5 text-blue-200 mx-auto mb-1" />
              <p className="text-[10px] sm:text-xs text-blue-200">7d vs 30d</p>
              <p className="font-bold text-white text-base sm:text-lg">{views7dPct}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
