import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react';

// Cores dos subnichos (mesmas do SubnicheTrendsCard)
const SUBNICHE_COLORS: Record<string, string> = {
  'Contos Familiares': '#F97316',
  'Terror': '#DC2626',
  'Histórias Sombrias': '#7C3AED',
  'Histórias Aleatórias': '#DB2777',
  'Relatos de Guerra': '#059669',
  'Stickman': '#2563EB',
  'Antiguidade': '#D97706',
  'Histórias Motivacionais': '#65A30D',
  'Mistérios': '#4F46E5',
  'Pessoas Desaparecidas': '#0284C7',
  'Psicologia & Mindset': '#0D9488',
  'Guerras e Civilizações': '#10B981',
};

interface Canal {
  id: number;
  nome_canal: string;
  url_canal: string;
  inscritos: number;
  inscritos_diff: number | null;
  ultima_coleta: string;
  subnicho: string;
}

interface GruposData {
  [subnicho: string]: Canal[];
}

interface TabelaResponse {
  grupos: GruposData;
  total_canais: number;
  total_subnichos: number;
}

export function TabelaCanais() {
  const [grupos, setGrupos] = useState<GruposData>({});
  const [totalCanais, setTotalCanais] = useState(0);
  const [totalSubnichos, setTotalSubnichos] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCanais();
  }, []);

  const fetchCanais = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('https://youtube-dashboard-backend-production.up.railway.app/api/canais-tabela');

      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }

      const data: TabelaResponse = await response.json();

      if (!data.grupos) {
        throw new Error('Formato de resposta inválido');
      }

      setGrupos(data.grupos);
      setTotalCanais(data.total_canais);
      setTotalSubnichos(data.total_subnichos);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar canais');
      console.error('Erro ao buscar canais:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number): string => {
    return num.toLocaleString('pt-BR');
  };

  const getGrowthIcon = (diff: number | null) => {
    if (diff === null || diff === 0) {
      return <Minus className="h-4 w-4 text-gray-500" />;
    }
    if (diff > 0) {
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    }
    return <TrendingDown className="h-4 w-4 text-red-600" />;
  };

  const getGrowthColor = (diff: number | null): string => {
    if (diff === null || diff === 0) return 'text-gray-600';
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

  if (loading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 Nossos Canais
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center p-12">
              <div className="text-center space-y-3">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-primary" />
                <p className="text-sm text-muted-foreground">Carregando canais...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 Nossos Canais
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center p-12 space-y-4">
              <p className="text-red-500 text-center">{error}</p>
              <Button onClick={fetchCanais} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Tentar Novamente
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header com estatísticas */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <CardTitle className="text-2xl">📊 Nossos Canais</CardTitle>
              <div className="flex gap-2">
                <Badge variant="secondary" className="text-sm">
                  {totalCanais} canais
                </Badge>
                <Badge variant="outline" className="text-sm">
                  {totalSubnichos} subnichos
                </Badge>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={fetchCanais}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Atualizar
            </Button>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Ganho de inscritos: ontem → hoje · Ordenado por desempenho
          </p>
        </CardHeader>
      </Card>

      {/* Grupos por subnicho */}
      {Object.entries(grupos).map(([subnicho, canais]) => {
        const color = SUBNICHE_COLORS[subnicho] || '#6B7280';

        return (
          <Card key={subnicho} className="overflow-hidden">
            <CardHeader
              className="border-b-2"
              style={{
                backgroundColor: `${color}15`,
                borderBottomColor: color,
              }}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-5 h-5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: color }}
                />
                <CardTitle className="text-xl">{subnicho}</CardTitle>
                <Badge
                  variant="secondary"
                  className="ml-auto"
                  style={{
                    backgroundColor: `${color}25`,
                    color: color,
                    borderColor: color,
                  }}
                >
                  {canais.length} {canais.length === 1 ? 'canal' : 'canais'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {canais.map((canal, index) => (
                  <div
                    key={canal.id}
                    className="p-4 flex items-center justify-between hover:bg-muted/50 transition-colors gap-4"
                  >
                    {/* Badge de posição (top 3) */}
                    {index < 3 && (
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                        style={{
                          backgroundColor: `${color}20`,
                          color: color,
                          border: `2px solid ${color}`,
                        }}
                      >
                        {index + 1}
                      </div>
                    )}

                    {index >= 3 && (
                      <div className="w-8 h-8 flex items-center justify-center text-xs text-muted-foreground flex-shrink-0">
                        {index + 1}
                      </div>
                    )}

                    {/* Nome do canal e inscritos */}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate text-base">
                        {canal.nome_canal}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {formatNumber(canal.inscritos)} inscritos
                      </div>
                    </div>

                    {/* Ganho de inscritos */}
                    <div
                      className="flex items-center gap-2 px-3 py-1.5 rounded-md min-w-[80px] justify-center"
                      style={{
                        backgroundColor:
                          canal.inscritos_diff === null || canal.inscritos_diff === 0
                            ? '#F3F4F6'
                            : canal.inscritos_diff > 0
                            ? '#DCFCE7'
                            : '#FEE2E2',
                      }}
                    >
                      {getGrowthIcon(canal.inscritos_diff)}
                      <span className={getGrowthColor(canal.inscritos_diff)}>
                        {formatGrowth(canal.inscritos_diff)}
                      </span>
                    </div>

                    {/* Botão acessar */}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openYouTube(canal.url_canal)}
                      className="gap-2 flex-shrink-0"
                      style={{
                        borderColor: `${color}50`,
                        color: color,
                      }}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Acessar
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        );
      })}

      {/* Mensagem se não houver canais */}
      {totalCanais === 0 && (
        <Card>
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
