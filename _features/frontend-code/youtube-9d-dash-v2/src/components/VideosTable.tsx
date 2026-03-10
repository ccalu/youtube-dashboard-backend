import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, Video } from '@/services/api';
import { formatNumber, formatRelativeDate } from '@/utils/formatters';
import { ColoredBadge } from '@/components/ui/colored-badge';
import { useFavoriteAnimation } from '@/hooks/useFavoriteAnimation';
import React from 'react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, ExternalLink, Eye, Star, Play, ChevronDown, ArrowUpDown, ArrowUp, ArrowDown, Search } from 'lucide-react';
import { DataRefreshButton } from '@/components/DataRefreshButton';
import { useToast } from '@/hooks/use-toast';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

export const VideosTable = React.memo(() => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { triggerAnimation, isAnimating } = useFavoriteAnimation();

  const [filters, setFilters] = useState({
    canal: 'all',
    lingua: 'all',
    subnicho: 'all',
    period: '30d',
    minViews: ''
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [sortConfig, setSortConfig] = useState<{
    key: 'titulo' | 'nome_canal' | 'data_publicacao' | 'views_atuais';
    direction: 'asc' | 'desc';
  } | null>({ key: 'data_publicacao', direction: 'desc' });

  // ⚡ OTIMIZAÇÃO: staleTime para cache
  const { data: videos, isLoading, error } = useQuery({
    queryKey: ['videos', { canal: filters.canal, lingua: filters.lingua, subnicho: filters.subnicho, period: filters.period, minViews: filters.minViews }],
    queryFn: () => apiService.getVideos({
      canal: filters.canal !== 'all' ? filters.canal : undefined,
      periodo_publicacao: filters.period as '7d' | '15d' | '30d' | '60d',
      lingua: filters.lingua !== 'all' ? filters.lingua : undefined,
      subnicho: filters.subnicho !== 'all' ? filters.subnicho : undefined,
    }),
    staleTime: 3 * 60 * 1000, // 3 minutos
  });

  const { data: filterOptions } = useQuery({
    queryKey: ['filter-options'],
    queryFn: apiService.getFilterOptions,
    staleTime: 10 * 60 * 1000,
  });

  const { data: favoritosVideos } = useQuery({
    queryKey: ['favoritos-videos'],
    queryFn: apiService.getFavoritosVideos,
    staleTime: 2 * 60 * 1000,
  });

  const handleSort = (key: 'titulo' | 'nome_canal' | 'data_publicacao' | 'views_atuais') => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (columnKey: 'titulo' | 'nome_canal' | 'data_publicacao' | 'views_atuais') => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return <ArrowUpDown className="h-4 w-4 ml-1 opacity-40" />;
    }
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="h-4 w-4 ml-1" />
      : <ArrowDown className="h-4 w-4 ml-1" />;
  };

  // ⚡ OTIMIZAÇÃO: useMemo para favoritosIds
  const favoritosIds = useMemo(() => 
    new Set(favoritosVideos?.videos?.map(v => Number(v.id)) || []),
    [favoritosVideos]
  );

  // Mutation para adicionar favorito
  const addFavoritoMutation = useMutation({
    mutationFn: (videoId: number) => apiService.addFavorito('video', videoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['favoritos-videos'] });
      toast({
        title: "Adicionado aos favoritos",
        description: "Vídeo adicionado aos favoritos com sucesso",
      });
    },
    onError: () => {
      toast({
        title: "Erro",
        description: "Não foi possível adicionar aos favoritos",
        variant: "destructive",
      });
    }
  });

  // Mutation para remover favorito
  const removeFavoritoMutation = useMutation({
    mutationFn: (videoId: number) => apiService.removeFavorito('video', videoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['favoritos-videos'] });
      toast({
        title: "Removido dos favoritos",
        description: "Vídeo removido dos favoritos com sucesso",
      });
    },
    onError: () => {
      toast({
        title: "Erro",
        description: "Não foi possível remover dos favoritos",
        variant: "destructive",
      });
    }
  });

  const handleToggleFavorito = (videoId: number, isFavorited: boolean) => {
    triggerAnimation(videoId); // MUDANÇA 8: Animação ao favoritar
    if (isFavorited) {
      removeFavoritoMutation.mutate(videoId);
    } else {
      addFavoritoMutation.mutate(videoId);
    }
  };

  // ⚡ OTIMIZAÇÃO: useMemo para ordenação - só recalcula quando necessário
  const filteredAndSortedVideos = useMemo(() => {
    // Filtro automático de views mínimas baseado no período
    const autoMinViews = filters.period === '60d' ? 30000 : 
                         filters.period === '30d' ? 10000 : 5000;
    
    // Filtro manual (se preenchido)
    const manualMinViews = filters.minViews ? parseInt(filters.minViews) : 0;
    
    // Usa o maior dos dois
    const finalMinViews = Math.max(autoMinViews, manualMinViews);
    
    // Aplica filtro de views
    let filtered = (videos?.videos || []).filter(video => 
      (video.views_atuais || 0) >= finalMinViews
    );
    
    // Aplica filtro de pesquisa (busca por título ou canal)
    if (searchTerm) {
      filtered = filtered.filter(video =>
        video.titulo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        video.nome_canal.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Aplica ordenação se sortConfig existe
    if (sortConfig) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];
        
        if (aValue == null) return 1;
        if (bValue == null) return -1;
        
        // Para datas, converter para timestamp
        if (sortConfig.key === 'data_publicacao') {
          const aTime = new Date(aValue).getTime();
          const bTime = new Date(bValue).getTime();
          return sortConfig.direction === 'asc' ? aTime - bTime : bTime - aTime;
        }
        
        // Para strings (título e canal)
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return sortConfig.direction === 'asc'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        }
        
        // Para números (views)
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        return 0;
      });
    }
    
    return filtered;
  }, [videos, sortConfig, filters.period, filters.minViews, searchTerm]);


  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Carregando vídeos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive">Erro ao carregar dados dos vídeos</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header - Desktop */}
      <div className="hidden lg:flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Play className="h-6 w-6 text-red-500" />
          <h2 className="text-2xl font-bold text-foreground">Vídeos</h2>
        </div>
      </div>

      {/* Header - Mobile */}
      <div className="flex flex-col gap-3 mb-6 lg:hidden">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Play className="h-6 w-6 text-red-500" />
            <h2 className="text-xl font-bold text-foreground">Vídeos</h2>
          </div>
          <DataRefreshButton />
        </div>
      </div>
      
      {/* Barra de Pesquisa */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          type="text"
          placeholder="Buscar por título ou canal..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 w-full bg-dashboard-card border-dashboard-border"
        />
        {searchTerm && (
          <p className="text-sm text-muted-foreground mt-2">
            {filteredAndSortedVideos.length} {filteredAndSortedVideos.length === 1 ? 'vídeo encontrado' : 'vídeos encontrados'}
          </p>
        )}
      </div>

      {/* Filtros */}
      <Collapsible open={filtersOpen} onOpenChange={setFiltersOpen} className="mb-6">
        <CollapsibleTrigger asChild>
          <Button variant="outline" className="w-full justify-between">
            <span>Filtros</span>
            <ChevronDown className={`h-4 w-4 transition-transform ${filtersOpen ? 'rotate-180' : ''}`} />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-4">
          <div className="grid grid-cols-1 gap-4 p-4 bg-table-header rounded-lg border border-dashboard-border">
            <div className="w-full">
              <label className="block text-sm font-medium text-foreground mb-2">
                Canal
              </label>
              <Select value={filters.canal} onValueChange={(value) => 
                setFilters(prev => ({ ...prev, canal: value }))
              }>
                <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                  <SelectItem value="all">Todos</SelectItem>
                  {filterOptions?.canais?.map(canal => (
                    <SelectItem key={canal} value={canal}>{canal}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-full">
              <label className="block text-sm font-medium text-foreground mb-2">
                Língua
              </label>
              <Select value={filters.lingua} onValueChange={(value) => 
                setFilters(prev => ({ ...prev, lingua: value }))
              }>
                <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                  <SelectItem value="all">Todos</SelectItem>
                  {filterOptions?.linguas?.map(lingua => (
                    <SelectItem key={lingua} value={lingua}>{lingua}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-full">
              <label className="block text-sm font-medium text-foreground mb-2">
                Subnicho
              </label>
              <Select value={filters.subnicho} onValueChange={(value) => 
                setFilters(prev => ({ ...prev, subnicho: value }))
              }>
                <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                  <SelectItem value="all">Todos</SelectItem>
                  {filterOptions?.subnichos?.map(subnicho => (
                    <SelectItem key={subnicho} value={subnicho}>{subnicho}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="w-full">
              <label className="block text-sm font-medium text-foreground mb-2">
                Período
              </label>
              <Select value={filters.period} onValueChange={(value) => 
                setFilters(prev => ({ ...prev, period: value }))
              }>
                <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                  <SelectItem value="7d">Últimos 7 dias</SelectItem>
                  <SelectItem value="15d">Últimos 15 dias</SelectItem>
                  <SelectItem value="30d">Últimos 30 dias</SelectItem>
                  <SelectItem value="60d">Últimos 60 dias</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="w-full">
              <label className="block text-sm font-medium text-foreground mb-2">
                Views mínimas
              </label>
              <Input
                type="number"
                placeholder="Ex: 1000"
                value={filters.minViews}
                onChange={(e) => setFilters(prev => ({ ...prev, minViews: e.target.value }))}
                className="w-full bg-dashboard-card border-dashboard-border"
              />
            </div>

          </div>
        </CollapsibleContent>
      </Collapsible>


      {/* DESKTOP: Table - MUDANÇA 11: Layout mais compacto */}
      <div className="hidden lg:block rounded-lg border border-dashboard-border overflow-hidden">
        <Table>
          <TableHeader className="hidden lg:table-header-group">
            <TableRow className="bg-table-header border-table-border hover:bg-table-header">
              <TableHead className="text-foreground font-semibold w-8"></TableHead>
              
              <TableHead 
                className="text-foreground font-semibold cursor-pointer hover:bg-table-hover w-[35%]"
                onClick={() => handleSort('titulo')}
              >
                <div className="flex items-center">
                  Título
                  {getSortIcon('titulo')}
                </div>
              </TableHead>
              
              <TableHead 
                className="text-foreground font-semibold cursor-pointer hover:bg-table-hover w-[20%]"
                onClick={() => handleSort('nome_canal')}
              >
                <div className="flex items-center">
                  Canal
                  {getSortIcon('nome_canal')}
                </div>
              </TableHead>
              
              <TableHead 
                className="text-foreground font-semibold text-right cursor-pointer hover:bg-table-hover w-[15%]"
                onClick={() => handleSort('views_atuais')}
              >
                <div className="flex items-center justify-end">
                  Views
                  {getSortIcon('views_atuais')}
                </div>
              </TableHead>
              
              <TableHead 
                className="text-foreground font-semibold text-right cursor-pointer hover:bg-table-hover w-[20%]"
                onClick={() => handleSort('data_publicacao')}
              >
                <div className="flex items-center justify-end">
                  Data
                  {getSortIcon('data_publicacao')}
                </div>
              </TableHead>
              
              <TableHead className="text-foreground font-semibold w-[10%]">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAndSortedVideos.map((video) => {
              const isFavorited = favoritosIds.has(Number(video.id));
              
              return (
                <TableRow 
                  key={video.id} 
                  className="border-table-border hover:bg-table-hover transition-colors"
                >
                  <TableCell className="w-8 py-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleToggleFavorito(Number(video.id), isFavorited)}
                      disabled={addFavoritoMutation.isPending || removeFavoritoMutation.isPending}
                      className="h-7 w-7"
                    >
                      <Star 
                        className={`h-3.5 w-3.5 ${isAnimating(Number(video.id)) ? 'animate-favorite' : ''} ${
                          isFavorited 
                            ? 'fill-yellow-500 text-yellow-500' 
                            : 'text-yellow-500'
                        }`} 
                      />
                    </Button>
                  </TableCell>
                  <TableCell className="font-medium py-2">
                    <span className="text-foreground line-clamp-2">
                      {video.titulo}
                    </span>
                  </TableCell>
                  <TableCell className="py-2">
                    <span className="text-foreground text-sm">{video.nome_canal}</span>
                  </TableCell>
                  <TableCell className="text-right py-2">
                    <div className="flex items-center justify-end space-x-1 text-foreground">
                      <Eye className="h-3 w-3 text-muted-foreground" />
                      <span className="text-sm">{formatNumber(video.views_atuais || 0)}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground text-sm py-2">
                    {formatRelativeDate(video.data_publicacao)}
                  </TableCell>
                  <TableCell className="py-2">
                    <div className="flex gap-1 justify-end">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => window.open(video.url_video || `https://www.youtube.com/watch?v=${video.video_id}`, '_blank')}
                        className="h-7 w-7"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* MOBILE/TABLET: Cards */}
      <div className="lg:hidden space-y-4 pb-4">
        {filteredAndSortedVideos.map((video) => {
          const isFavorited = favoritosIds.has(Number(video.id));
          
          return (
            <div
              key={video.id}
              className="bg-dashboard-card border border-dashboard-border rounded-lg p-4 space-y-4 overflow-hidden"
            >
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-foreground text-sm leading-tight mb-2 line-clamp-2 break-words">
                    {video.titulo}
                  </h3>
                  <Badge variant="outline" className="border-primary/30 text-foreground text-xs">
                    {video.nome_canal}
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0"
                  onClick={() => handleToggleFavorito(Number(video.id), isFavorited)}
                  disabled={addFavoritoMutation.isPending || removeFavoritoMutation.isPending}
                >
                  <Star 
                    className={`h-5 w-5 ${
                      isFavorited 
                        ? 'fill-yellow-500 text-yellow-500' 
                        : 'text-yellow-500'
                    }`} 
                  />
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="bg-muted/30 rounded-lg p-2.5">
                  <p className="text-xs text-muted-foreground mb-1 truncate">Views</p>
                  <div className="flex items-center text-sm font-bold text-foreground">
                    <Eye className="h-3 w-3 mr-1 shrink-0" />
                    <span className="truncate">{formatNumber(video.views_atuais || 0)}</span>
                  </div>
                </div>
                <div className="bg-muted/30 rounded-lg p-2.5">
                  <p className="text-xs text-muted-foreground mb-1 truncate">Publicado</p>
                  <p className="text-xs font-semibold text-foreground truncate">{formatRelativeDate(video.data_publicacao)}</p>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                className="w-full justify-center"
                onClick={() => window.open(video.url_video || `https://www.youtube.com/watch?v=${video.video_id}`, '_blank')}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Assistir
              </Button>
            </div>
          );
        })}
      </div>

      {filteredAndSortedVideos.length === 0 && (
        <div className="text-center py-8">
          <p className="text-muted-foreground">Nenhum vídeo encontrado com os filtros aplicados</p>
        </div>
      )}
    </div>
  );
});