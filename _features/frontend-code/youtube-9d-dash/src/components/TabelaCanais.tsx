import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, RefreshCw, TableIcon } from 'lucide-react';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { SkeletonSubnichoCard } from '@/components/ui/skeleton';
import { useQuery } from '@tanstack/react-query';
import { apiService, Channel } from '@/services/api';

export function TabelaCanais() {
  const { data, isLoading: loading, error, refetch } = useQuery({
    queryKey: ['our-channels'], // MESMO CACHE que OurChannelsTable
    queryFn: () => apiService.getOurChannels(),
  });

  // Agrupar canais por subnicho no frontend
  const grupos = useMemo(() => {
    if (!data?.canais) return {};
    
    const grouped: Record<string, Channel[]> = {};
    
    data.canais
      .filter(canal => canal.tipo === 'nosso')
      .forEach(canal => {
        const subnicho = canal.subnicho || 'Sem Subnicho';
        if (!grouped[subnicho]) {
          grouped[subnicho] = [];
        }
        grouped[subnicho].push(canal);
      });
    
    // Ordenar canais dentro de cada grupo por inscritos_diff (maior ganho primeiro)
    Object.keys(grouped).forEach(key => {
      grouped[key].sort((a, b) => {
        const diffA = a.inscritos_diff ?? 0;
        const diffB = b.inscritos_diff ?? 0;
        return diffB - diffA;
      });
    });
    
    return grouped;
  }, [data?.canais]);

  const formatNumber = (num: number): string => {
    return num.toLocaleString('pt-BR');
  };

  const getGrowthIcon = (diff: number | null) => {
    if (diff === null || diff === 0) {
      return <Minus className="h-4 w-4 text-muted-foreground" />;
    }
    if (diff > 0) {
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    }
    return <TrendingDown className="h-4 w-4 text-red-600" />;
  };

  const getGrowthColor = (diff: number | null): string => {
    if (diff === null || diff === 0) return 'text-muted-foreground';
    if (diff > 0) return 'text-green-600 font-semibold';
    return 'text-red-600 font-semibold';
  };

  const formatGrowth = (diff: number | null): string => {
    if (diff === null) return '--';
    if (diff === 0) return '0';
    if (diff > 0) return `+${diff}`;
    return `${diff}`;
  };

  const openYouTube = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  // Ordem fixa dos subnichos (Monetizados primeiro, Desmonetizado último)
  const SUBNICHE_ORDER = [
    'monetizados',
    'reis perversos',
    'historias sombrias',
    'culturas macabras',
    'relatos de guerra',
    'frentes de guerra',
    'guerras e civilizacoes',
    'licoes de vida',
    'registros malditos',
  ];

  // Subnicho que sempre fica por último
  const LAST_SUBNICHE = ['desmonetizado', 'desmonetizados'];

  // Subnichos a serem excluídos
  const EXCLUDED_SUBNICHES = ['historias aleatorias', 'contos familiares'];

  const normalizeString = (str: string) => 
    str.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

  // getSubnichoEmoji now imported from @/utils/subnichoEmojis

  // Override de bandeira para canais específicos
  const getChannelFlagOverride = (channelName: string): string | null => {
    const overrides: Record<string, string> = {
      '禁じられた物語': '🇯🇵',
      '古代の物語': '🇯🇵',
    };
    return overrides[channelName] || null;
  };

  const getLanguageFlag = (lingua: string | null | undefined, channelName?: string): string => {
    // Verificar override específico do canal primeiro
    if (channelName) {
      const override = getChannelFlagOverride(channelName);
      if (override) return override;
    }
    
    if (!lingua) return '';
    const normalized = lingua.toLowerCase().trim();
    const flagMap: Record<string, string> = {
      'portuguese': '🇧🇷',
      'português': '🇧🇷',
      'portugues': '🇧🇷',
      'english': '🇺🇸',
      'ingles': '🇺🇸',
      'inglês': '🇺🇸',
      'spanish': '🇪🇸',
      'espanhol': '🇪🇸',
      'german': '🇩🇪',
      'alemão': '🇩🇪',
      'alemao': '🇩🇪',
      'french': '🇫🇷',
      'francês': '🇫🇷',
      'frances': '🇫🇷',
      'italian': '🇮🇹',
      'italiano': '🇮🇹',
      'russian': '🇷🇺',
      'russo': '🇷🇺',
      'polish': '🇵🇱',
      'polonês': '🇵🇱',
      'polones': '🇵🇱',
      'turkish': '🇹🇷',
      'turco': '🇹🇷',
      'korean': '🇰🇷',
      'coreano': '🇰🇷',
      'ko': '🇰🇷',
      'arabic': '🇸🇦',
      'árabe': '🇸🇦',
      'arabe': '🇸🇦',
      'ar': '🇸🇦',
      'japanese': '🇯🇵',
      'japones': '🇯🇵',
      'japonês': '🇯🇵',
      'ja': '🇯🇵',
      'n/a': '',
    };
    return flagMap[normalized] || '🌐';
  };

  // Subnicho Card Component
  const SubnichoCard: React.FC<{
    subnicho: string;
    canais: Channel[];
    formatNumber: (num: number) => string;
    getGrowthIcon: (diff: number | null) => React.ReactNode;
    getGrowthColor: (diff: number | null) => string;
    formatGrowth: (diff: number | null) => string;
    openYouTube: (url: string) => void;
    getSubnichoEmoji: (subnicho: string) => string;
    getLanguageFlag: (lingua: string | null | undefined, channelName?: string) => string;
    animationDelay?: number;
  }> = ({
    subnicho,
    canais,
    formatNumber,
    getGrowthIcon,
    getGrowthColor,
    formatGrowth,
    openYouTube,
    getSubnichoEmoji,
    getLanguageFlag,
    animationDelay = 0,
  }) => {
    const [collapsed, setCollapsed] = useState(true);
    const cores = obterCorSubnicho(subnicho);
    const color = cores.fundo;
    const hasGradient = 'gradient' in cores && cores.gradient;

    return (
      <Card 
        className="overflow-hidden bg-card border-border opacity-0 animate-fade-in-up"
        style={{ animationDelay: `${animationDelay}ms` }}
      >
        <CardHeader
          className="border-b-2 p-3 sm:p-6 cursor-pointer"
          style={{
            background: hasGradient ? (cores as any).gradient : `${color}40`,
            borderBottomColor: color,
          }}
          onClick={() => setCollapsed(!collapsed)}
        >
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="text-base sm:text-xl flex-shrink-0">{getSubnichoEmoji(subnicho)}</span>
            <CardTitle className="text-base sm:text-xl truncate">{subnicho}</CardTitle>
                <Badge
                  variant="secondary"
                  className="ml-auto text-xs border font-semibold"
                  style={{
                    backgroundColor: `${color}40`,
                    color: 'white',
                    borderColor: color,
                  }}
                >
                  {canais.length}
                </Badge>
            <span className="text-muted-foreground">
              {collapsed ? '▼' : '▲'}
            </span>
          </div>
        </CardHeader>
        {!collapsed && (
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {canais.map((canal, index) => (
                <div
                  key={canal.id}
                  className="p-3 sm:p-4 flex items-center justify-between hover:bg-muted/50 transition-colors gap-2 sm:gap-4"
                >
                  <div
                    className="w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold flex-shrink-0"
                    style={{
                      backgroundColor: `${color}20`,
                      color: color,
                      border: `2px solid ${color}`,
                    }}
                  >
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate text-sm sm:text-base text-foreground flex items-center gap-1">
                      <span>{getLanguageFlag(canal.lingua, canal.nome_canal)}</span>
                      <span className="truncate">{canal.nome_canal}</span>
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5 sm:mt-1">
                      👥{formatNumber(canal.inscritos ?? 0)}
                    </div>
                  </div>
                  <div
                    className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-md min-w-[60px] sm:min-w-[80px] justify-center"
                    style={{
                      backgroundColor:
                        canal.inscritos_diff === null || canal.inscritos_diff === 0
                          ? 'hsl(var(--muted))'
                          : canal.inscritos_diff > 0
                          ? 'hsl(142.1 76.2% 36.3% / 0.15)'
                          : 'hsl(0 84.2% 60.2% / 0.15)',
                    }}
                  >
                    <span className="hidden sm:inline">{getGrowthIcon(canal.inscritos_diff)}</span>
                    <span className={`text-xs sm:text-sm ${getGrowthColor(canal.inscritos_diff)}`}>
                      {formatGrowth(canal.inscritos_diff)}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openYouTube(canal.url_canal);
                    }}
                    className="w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center flex-shrink-0 text-lg hover:scale-110 transition-transform"
                    title="Abrir canal no YouTube"
                  >
                    ▶️
                  </button>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>
    );
  };

  const sortedGrupos = Object.entries(grupos)
    .filter(([subnicho]) => {
      const normalized = normalizeString(subnicho);
      return !EXCLUDED_SUBNICHES.includes(normalized);
    })
    .sort(([a], [b]) => {
      const normalizedA = normalizeString(a);
      const normalizedB = normalizeString(b);
      
      // Desmonetizado sempre por último
      const aIsLast = LAST_SUBNICHE.includes(normalizedA);
      const bIsLast = LAST_SUBNICHE.includes(normalizedB);
      if (aIsLast && !bIsLast) return 1;
      if (!aIsLast && bIsLast) return -1;
      if (aIsLast && bIsLast) return 0;
      
      const indexA = SUBNICHE_ORDER.findIndex(s => normalizeString(s) === normalizedA);
      const indexB = SUBNICHE_ORDER.findIndex(s => normalizeString(s) === normalizedB);
      // Se não estiver na lista, vai pro final (mas antes de desmonetizado)
      if (indexA === -1 && indexB === -1) return 0;
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    });

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="bg-card border-border animate-fade-in">
          <CardHeader className="p-3 sm:p-6">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base sm:text-2xl flex items-center gap-2">
                <TableIcon className="h-5 w-5 text-orange-500" />
                Nossos Canais
              </CardTitle>
              <div className="flex items-center gap-1.5">
                <div className="h-5 w-16 bg-muted rounded animate-shimmer bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%]" />
                <div className="h-5 w-20 bg-muted rounded animate-shimmer bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%]" />
              </div>
            </div>
          </CardHeader>
        </Card>
        {[0, 1, 2, 3, 4].map((i) => (
          <SkeletonSubnichoCard 
            key={i} 
            className="opacity-0 animate-fade-in-up" 
            style={{ animationDelay: `${i * 80}ms` }} 
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card className="bg-card border-border">
          <CardHeader>
              <CardTitle className="text-base sm:text-2xl flex items-center gap-2">
                <TableIcon className="h-5 w-5 text-orange-500" />
                Nossos Canais
              </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center p-12 space-y-4">
              <p className="text-destructive text-center">{error.message}</p>
              <Button onClick={() => refetch()} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Tentar Novamente
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Calculate filtered totals
  const filteredTotalCanais = sortedGrupos.reduce((acc, [, canais]) => acc + canais.length, 0);
  const filteredTotalSubnichos = sortedGrupos.length;

    return (
      <div className="space-y-6">
        {/* Header com estatísticas */}
        <Card className="bg-card border-border">
          <CardHeader className="p-3 sm:p-6">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base sm:text-2xl flex items-center gap-2">
                <TableIcon className="h-5 w-5 text-orange-500" />
                Nossos Canais
              </CardTitle>
              <div className="flex items-center gap-1.5">
                <Badge variant="secondary" className="text-[10px] sm:text-xs">
                  {filteredTotalCanais} canais
                </Badge>
                <Badge variant="secondary" className="text-[10px] sm:text-xs">
                  {filteredTotalSubnichos} subnichos
                </Badge>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Grupos por subnicho */}
        {sortedGrupos.map(([subnicho, canais], index) => (
          <SubnichoCard
            key={subnicho}
            subnicho={subnicho}
            canais={canais}
            formatNumber={formatNumber}
            getGrowthIcon={getGrowthIcon}
            getGrowthColor={getGrowthColor}
            formatGrowth={formatGrowth}
            openYouTube={openYouTube}
            getSubnichoEmoji={getSubnichoEmoji}
            getLanguageFlag={getLanguageFlag}
            animationDelay={index * 60}
          />
        ))}

      {/* Mensagem se não houver canais */}
      {filteredTotalCanais === 0 && (
        <Card className="bg-card border-border">
          <CardContent className="p-12">
            <div className="text-center text-muted-foreground">
              <p>Nenhum canal encontrado.</p>
              <p className="text-sm mt-2">Adicione canais marcados como "nosso" para vê-los aqui.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
