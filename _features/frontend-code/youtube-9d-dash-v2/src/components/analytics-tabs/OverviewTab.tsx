import React from 'react';
import { Channel } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ColoredBadge } from '@/components/ui/colored-badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, Users, Eye, Video, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatNumber } from '@/utils/formatters';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';

interface OverviewTabProps {
  canal: Channel;
}

// Cores fixas para os cards de estatísticas
const CORES_STATS = {
  inscritos: { fundo: '#3B82F6', texto: 'text-blue-200' },    // Azul
  views: { fundo: '#059669', texto: 'text-green-200' },       // Verde
  videos: { fundo: '#F59E0B', texto: 'text-yellow-200' }      // Amarelo
};

// Formata diferença de views em formato legível (K, M)
const formatViewsDiff = (diff: number | null | undefined): string => {
  if (diff == null) return '';
  const absDiff = Math.abs(diff);
  if (absDiff >= 1000000) return `${(absDiff / 1000000).toFixed(1)}M`;
  if (absDiff >= 1000) return `${(absDiff / 1000).toFixed(1)}K`;
  return absDiff.toString();
};

export const OverviewTab: React.FC<OverviewTabProps> = ({ canal }) => {
  const cores = obterCorSubnicho(canal.subnicho);
  const inscritosDiff = canal.inscritos_diff ?? 0;
  const isGrowthPositive = inscritosDiff >= 0;

  return (
    <div className="space-y-4 fade-in">
      {/* Header Card */}
      <Card 
        className="border-l-4 border-0" 
        style={{ 
          borderLeftColor: cores.borda,
          backgroundColor: cores.fundo + '5E'
        }}
      >
        <CardHeader className="pb-2 px-3 sm:px-6">
          <div className="flex items-start sm:items-center justify-between gap-2 flex-wrap">
            <CardTitle className="text-base sm:text-xl font-bold text-white">
              {getSubnichoEmoji(canal.subnicho)} {canal.nome_canal}
            </CardTitle>
            {canal.url_canal && (
              <Button asChild variant="outline" size="sm" className="text-xs h-7 sm:h-9">
                <a
                  href={canal.url_canal}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Abrir no YouTube</span>
                  <span className="sm:hidden">YouTube</span>
                </a>
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            <ColoredBadge text={canal.subnicho} type="subnicho" />
            <ColoredBadge text={canal.lingua} type="language" />
            <Badge 
              className={`capitalize ${
                canal.tipo === 'nosso' 
                  ? 'bg-green-600 text-white border-green-700' 
                  : 'bg-blue-600 text-white border-blue-700'
              }`}
            >
              {canal.tipo}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3">
        {/* Inscritos */}
        <Card className="border-0" style={{ backgroundColor: CORES_STATS.inscritos.fundo + '5E' }}>
          <CardContent className="pt-3 sm:pt-4">
            <div className={`flex items-center gap-1.5 ${CORES_STATS.inscritos.texto} mb-1`}>
              <Users className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Inscritos</span>
            </div>
            <p className="text-base sm:text-xl font-bold text-white">
              {formatNumber(canal.inscritos || 0)}
            </p>
            {inscritosDiff !== 0 && (
              <div className={`flex items-center gap-1 text-xs mt-1 ${
                isGrowthPositive ? 'text-growth-positive' : 'text-growth-negative'
              }`}>
                {isGrowthPositive ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                <span>{isGrowthPositive ? '+' : ''}{formatNumber(inscritosDiff)} hoje</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Views 7d - Diferença Absoluta */}
        <Card className="border-0" style={{ backgroundColor: CORES_STATS.views.fundo + '5E' }}>
          <CardContent className="pt-3 sm:pt-4">
            <div className={`flex items-center gap-1.5 ${CORES_STATS.views.texto} mb-1`}>
              <Eye className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Views 7d</span>
            </div>
            <p className="text-base sm:text-xl font-bold text-white">
              {formatNumber(canal.views_7d || 0)}
            </p>
            {canal.views_diff_7d != null ? (
              <div className={`flex items-center gap-1 text-[10px] mt-1 ${
                canal.views_diff_7d >= 0 ? 'text-growth-positive' : 'text-growth-negative'
              }`}>
                {canal.views_diff_7d >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                <span className="whitespace-nowrap">
                  {canal.views_diff_7d >= 0 ? '+' : '-'}
                  {formatViewsDiff(canal.views_diff_7d)} vs anterior
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-xs mt-1 text-muted-foreground">
                <Minus className="h-3 w-3" />
                <span>Sem histórico</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Views 30d - Diferença Absoluta */}
        <Card className="border-0" style={{ backgroundColor: CORES_STATS.views.fundo + '5E' }}>
          <CardContent className="pt-3 sm:pt-4">
            <div className={`flex items-center gap-1.5 ${CORES_STATS.views.texto} mb-1`}>
              <Eye className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Views 30d</span>
            </div>
            <p className="text-base sm:text-xl font-bold text-white">
              {formatNumber(canal.views_30d || 0)}
            </p>
            {canal.views_diff_30d != null ? (
              <div className={`flex items-center gap-1 text-[10px] mt-1 ${
                canal.views_diff_30d >= 0 ? 'text-growth-positive' : 'text-growth-negative'
              }`}>
                {canal.views_diff_30d >= 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                <span className="whitespace-nowrap">
                  {canal.views_diff_30d >= 0 ? '+' : '-'}
                  {formatViewsDiff(canal.views_diff_30d)} vs anterior
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-xs mt-1 text-muted-foreground">
                <Minus className="h-3 w-3" />
                <span>Sem histórico</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Vídeos Publicados */}
        <Card className="border-0" style={{ backgroundColor: CORES_STATS.videos.fundo + '5E' }}>
          <CardContent className="pt-3 sm:pt-4">
            <div className={`flex items-center gap-1.5 ${CORES_STATS.videos.texto} mb-1`}>
              <Video className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              <span className="text-[10px] sm:text-xs">Vídeos (7d)</span>
            </div>
            <p className="text-base sm:text-xl font-bold text-white">
              {canal.videos_publicados_7d ?? 0}
            </p>
          </CardContent>
        </Card>
      </div>

    </div>
  );
};
