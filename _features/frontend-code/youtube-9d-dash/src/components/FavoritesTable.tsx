import { useEffect, useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { formatNumber, formatGrowth, formatRelativeDate } from '@/utils/formatters';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { getLanguageFlag } from '@/utils/languageFlags';
import { ColoredBadge } from '@/components/ui/colored-badge';
import { useFavoriteAnimation } from '@/hooks/useFavoriteAnimation';
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, ExternalLink, Star, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

interface FavoritoCanal {
  id: number;
  nome_canal: string;
  lingua: string;
  subnicho?: string;
  nicho?: string;
  url_canal?: string;
  inscritos?: number;
  views_7d?: number;
  views_30d?: number;
}

export const FavoritesTable = React.memo(() => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { triggerAnimation, isAnimating } = useFavoriteAnimation();

  // Track collapsed state per subnicho - default all expanded
  const [collapsedSubnichos, setCollapsedSubnichos] = useState<Set<string>>(new Set());
  const [collapseInitialized, setCollapseInitialized] = useState(false);

  // ⚡ OTIMIZAÇÃO: staleTime para cache
  const { data: favoritosCanais, isLoading: loadingCanais } = useQuery({
    queryKey: ['favoritos-canais'],
    queryFn: apiService.getFavoritosCanais,
    staleTime: 2 * 60 * 1000,
  });

  // Mutation para remover favorito
  const removeFavoritoMutation = useMutation({
    mutationFn: ({ tipo, itemId }: { tipo: 'canal' | 'video', itemId: number }) =>
      apiService.removeFavorito(tipo, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['favoritos-canais'] });
      queryClient.invalidateQueries({ queryKey: ['favoritos-videos'] });
      toast({
        title: "Favorito removido",
        description: "Item removido dos favoritos com sucesso",
      });
    },
    onError: () => {
      toast({
        title: "Erro",
        description: "Não foi possível remover o favorito",
        variant: "destructive",
      });
    }
  });

  const handleRemoveFavorito = (tipo: 'canal' | 'video', itemId: number) => {
    triggerAnimation(itemId);
    removeFavoritoMutation.mutate({ tipo, itemId });
  };

  const toggleSubnicho = (subnicho: string) => {
    setCollapsedSubnichos(prev => {
      const newSet = new Set(prev);
      if (newSet.has(subnicho)) {
        newSet.delete(subnicho);
      } else {
        newSet.add(subnicho);
      }
      return newSet;
    });
  };

  // ⚡ Group by subnicho
  const groupedBySubnicho = useMemo(() => {
    const canais = favoritosCanais?.canais || [];
    const groups: Record<string, FavoritoCanal[]> = {};
    
    canais.forEach((canal: FavoritoCanal) => {
      const subnicho = canal.subnicho || canal.nicho || 'Sem Subnicho';
      if (!groups[subnicho]) {
        groups[subnicho] = [];
      }
      groups[subnicho].push(canal);
    });

    const normalizeStr = (s: string) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
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
    const LAST_SUBNICHE = ['desmonetizado', 'desmonetizados'];

    const sortedKeys = Object.keys(groups).sort((a, b) => {
      const na = normalizeStr(a);
      const nb = normalizeStr(b);

      const aIsLast = LAST_SUBNICHE.includes(na);
      const bIsLast = LAST_SUBNICHE.includes(nb);
      if (aIsLast && !bIsLast) return 1;
      if (!aIsLast && bIsLast) return -1;
      if (aIsLast && bIsLast) return 0;

      const ia = SUBNICHE_ORDER.findIndex(s => normalizeStr(s) === na);
      const ib = SUBNICHE_ORDER.findIndex(s => normalizeStr(s) === nb);
      if (ia === -1 && ib === -1) return 0;
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });

    return { groups, sortedKeys };
  }, [favoritosCanais]);

  // Default: leave all groups COLLAPSED when data loads
  useEffect(() => {
    if (collapseInitialized) return;
    if (groupedBySubnicho.sortedKeys.length === 0) return;

    setCollapsedSubnichos(new Set(groupedBySubnicho.sortedKeys));
    setCollapseInitialized(true);
  }, [collapseInitialized, groupedBySubnicho.sortedKeys]);

  const totalCanais = favoritosCanais?.canais?.length || 0;

  return (
    <div className="space-y-4">
      {loadingCanais ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-2 text-muted-foreground">Carregando canais favoritos...</span>
        </div>
      ) : totalCanais > 0 ? (
        <div className="space-y-3">
          {/* Header com total */}
          <div className="flex items-center justify-between px-2">
            <span className="text-sm text-muted-foreground">
              {totalCanais} {totalCanais === 1 ? 'canal favorito' : 'canais favoritos'} em {groupedBySubnicho.sortedKeys.length} {groupedBySubnicho.sortedKeys.length === 1 ? 'subnicho' : 'subnichos'}
            </span>
          </div>

          {/* Groups by subnicho */}
          {groupedBySubnicho.sortedKeys.map(subnicho => {
            const canais = groupedBySubnicho.groups[subnicho];
            const cores = obterCorSubnicho(subnicho);
            const emoji = getSubnichoEmoji(subnicho);
            const isCollapsed = collapsedSubnichos.has(subnicho);

            return (
              <Collapsible key={subnicho} open={!isCollapsed} onOpenChange={() => toggleSubnicho(subnicho)}>
                <div 
                  className="rounded-lg border overflow-hidden"
                  style={{ 
                    borderColor: cores.borda,
                    borderLeftWidth: '4px',
                    backgroundColor: cores.fundo + '15',
                  }}
                >
                  {/* Subnicho Header */}
                  <CollapsibleTrigger asChild>
                    <div 
                      className="flex items-center justify-between p-3 cursor-pointer hover:bg-accent/30 transition-colors"
                      style={{ backgroundColor: cores.fundo + '25' }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{emoji}</span>
                        <span className="font-semibold text-foreground">{subnicho}</span>
                        <Badge 
                          variant="secondary" 
                          className="text-xs"
                          style={{ backgroundColor: cores.fundo + '40', color: 'white' }}
                        >
                          {canais.length}
                        </Badge>
                      </div>
                      {isCollapsed ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    {/* DESKTOP: Table */}
                    <div className="hidden lg:block">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-table-header border-table-border hover:bg-table-header">
                            <TableHead className="w-8"></TableHead>
                            <TableHead className="text-foreground font-semibold">Canal</TableHead>
                            <TableHead className="text-foreground font-semibold">Língua</TableHead>
                            <TableHead className="text-foreground font-semibold text-right">Inscritos</TableHead>
                            <TableHead className="text-foreground font-semibold text-right">Views 7d</TableHead>
                            <TableHead className="text-foreground font-semibold text-right">Views 30d</TableHead>
                            <TableHead className="text-foreground font-semibold text-center">Ações</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {canais.map((canal) => (
                            <TableRow 
                              key={canal.id} 
                              className="border-table-border hover:bg-table-hover transition-colors"
                            >
                              <TableCell className="py-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="p-0 h-7 w-7"
                                  onClick={() => handleRemoveFavorito('canal', canal.id)}
                                  disabled={removeFavoritoMutation.isPending}
                                >
                                  <Star 
                                    className={`h-3.5 w-3.5 fill-yellow-500 text-yellow-500 ${
                                      isAnimating(canal.id) ? 'animate-favorite' : ''
                                    }`}
                                  />
                                </Button>
                              </TableCell>
                              <TableCell className="font-medium text-foreground">
                                <div className="flex items-center gap-2">
                                  <span>{getLanguageFlag(canal.lingua)}</span>
                                  <span>{canal.nome_canal}</span>
                                </div>
                              </TableCell>
                              <TableCell>
                                <ColoredBadge text={canal.lingua} type="language" />
                              </TableCell>
                              <TableCell className="text-right text-foreground">
                                {formatNumber(canal.inscritos || 0)}
                              </TableCell>
                              <TableCell className="text-right text-foreground">
                                {formatNumber(canal.views_7d || 0)}
                              </TableCell>
                              <TableCell className="text-right text-foreground">
                                {formatNumber(canal.views_30d || 0)}
                              </TableCell>
                              <TableCell className="text-center">
                                <div className="flex items-center justify-center gap-2">
                                  {canal.url_canal && (
                                    <Button
                                      asChild
                                      variant="ghost"
                                      size="sm"
                                      className="p-1 h-auto"
                                    >
                                      <a
                                        href={canal.url_canal}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        aria-label={`Abrir canal no YouTube: ${canal.nome_canal}`}
                                      >
                                        <ExternalLink className="h-4 w-4 text-primary" />
                                      </a>
                                    </Button>
                                  )}
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="p-1 h-auto"
                                    onClick={() => handleRemoveFavorito('canal', canal.id)}
                                    disabled={removeFavoritoMutation.isPending}
                                  >
                                    <Trash2 className="h-4 w-4 text-red-500" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>

                    {/* MOBILE: Cards */}
                    <div className="lg:hidden space-y-2 p-2">
                      {canais.map((canal) => (
                        <div
                          key={canal.id}
                          className="border rounded-lg p-3 space-y-2 bg-card/50"
                        >
                          {/* Header com Nome e Estrela */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <span className="text-lg flex-shrink-0">{getLanguageFlag(canal.lingua)}</span>
                              <h3 className="text-base font-bold text-foreground leading-tight break-words">
                                {canal.nome_canal}
                              </h3>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-0 h-7 w-7 flex-shrink-0"
                              onClick={() => handleRemoveFavorito('canal', canal.id)}
                              disabled={removeFavoritoMutation.isPending}
                            >
                              <Star 
                                className={`h-5 w-5 fill-yellow-500 text-yellow-500 ${
                                  isAnimating(canal.id) ? 'animate-favorite' : ''
                                }`}
                              />
                            </Button>
                          </div>

                          {/* Métricas Inline */}
                          <div className="flex items-center gap-3 text-xs text-foreground pt-1">
                            <span>👥 {formatNumber(canal.inscritos || 0)}</span>
                            <span>📊 7d: {formatNumber(canal.views_7d || 0)}</span>
                            <span>📈 30d: {formatNumber(canal.views_30d || 0)}</span>
                          </div>

                          {/* Botão de Ação */}
                          {canal.url_canal && (
                            <Button
                              asChild
                              className="w-full h-10 mt-2 text-sm"
                            >
                              <a
                                href={canal.url_canal}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <ExternalLink className="h-4 w-4 mr-2" />
                                Ver Canal
                              </a>
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12 bg-dashboard-card rounded-lg border border-dashboard-border">
          <Star className="h-12 w-12 text-yellow-500 mx-auto mb-4 opacity-50" />
          <p className="text-muted-foreground text-lg mb-2">Nenhum canal favoritado</p>
          <p className="text-sm text-muted-foreground">
            Clique na estrela nos canais para adicioná-los aos favoritos
          </p>
        </div>
      )}
    </div>
  );
});