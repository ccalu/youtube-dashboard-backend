import { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, Channel } from '@/services/api';
import { formatNumber } from '@/utils/formatters';
import { ColoredBadge } from '@/components/ui/colored-badge';
import { useFavoriteAnimation } from '@/hooks/useFavoriteAnimation';
import { obterCorSubnicho, obterGradienteTranslucido } from '@/utils/subnichoColors';
import React from 'react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Loader2, ExternalLink, Star, Plus, Edit, Trash2, Search, ArrowUpDown, ArrowUp, ArrowDown, Home, ChevronDown, ChevronLeft, ChevronRight, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { AddEditCanalModal } from '@/components/AddEditCanalModal';
import { ConfirmDeleteDialog } from '@/components/ConfirmDeleteDialog';
import { ModalAnalytics } from '@/components/ModalAnalytics';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

export const OurChannelsTable = React.memo(() => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const { triggerAnimation, isAnimating } = useFavoriteAnimation();

  const [filters, setFilters] = useState({
    lingua: 'all',
    subnicho: 'all',
    minViews: ''
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<{
    key: keyof Channel;
    direction: 'asc' | 'desc';
  } | null>(null);

  const [isAddEditModalOpen, setIsAddEditModalOpen] = useState(false);
  const [selectedCanal, setSelectedCanal] = useState<Channel | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteType, setDeleteType] = useState<'deactivate' | 'permanent'>('deactivate');
  const [canalToDelete, setCanalToDelete] = useState<Channel | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);
  const [analyticsModalOpen, setAnalyticsModalOpen] = useState(false);
  const [selectedChannelForAnalytics, setSelectedChannelForAnalytics] = useState<Channel | null>(null);

  // ⚡ OTIMIZAÇÃO: staleTime para cache
  const { data: channels, isLoading, error } = useQuery({
    queryKey: ['our-channels'],
    queryFn: () => apiService.getOurChannels(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: filterOptions } = useQuery({
    queryKey: ['filter-options'],
    queryFn: apiService.getFilterOptions,
    staleTime: 10 * 60 * 1000,
  });

  const { data: favoritosCanais } = useQuery({
    queryKey: ['favoritos-canais'],
    queryFn: apiService.getFavoritosCanais,
    staleTime: 2 * 60 * 1000,
  });

  const favoritosIds = useMemo(() => 
    new Set(favoritosCanais?.canais?.map(c => c.id) || []),
    [favoritosCanais]
  );

  const addFavoritoMutation = useMutation({
    mutationFn: (canalId: number) => apiService.addFavorito('canal', canalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['favoritos-canais'] });
      toast({
        title: "Adicionado aos favoritos",
        description: "Canal adicionado aos favoritos com sucesso",
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

  const removeFavoritoMutation = useMutation({
    mutationFn: (canalId: number) => apiService.removeFavorito('canal', canalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['favoritos-canais'] });
      toast({
        title: "Removido dos favoritos",
        description: "Canal removido dos favoritos com sucesso",
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

  const handleToggleFavorito = useCallback((canalId: number, isFavorited: boolean) => {
    triggerAnimation(canalId);
    if (isFavorited) {
      removeFavoritoMutation.mutate(canalId);
    } else {
      addFavoritoMutation.mutate(canalId);
    }
  }, [triggerAnimation, removeFavoritoMutation, addFavoritoMutation]);

  const handleOpenAnalytics = useCallback((channel: Channel) => {
    setSelectedChannelForAnalytics(channel);
    setAnalyticsModalOpen(true);
  }, []);

  const deleteCanalMutation = useMutation({
    mutationFn: (data: { canalId: number; permanent: boolean }) =>
      data.permanent
        ? apiService.deleteCanal(data.canalId)
        : apiService.deactivateCanal(data.canalId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['our-channels'] });
      queryClient.invalidateQueries({ queryKey: ['filter-options'] });
      queryClient.invalidateQueries({ queryKey: ['kanban-structure'] });
      toast({
        title: variables.permanent ? 'Canal deletado' : 'Canal desativado',
        description: variables.permanent
          ? 'Canal deletado permanentemente com sucesso'
          : 'Canal desativado com sucesso',
      });
    },
    onError: () => {
      toast({
        title: 'Erro',
        description: 'Não foi possível completar a operação',
        variant: 'destructive',
      });
    },
  });

  const handleAddCanal = () => {
    setSelectedCanal(null);
    setIsAddEditModalOpen(true);
  };

  const handleEditCanal = (canal: Channel) => {
    setSelectedCanal(canal);
    setIsAddEditModalOpen(true);
  };

  const handleDeleteClick = (canal: Channel, permanent: boolean) => {
    setCanalToDelete(canal);
    setDeleteType(permanent ? 'permanent' : 'deactivate');
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (canalToDelete) {
      deleteCanalMutation.mutate({
        canalId: canalToDelete.id,
        permanent: deleteType === 'permanent',
      });
    }
    setDeleteDialogOpen(false);
    setCanalToDelete(null);
  };

  const handleModalSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['our-channels'] });
    queryClient.invalidateQueries({ queryKey: ['filter-options'] });
    toast({
      title: selectedCanal ? 'Canal atualizado' : 'Canal adicionado',
      description: selectedCanal
        ? 'Canal atualizado com sucesso'
        : 'Canal adicionado com sucesso',
    });
  };

  const handleSort = (key: keyof Channel) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (columnKey: keyof Channel) => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return <ArrowUpDown className="h-4 w-4 ml-1 opacity-40" />;
    }
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="h-4 w-4 ml-1" />
      : <ArrowDown className="h-4 w-4 ml-1" />;
  };

  // ⚡ OTIMIZAÇÃO: useMemo para filtros
  const filteredChannels = useMemo(() => {
    return (channels?.canais || []).filter(channel => {
      // MUDANÇA 5: Garantir que mostra apenas canais tipo="nosso"
      if (channel.tipo !== 'nosso') {
        return false;
      }
      if (filters.lingua !== 'all' && channel.lingua !== filters.lingua) {
        return false;
      }
      if (filters.subnicho !== 'all' && channel.subnicho !== filters.subnicho) {
        return false;
      }
      if (filters.minViews && channel.views_7d < Number(filters.minViews)) {
        return false;
      }
      if (searchTerm) {
        return channel.nome_canal.toLowerCase().includes(searchTerm.toLowerCase());
      }
      return true;
    });
  }, [channels, filters, searchTerm]);

  // Ordem fixa dos subnichos
  const SUBNICHE_ORDER_LIST = [
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
  const LAST_SUBNICHE_LIST = ['desmonetizado', 'desmonetizados'];
  const normalizeStr = (s: string) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();

  // ⚡ OTIMIZAÇÃO: useMemo para ordenação — default: agrupar por subnicho
  const sortedChannels = useMemo(() => {
    const list = sortConfig ? [...filteredChannels].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];
      
      if (aValue == null) return 1;
      if (bValue == null) return -1;
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortConfig.direction === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc'
          ? aValue - bValue
          : bValue - aValue;
      }
      
      return 0;
    }) : [...filteredChannels];

    // Quando não há ordenação manual, agrupar por subnicho na ordem da Tabela
    if (!sortConfig) {
      list.sort((a, b) => {
        const na = normalizeStr(a.subnicho || '');
        const nb = normalizeStr(b.subnicho || '');
        const aIsLast = LAST_SUBNICHE_LIST.includes(na);
        const bIsLast = LAST_SUBNICHE_LIST.includes(nb);
        if (aIsLast && !bIsLast) return 1;
        if (!aIsLast && bIsLast) return -1;
        const ia = SUBNICHE_ORDER_LIST.findIndex(s => normalizeStr(s) === na);
        const ib = SUBNICHE_ORDER_LIST.findIndex(s => normalizeStr(s) === nb);
        const orderA = ia >= 0 ? ia : SUBNICHE_ORDER_LIST.length;
        const orderB = ib >= 0 ? ib : SUBNICHE_ORDER_LIST.length;
        return orderA - orderB;
      });
    }

    return list;
  }, [filteredChannels, sortConfig]);

  // Pagination logic
  const totalPages = Math.ceil(sortedChannels.length / itemsPerPage);
  const paginatedChannels = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedChannels.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedChannels, currentPage, itemsPerPage]);

  // Reset to page 1 when filters change
  useMemo(() => {
    setCurrentPage(1);
  }, [filters, searchTerm]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Carregando nossos canais...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive">Erro ao carregar dados dos nossos canais</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header - Desktop */}
      <div className="hidden lg:flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Home className="h-6 w-6 text-green-600" />
          <h2 className="text-2xl font-semibold text-foreground">Nossos Canais ({sortedChannels.length})</h2>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleAddCanal} className="gap-2">
            <Plus className="h-4 w-4" />
            Adicionar Canal
          </Button>
        </div>
      </div>

      {/* Header - Mobile */}
      <div className="flex flex-col gap-3 mb-6 lg:hidden">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Home className="h-6 w-6 text-green-600" />
            <h2 className="text-xl font-semibold text-foreground">Nossos Canais ({sortedChannels.length})</h2>
          </div>
        </div>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          type="text"
          placeholder="Pesquisar..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 w-full bg-dashboard-card border-dashboard-border"
        />
        {searchTerm && (
          <p className="text-sm text-muted-foreground mt-2">
            {sortedChannels.length} {sortedChannels.length === 1 ? 'canal encontrado' : 'canais encontrados'}
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
                Views mínimas (7d)
              </label>
              <Input
                type="number"
                placeholder="Ex: 10000"
                value={filters.minViews}
                onChange={(e) => setFilters(prev => ({ ...prev, minViews: e.target.value }))}
                className="w-full bg-dashboard-card border-dashboard-border"
              />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>


      <div className="hidden lg:block rounded-lg border border-dashboard-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-table-header border-table-border hover:bg-table-header">
              <TableHead className="text-foreground font-semibold w-12"></TableHead>
              <TableHead 
                className="text-foreground font-semibold cursor-pointer hover:bg-table-hover"
                onClick={() => handleSort('nome_canal')}
              >
                <div className="flex items-center">
                  Canal
                  {getSortIcon('nome_canal')}
                </div>
              </TableHead>
              <TableHead 
                className="text-foreground font-semibold cursor-pointer hover:bg-table-hover"
                onClick={() => handleSort('subnicho')}
              >
                <div className="flex items-center">
                  Subnicho
                  {getSortIcon('subnicho')}
                </div>
              </TableHead>
              <TableHead 
                className="text-foreground font-semibold cursor-pointer hover:bg-table-hover"
                onClick={() => handleSort('lingua')}
              >
                <div className="flex items-center">
                  Língua
                  {getSortIcon('lingua')}
                </div>
              </TableHead>
              <TableHead 
                className="text-foreground font-semibold text-right cursor-pointer hover:bg-table-hover"
                onClick={() => handleSort('inscritos')}
              >
                <div className="flex items-center justify-end">
                  Inscritos
                  {getSortIcon('inscritos')}
                </div>
              </TableHead>
              <TableHead 
                className="text-foreground font-semibold text-right cursor-pointer hover:bg-table-hover"
                onClick={() => handleSort('views_7d')}
              >
                <div className="flex items-center justify-end">
                  Views 7d
                  {getSortIcon('views_7d')}
                </div>
              </TableHead>
              <TableHead 
                className="text-foreground font-semibold text-right cursor-pointer hover:bg-table-hover"
                onClick={() => handleSort('views_30d')}
              >
                <div className="flex items-center justify-end">
                  Views 30d
                  {getSortIcon('views_30d')}
                </div>
              </TableHead>
              <TableHead className="text-foreground font-semibold text-center">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedChannels.map((channel) => {
              const isFavorited = favoritosIds.has(channel.id);
              const cores = obterCorSubnicho(channel.subnicho);
              
              return (
                <TableRow 
                  key={channel.id} 
                  className="border-table-border hover:bg-table-hover transition-colors"
                  style={{ 
                    background: obterGradienteTranslucido(channel.subnicho),
                    borderLeft: `4px solid ${cores.borda}`
                  }}
                >
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-1 h-auto"
                      onClick={() => handleToggleFavorito(channel.id, isFavorited)}
                      disabled={addFavoritoMutation.isPending || removeFavoritoMutation.isPending}
                    >
                      <Star 
                        className={`h-5 w-5 transition-all ${isAnimating(channel.id) ? 'animate-favorite' : ''} ${
                          isFavorited 
                            ? 'fill-yellow-500 text-yellow-500' 
                            : 'text-yellow-500 hover:fill-yellow-500'
                        }`} 
                      />
                    </Button>
                  </TableCell>
                  <TableCell className="font-medium text-foreground">
                    {channel.nome_canal}
                  </TableCell>
                  <TableCell>
                    <ColoredBadge text={channel.subnicho.replace(' (Dark History)', '')} type="subnicho" />
                  </TableCell>
                  <TableCell>
                    <ColoredBadge text={channel.lingua} type="language" />
                  </TableCell>
                  <TableCell className="text-right text-foreground">
                    {formatNumber(channel.inscritos)}
                    {channel.inscritos_diff !== null && channel.inscritos_diff !== undefined && (
                      <span className={`ml-2 text-sm ${
                        channel.inscritos_diff > 0 
                          ? 'text-green-600' 
                          : channel.inscritos_diff < 0 
                            ? 'text-red-600' 
                            : 'text-gray-500'
                      }`}>
                        ({channel.inscritos_diff > 0 ? '+' : ''}{channel.inscritos_diff})
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right text-foreground">
                    {formatNumber(channel.views_7d)}
                  </TableCell>
                  <TableCell className="text-right text-foreground">
                    {formatNumber(channel.views_30d)}
                  </TableCell>
                  <TableCell className="text-center">
                    <div className="flex items-center justify-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="p-1 h-auto"
                        onClick={() => handleOpenAnalytics(channel)}
                        title="Analisar canal"
                      >
                        <BarChart3 className="h-4 w-4 text-blue-500" />
                      </Button>
                      {channel.url_canal && (
                        <Button
                          asChild
                          variant="ghost"
                          size="sm"
                          className="p-1 h-auto"
                        >
                          <a
                            href={channel.url_canal}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`Abrir canal no YouTube: ${channel.nome_canal}`}
                          >
                            <ExternalLink className="h-4 w-4 text-primary" />
                          </a>
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="p-1 h-auto"
                        onClick={() => handleEditCanal(channel)}
                      >
                        <Edit className="h-4 w-4 text-primary" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="p-1 h-auto"
                        onClick={() => handleDeleteClick(channel, true)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* MOBILE: Cards Otimizados */}
      <div className="lg:hidden space-y-3 pb-4">
        {paginatedChannels.map((channel) => {
          const isFavorited = favoritosIds.has(channel.id);
          const cores = obterCorSubnicho(channel.subnicho);
          
          return (
            <div
              key={channel.id}
              className="border rounded-lg p-4 space-y-3 overflow-hidden"
              style={{ 
                backgroundColor: cores.fundo + '25',
                borderColor: cores.borda,
                borderWidth: '1px'
              }}
            >
              {/* Cabeçalho com nome + favorito (mobile) */}
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-lg font-bold text-foreground leading-tight break-words">
                  {channel.nome_canal}
                </h3>
                <Button
                  variant="ghost"
                  size="icon"
                  className="p-1 h-8 w-8 -mr-1"
                  onClick={() => handleToggleFavorito(channel.id, isFavorited)}
                  disabled={addFavoritoMutation.isPending || removeFavoritoMutation.isPending}
                  aria-label={isFavorited ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
                >
                  <Star 
                    className={`h-5 w-5 ${isAnimating(channel.id) ? 'animate-favorite' : ''} ${
                      isFavorited 
                        ? 'fill-yellow-500 text-yellow-500' 
                        : 'text-yellow-500'
                    }`} 
                  />
                </Button>
              </div>

              
              <div className="flex gap-2 items-center mobile-subtitle">
                <ColoredBadge 
                  text={channel.subnicho.replace(' (Dark History)', '')} 
                  type="subnicho" 
                  className="text-[10px] px-1.5 py-0.5 leading-tight flex-shrink-0" 
                />
                <span className="text-muted-foreground">•</span>
                <ColoredBadge text={channel.lingua} type="language" className="text-[10px] px-1.5 py-0.5 leading-tight flex-shrink-0" />
              </div>

              
              <div className="space-y-2 pt-2 border-t border-dashboard-border">
                <div className="flex items-center text-sm text-foreground">
                  <span className="mr-2">👥</span>
                  <span className="font-normal">
                    {formatNumber(channel.inscritos)} inscritos
                    {channel.inscritos_diff !== null && channel.inscritos_diff !== undefined && (
                      <span className={`ml-2 text-xs ${
                        channel.inscritos_diff > 0 
                          ? 'text-green-600' 
                          : channel.inscritos_diff < 0 
                            ? 'text-red-600' 
                            : 'text-gray-500'
                      }`}>
                        ({channel.inscritos_diff > 0 ? '+' : ''}{channel.inscritos_diff})
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex items-center text-sm text-foreground">
                  <span className="mr-2">🎬</span>
                  <span className="font-normal">Views 7d: {formatNumber(channel.views_7d)}</span>
                </div>
                <div className="flex items-center text-sm text-foreground">
                  <span className="mr-2">🎬</span>
                  <span className="font-normal">Views 30d: {formatNumber(channel.views_30d)}</span>
                </div>
              </div>

              
              {channel.url_canal && (
                <Button
                  asChild
                  className="w-full h-12 mt-3 text-base bg-gradient-to-r from-red-600 to-red-800 hover:from-red-700 hover:to-red-900 text-white"
                >
                  <a
                    href={channel.url_canal}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="h-5 w-5 mr-2" />
                    Abrir Canal
                  </a>
                </Button>
              )}
            </div>
          );
        })}
      </div>

      {/* Pagination Controls */}
      {sortedChannels.length > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-dashboard-border">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Mostrando {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, sortedChannels.length)} de {sortedChannels.length}</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Por página:</span>
              <Select value={String(itemsPerPage)} onValueChange={(value) => { setItemsPerPage(Number(value)); setCurrentPage(1); }}>
                <SelectTrigger className="w-[70px] h-8 bg-dashboard-card border-dashboard-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-dashboard-card border-dashboard-border">
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                  <SelectItem value="100">100</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => { setCurrentPage(p => Math.max(1, p - 1)); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground min-w-[80px] text-center">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => { setCurrentPage(p => Math.min(totalPages, p + 1)); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {sortedChannels.length === 0 && (
        <div className="text-center py-8">
          <p className="text-muted-foreground">
            Nenhum canal nosso encontrado. Adicione canais com tipo="nosso" no backend.
          </p>
        </div>
      )}

      <AddEditCanalModal
        isOpen={isAddEditModalOpen}
        onClose={() => setIsAddEditModalOpen(false)}
        canal={selectedCanal}
        tipo="nosso"
        onSuccess={handleModalSuccess}
      />

      <ConfirmDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleConfirmDelete}
        title={
          deleteType === 'permanent'
            ? 'Deletar Canal Permanentemente?'
            : 'Desativar Canal?'
        }
        description={
          deleteType === 'permanent'
            ? 'TEM CERTEZA? Isso vai deletar o canal e TODOS os vídeos e dados relacionados. Esta ação é IRREVERSÍVEL!'
            : 'Tem certeza que deseja desativar este canal? Ele será mantido no banco de dados mas não aparecerá mais nas listagens.'
        }
        confirmText={deleteType === 'permanent' ? 'Deletar Permanentemente' : 'Desativar'}
        isDestructive={true}
      />

      <ModalAnalytics
        open={analyticsModalOpen}
        onOpenChange={setAnalyticsModalOpen}
        canal={selectedChannelForAnalytics}
      />
    </div>
  );
});