import { useState, useCallback, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Users,
  MessageSquare,
  Clock,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Play,
  Copy,
  Check,
  Loader2,
  ThumbsUp,
  ExternalLink,
  Sparkles,
  Search,
  X,
} from 'lucide-react';
import { apiService } from '@/services/api';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
import { formatNumber } from '@/utils/formatters';
import { useToast } from '@/hooks/use-toast';
import { useDebounce } from '@/hooks/useDebounce';
import { Skeleton, SkeletonSubnichoCard } from '@/components/ui/skeleton';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// ── Static constants (moved outside component to avoid re-creation) ──

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
const normalizeStr = (s: string) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();

// ── Date helpers ──

const getPublicationDate = (dateStr: string | null | undefined): Date | null => {
  if (!dateStr) return null;
  const match = dateStr.match(/^(\d{4}-\d{2}-\d{2})/);
  const ymd = match?.[1];
  if (!ymd) return null;
  const date = new Date(`${ymd}T12:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
};

const getPublicationTimeMs = (dateStr: string | null | undefined): number => {
  const date = getPublicationDate(dateStr);
  return date ? date.getTime() : Number.NEGATIVE_INFINITY;
};

const formatVideoDate = (dateStr: string | null | undefined): string => {
  const date = getPublicationDate(dateStr);
  if (!date) return '—';
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' });
};

// ── Flag helpers ──

const getChannelFlagOverride = (channelName: string): string | null => {
  const overrides: Record<string, string> = {
    '禁じられた物語': '🇯🇵',
    '古代の物語': '🇯🇵',
  };
  return overrides[channelName] || null;
};

const getLanguageFlag = (lingua: string | null | undefined, channelName?: string): string => {
  if (channelName) {
    const override = getChannelFlagOverride(channelName);
    if (override) return override;
  }
  if (!lingua) return '🌐';
  const normalized = lingua.toLowerCase().trim();
  const flagMap: Record<string, string> = {
    'portuguese': '🇧🇷', 'português': '🇧🇷', 'portugues': '🇧🇷',
    'english': '🇺🇸', 'ingles': '🇺🇸', 'inglês': '🇺🇸',
    'spanish': '🇪🇸', 'espanhol': '🇪🇸',
    'german': '🇩🇪', 'alemão': '🇩🇪', 'alemao': '🇩🇪',
    'french': '🇫🇷', 'francês': '🇫🇷', 'frances': '🇫🇷',
    'italian': '🇮🇹', 'italiano': '🇮🇹',
    'korean': '🇰🇷', 'coreano': '🇰🇷',
    'japanese': '🇯🇵', 'japones': '🇯🇵', 'japonês': '🇯🇵',
    'arabic': '🇸🇦', 'árabe': '🇸🇦', 'arabe': '🇸🇦',
    'russian': '🇷🇺', 'russo': '🇷🇺',
    'turkish': '🇹🇷', 'turco': '🇹🇷',
    'polish': '🇵🇱', 'polones': '🇵🇱', 'polonês': '🇵🇱', 'polonес': '🇵🇱',
    'chinese': '🇨🇳', 'chines': '🇨🇳', 'chinês': '🇨🇳',
    'hindi': '🇮🇳',
  };
  return flagMap[normalized] || '🌐';
};

// ── Component ──

export function CommentsTab() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // State
  const [expandedSubnichos, setExpandedSubnichos] = useState<Set<string>>(new Set());
  const [selectedChannel, setSelectedChannel] = useState<{id: number; name: string; lingua?: string} | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<{id: string; title: string} | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set());
  const [commentsTab, setCommentsTab] = useState<'pending' | 'responded'>('pending');
  const [generatingResponse, setGeneratingResponse] = useState<Record<string, boolean>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);

  // Queries
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['comments-summary'],
    queryFn: () => apiService.getCommentsSummary(),
    staleTime: 1000 * 60 * 60,
    gcTime: 1000 * 60 * 120,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });

  const { data: channels, isLoading: loadingChannels } = useQuery({
    queryKey: ['monetized-channels-comments'],
    queryFn: () => apiService.getMonetizedChannelsComments(),
    staleTime: 1000 * 60 * 60,
    gcTime: 1000 * 60 * 120,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });

  const { data: videos, isLoading: loadingVideos } = useQuery({
    queryKey: ['channel-videos-comments', selectedChannel?.id],
    queryFn: () => apiService.getVideosWithComments(selectedChannel!.id),
    enabled: !!selectedChannel,
    staleTime: 24 * 60 * 60 * 1000,
    gcTime: 25 * 60 * 60 * 1000,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    placeholderData: (previousData) => previousData,
  });

  const { data: commentsData, isLoading: loadingComments } = useQuery({
    queryKey: ['video-comments', selectedVideo?.id, currentPage],
    queryFn: () => apiService.getCommentsPaginated(selectedVideo!.id, currentPage),
    enabled: !!selectedVideo,
    staleTime: 1000 * 60 * 30,
    gcTime: 1000 * 60 * 60,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    placeholderData: (previousData) => previousData,
  });

  // ── Parte 3: Prefetch comments for first 3 videos when video list loads ──
  useEffect(() => {
    if (videos && videos.length > 0) {
      videos.slice(0, 3).forEach(video => {
        queryClient.prefetchQuery({
          queryKey: ['video-comments', video.video_id, 1],
          queryFn: () => apiService.getCommentsPaginated(video.video_id, 1),
          staleTime: 1000 * 60 * 30,
        });
      });
    }
  }, [videos, queryClient]);

  // Mutations (collectMutation removed - dead code)
  const markRespondedMutation = useMutation({
    mutationFn: (commentId: string) => apiService.markCommentAsResponded(commentId),
    onSuccess: () => {
      toast({ title: "Marcado como respondido", description: "Comentário movido para aba 'Respondidos'" });
      queryClient.invalidateQueries({ queryKey: ['video-comments'] });
      queryClient.invalidateQueries({ queryKey: ['comments-summary'] });
    },
    onError: () => {
      toast({ title: "Erro", description: "Não foi possível marcar o comentário", variant: "destructive" });
    },
  });

  const generateResponseMutation = useMutation({
    mutationFn: (commentId: string) => apiService.generateCommentResponse(commentId),
    onSuccess: () => {
      toast({ title: "Resposta gerada!", description: "Uma resposta personalizada foi criada para este comentário." });
      queryClient.invalidateQueries({ queryKey: ['video-comments'] });
    },
    onError: () => {
      toast({ title: "Erro ao gerar resposta", description: "Não foi possível gerar uma resposta. Tente novamente.", variant: "destructive" });
    },
  });

  // Handlers
  const toggleSubnicho = useCallback((subnicho: string) => {
    setExpandedSubnichos(prev => {
      const next = new Set(prev);
      if (next.has(subnicho)) next.delete(subnicho);
      else next.add(subnicho);
      return next;
    });
  }, []);

  const handleCopyResponse = useCallback(async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast({ title: "Copiado!", description: "Resposta copiada para a área de transferência" });
    setTimeout(() => setCopiedId(null), 2000);
  }, [toast]);

  const openVideoComments = useCallback((video: {id: string; title: string}) => {
    setSelectedVideo(video);
    setCurrentPage(1);
    setExpandedComments(new Set());
    setCommentsTab('pending');
    setSearchTerm('');
  }, []);

  const isPortugueseChannel = useCallback((lingua: string | null | undefined): boolean => {
    if (!lingua) return false;
    const normalized = lingua.toLowerCase().trim();
    return ['portuguese', 'português', 'portugues', 'pt', 'pt-br'].includes(normalized);
  }, []);

  const toggleCommentExpand = useCallback((commentId: string) => {
    setExpandedComments(prev => {
      const next = new Set(prev);
      if (next.has(commentId)) next.delete(commentId);
      else next.add(commentId);
      return next;
    });
  }, []);

  const truncateTitle = (title: string, maxWords: number = 6): string => {
    const words = title.split(' ');
    if (words.length <= maxWords) return title;
    return words.slice(0, maxWords).join(' ') + '...';
  };

  // Group channels by subnicho
  const groupedChannels = useMemo(() => {
    if (!channels || !Array.isArray(channels)) return null;
    
    const grouped = channels.reduce((acc, channel) => {
      const subnicho = channel.subnicho || 'Sem Subnicho';
      if (!acc[subnicho]) acc[subnicho] = [];
      acc[subnicho].push(channel);
      return acc;
    }, {} as Record<string, typeof channels>);
    
    Object.keys(grouped).forEach(subnicho => {
      grouped[subnicho]?.sort((a, b) => b.total_comentarios - a.total_comentarios);
    });
    
    const sortedEntries = Object.entries(grouped).sort(([a], [b]) => {
      const na = normalizeStr(a);
      const nb = normalizeStr(b);
      const isLastA = LAST_SUBNICHE.includes(na);
      const isLastB = LAST_SUBNICHE.includes(nb);
      if (isLastA && !isLastB) return 1;
      if (!isLastA && isLastB) return -1;
      const idxA = SUBNICHE_ORDER.indexOf(na);
      const idxB = SUBNICHE_ORDER.indexOf(nb);
      const orderA = idxA >= 0 ? idxA : SUBNICHE_ORDER.length;
      const orderB = idxB >= 0 ? idxB : SUBNICHE_ORDER.length;
      return orderA - orderB;
    });

    return Object.fromEntries(sortedEntries);
  }, [channels]);

  // Process videos
  const processedVideos = useMemo(() => {
    if (!videos) return [];
    const videoMap = new Map<string, typeof videos[0]>();
    videos.forEach(video => {
      const existing = videoMap.get(video.video_id);
      if (!existing || video.views > existing.views) videoMap.set(video.video_id, video);
    });
    return Array.from(videoMap.values())
      .filter(video => video.total_comentarios > 0)
      .sort((a, b) => getPublicationTimeMs(b.data_publicacao) - getPublicationTimeMs(a.data_publicacao));
  }, [videos]);

  // Filter comments
  const filteredComments = useMemo(() => {
    if (!commentsData?.comments) return [];
    let comments = commentsData.comments.slice();
    if (debouncedSearch.trim()) {
      const searchLower = debouncedSearch.toLowerCase().trim();
      comments = comments.filter(c => 
        c.comment_text_original?.toLowerCase().includes(searchLower) ||
        c.comment_text_pt?.toLowerCase().includes(searchLower) ||
        c.author_name?.toLowerCase().includes(searchLower)
      );
    }
    if (commentsTab === 'pending') {
      return comments.filter(c => !c.is_responded).sort((a, b) => {
        const aHas = a.suggested_response ? 1 : 0;
        const bHas = b.suggested_response ? 1 : 0;
        return bHas - aHas;
      });
    }
    return comments.filter(c => c.is_responded);
  }, [commentsData?.comments, commentsTab, debouncedSearch]);

  const pendingCount = useMemo(() => commentsData?.comments?.filter(c => !c.is_responded).length || 0, [commentsData?.comments]);
  const respondedCount = useMemo(() => commentsData?.comments?.filter(c => c.is_responded).length || 0, [commentsData?.comments]);

  // ── Parte 1: Progressive rendering (NO global spinner) ──

  return (
    <div className="space-y-6">
      {/* Summary Cards - skeleton while loading */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {loadingSummary ? (
          <>
            <Skeleton className="h-[88px] rounded-lg" />
            <Skeleton className="h-[88px] rounded-lg" />
            <Skeleton className="h-[88px] rounded-lg" />
          </>
        ) : (
          <>
            <Card className="border-0" style={{ backgroundColor: '#3B82F65E' }}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-blue-200 mb-1">
                  <Users className="h-4 w-4" />
                  <span className="text-xs">Nossos Canais</span>
                </div>
                <p className="text-xl font-bold text-white">
                  {summary?.canais_monetizados || 0}
                </p>
              </CardContent>
            </Card>

            <Card className="border-0" style={{ backgroundColor: '#0596695E' }}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-green-200 mb-1">
                  <MessageSquare className="h-4 w-4" />
                  <span className="text-xs">Total de Comentários <span className="text-[10px] opacity-70">(30 dias)</span></span>
                </div>
                <p className="text-xl font-bold text-white">
                  {formatNumber(summary?.total_comentarios || 0)}
                </p>
              </CardContent>
            </Card>

            <Card className="border-0" style={{ backgroundColor: '#F59E0B5E' }}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 text-yellow-200 mb-1">
                  <Clock className="h-4 w-4" />
                  <span className="text-xs">Novos Hoje</span>
                </div>
                <p className="text-xl font-bold text-white">
                  {summary?.novos_hoje || 0}
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Channels List by Subnicho - skeleton while loading */}
      <Card className="border-0 bg-card/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-cyan-500" />
            Nossos Canais com Comentários
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loadingChannels ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <SkeletonSubnichoCard key={i} />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {groupedChannels && Object.entries(groupedChannels).map(([subnicho, subChannels]) => {
                const cores = obterCorSubnicho(subnicho);
                const isExpanded = expandedSubnichos.has(subnicho);
                const emoji = getSubnichoEmoji(subnicho);
                const totalComments = subChannels?.reduce((sum, ch) => sum + ch.total_comentarios, 0) || 0;

                return (
                  <Collapsible
                    key={subnicho}
                    open={isExpanded}
                    onOpenChange={() => toggleSubnicho(subnicho)}
                  >
                    <CollapsibleTrigger asChild>
                      <div
                        className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg cursor-pointer transition-all hover:scale-[1.01]"
                        style={{
                          backgroundColor: cores.fundo + '40',
                          borderLeft: `4px solid ${cores.borda}`,
                        }}
                      >
                        <div className="flex items-center gap-2">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-muted-foreground" />
                          )}
                          <span className="text-lg">{emoji}</span>
                          <span className="font-medium text-white">{subnicho}</span>
                          <Badge variant="secondary" className="ml-2">
                            {subChannels?.length || 0} canais
                          </Badge>
                        </div>
                        <Badge className="bg-cyan-600/50 text-cyan-100">
                          {formatNumber(totalComments)} comentários
                        </Badge>
                      </div>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent className="mt-1 space-y-1 pl-2 sm:pl-6">
                      {subChannels?.map((channel) => (
                        <div
                          key={channel.id}
                          className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-md bg-card/30 hover:bg-card/50 transition-colors"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-foreground flex items-center gap-1.5">
                              <span>{getLanguageFlag(channel.lingua, channel.nome_canal)}</span>
                              <span className="truncate">{channel.nome_canal}</span>
                            </p>
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground mt-1">
                              <span>{channel.total_videos} vídeos</span>
                              <span className="hidden sm:inline">•</span>
                              <span>{formatNumber(channel.total_comentarios)} comentários</span>
                              {channel.comentarios_sem_resposta > 0 && (
                                <>
                                  <span className="hidden sm:inline">•</span>
                                  <span className="text-yellow-400">
                                    {channel.comentarios_sem_resposta} sem resposta
                                  </span>
                                </>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center">
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full sm:w-auto text-xs"
                              onMouseEnter={() => {
                                queryClient.prefetchQuery({
                                  queryKey: ['channel-videos-comments', channel.id],
                                  queryFn: () => apiService.getVideosWithComments(channel.id),
                                  staleTime: 24 * 60 * 60 * 1000,
                                });
                              }}
                              onClick={() => setSelectedChannel({ id: channel.id, name: channel.nome_canal, lingua: channel.lingua })}
                            >
                              Ver Comentários
                            </Button>
                          </div>
                        </div>
                      ))}
                    </CollapsibleContent>
                  </Collapsible>
                );
              })}

              {(!groupedChannels || Object.keys(groupedChannels).length === 0) && (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>Nenhum canal monetizado encontrado</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Videos Modal */}
      <Dialog open={!!selectedChannel} onOpenChange={() => setSelectedChannel(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] w-[95vw] sm:w-full">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Play className="h-5 w-5 text-cyan-500" />
              Vídeos de {selectedChannel?.name}
            </DialogTitle>
            <DialogDescription className="sr-only">
              Lista de vídeos com comentários do canal {selectedChannel?.name}
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="h-[60vh]">
            {/* Parte 2: Skeleton for videos modal */}
            {loadingVideos && !videos ? (
              <div className="space-y-2 pr-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-card/50">
                    <Skeleton className="w-24 h-16 rounded flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-2 pr-4">
                {processedVideos.map((video) => (
                  <div
                    key={video.video_id}
                    className="flex items-start gap-3 p-3 rounded-lg bg-card/50 hover:bg-card/70 transition-colors cursor-pointer"
                    onClick={() => openVideoComments({ id: video.video_id, title: video.titulo })}
                  >
                    <div className="relative flex-shrink-0">
                      <img 
                        src={video.thumbnail || `https://i.ytimg.com/vi/${video.video_id}/mqdefault.jpg`}
                        alt={video.titulo}
                        className="w-16 h-10 sm:w-24 sm:h-16 object-cover rounded"
                        loading="lazy"
                      />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground">{truncateTitle(video.titulo, 6)}</p>
                      <div className="flex flex-wrap items-center gap-x-2 sm:gap-x-3 gap-y-0.5 text-xs text-muted-foreground mt-1">
                        <span className="text-cyan-400">
                          {formatVideoDate(video.data_publicacao)}
                        </span>
                        <span className="hidden sm:inline">•</span>
                        <span>{formatNumber(video.views)} views</span>
                        <span className="hidden sm:inline">•</span>
                        <span>{video.total_comentarios} coment.</span>
                        {video.comentarios_sem_resposta > 0 && (
                          <Badge variant="destructive" className="text-[10px] px-1.5">
                            {video.comentarios_sem_resposta} s/r
                          </Badge>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-3" />
                  </div>
                ))}

                {processedVideos.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Play className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Nenhum vídeo com comentários</p>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Comments Modal */}
      <Dialog open={!!selectedVideo} onOpenChange={() => setSelectedVideo(null)}>
        <DialogContent className="max-w-3xl max-h-[85vh] w-[95vw] sm:w-full">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-cyan-500" />
              <span className="truncate max-w-[500px]">{selectedVideo?.title}</span>
            </DialogTitle>
            <DialogDescription className="sr-only">
              Comentários do vídeo {selectedVideo?.title}
            </DialogDescription>
          </DialogHeader>
          
          {/* Search Input */}
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Buscar comentário, autor..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-8 h-9 bg-card/50 border-border/50"
            />
            {searchTerm && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
                onClick={() => setSearchTerm('')}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>

          <Tabs value={commentsTab} onValueChange={(v) => setCommentsTab(v as 'pending' | 'responded')} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-3">
              <TabsTrigger value="pending" className="flex items-center gap-2">
                <AlertCircle className="h-3.5 w-3.5" />
                Pendentes
                {pendingCount > 0 && (
                  <Badge variant="secondary" className="ml-1 text-[10px] px-1.5">
                    {pendingCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="responded" className="flex items-center gap-2">
                <Check className="h-3.5 w-3.5" />
                Respondidos
                {respondedCount > 0 && (
                  <Badge variant="secondary" className="ml-1 text-[10px] px-1.5">
                    {respondedCount}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>
            
            <ScrollArea className="h-[55vh]">
              {/* Parte 2: Skeleton for comments modal */}
              {loadingComments && !commentsData ? (
                <div className="space-y-3 pr-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="p-3 rounded-lg border border-border/50 bg-card/50 space-y-2">
                      <div className="flex items-center gap-2">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-3 w-16" />
                      </div>
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                      <div className="flex gap-2 mt-1">
                        <Skeleton className="h-6 w-20 rounded" />
                        <Skeleton className="h-6 w-20 rounded" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-3 pr-4">
                  {filteredComments.map((comment) => {
                    const isExpanded = expandedComments.has(comment.id);
                    const originalText = comment.comment_text_original || '';
                    const translatedText = comment.comment_text_pt || '';
                    const isLongOriginal = originalText.length > 150;
                    const isLongTranslation = translatedText.length > 150;
                    const showTranslation = !isPortugueseChannel(selectedChannel?.lingua) && 
                      translatedText && translatedText !== originalText;
                    
                    return (
                      <div
                        key={comment.id}
                        className={`p-3 rounded-lg border transition-colors ${
                          comment.suggested_response && !comment.is_responded
                            ? 'bg-cyan-900/20 border-cyan-600/40'
                            : comment.is_responded 
                              ? 'bg-green-900/20 border-green-600/30' 
                              : 'bg-card/50 border-border/50'
                        }`}
                      >
                        {/* Comment Header */}
                        <div className="flex flex-wrap items-center justify-between gap-1 mb-1.5">
                          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                            <span className="font-medium text-sm text-foreground">@{comment.author_name}</span>
                            <span className="text-[10px] text-muted-foreground">
                              {(() => {
                                try {
                                  if (!comment.published_at) return '';
                                  const dateStr = comment.published_at.includes('T') 
                                    ? comment.published_at 
                                    : comment.published_at + 'T12:00:00';
                                  const date = new Date(dateStr);
                                  if (isNaN(date.getTime())) return '';
                                  return formatDistanceToNow(date, { addSuffix: true, locale: ptBR });
                                } catch {
                                  return '';
                                }
                              })()}
                            </span>
                            {comment.like_count > 0 && (
                              <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                                <ThumbsUp className="h-2.5 w-2.5" />
                                {comment.like_count}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5">
                            {comment.suggested_response && !comment.is_responded && (
                              <Badge className="bg-cyan-600/50 text-cyan-100 text-[10px] px-1.5 py-0.5">
                                Resposta Sugerida
                              </Badge>
                            )}
                            {comment.is_responded && (
                              <Badge className="bg-green-600/50 text-green-100 text-[10px] px-1.5 py-0.5">
                                <Check className="h-2.5 w-2.5 mr-0.5" />
                                Respondido
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Comment Text */}
                        <div className="space-y-1.5 mb-2">
                          <p className={`text-sm text-foreground ${!isExpanded && isLongOriginal ? 'line-clamp-2' : ''}`}>
                            {originalText}
                          </p>
                          
                          {showTranslation && (
                            <p className={`text-xs text-muted-foreground italic border-l-2 border-cyan-500/50 pl-2 ${!isExpanded && isLongTranslation ? 'line-clamp-2' : ''}`}>
                              {translatedText}
                            </p>
                          )}
                          
                          {(isLongOriginal || (showTranslation && isLongTranslation)) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleCommentExpand(comment.id)}
                              className="text-[10px] h-5 px-1.5 text-cyan-400 hover:text-cyan-300"
                            >
                              {isExpanded ? 'Ver menos' : 'Ver mais...'}
                            </Button>
                          )}
                        </div>

                        {/* Action Buttons */}
                        <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                          {!comment.is_responded && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setGeneratingResponse(prev => ({ ...prev, [comment.id]: true }));
                                generateResponseMutation.mutate(comment.id, {
                                  onSettled: () => setGeneratingResponse(prev => ({ ...prev, [comment.id]: false }))
                                });
                              }}
                              disabled={generatingResponse[comment.id]}
                              className="text-[10px] h-6 px-2"
                            >
                              {generatingResponse[comment.id] ? (
                                <>
                                  <Loader2 className="h-2.5 w-2.5 mr-1 animate-spin" />
                                  Gerando...
                                </>
                              ) : comment.suggested_response ? (
                                <>
                                  <Sparkles className="h-2.5 w-2.5 mr-1 text-amber-500" />
                                  Regenerar
                                </>
                              ) : (
                                <>
                                  <Sparkles className="h-2.5 w-2.5 mr-1" />
                                  Gerar Resposta
                                </>
                              )}
                            </Button>
                          )}
                          
                          {!comment.is_responded && (
                            <Button
                              size="sm"
                              onClick={() => markRespondedMutation.mutate(comment.id)}
                              disabled={!comment.suggested_response || markRespondedMutation.isPending}
                              className="text-[10px] h-6 px-2 bg-green-600 hover:bg-green-700 disabled:opacity-50"
                            >
                              <Check className="h-2.5 w-2.5 mr-1" />
                              Respondido
                            </Button>
                          )}
                          
                          <Button
                            size="sm"
                            variant="ghost"
                            asChild
                            className="text-[10px] h-6 px-2"
                          >
                            <a
                              href={`https://www.youtube.com/watch?v=${selectedVideo?.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <ExternalLink className="h-2.5 w-2.5 mr-1" />
                              YouTube
                            </a>
                          </Button>
                        </div>

                        {/* Suggested Response Card */}
                        {comment.suggested_response && (
                          <div className="mt-2 p-2 rounded-md bg-blue-900/20 border border-blue-600/30">
                            <div className="flex items-start gap-2">
                              <Sparkles className="h-3.5 w-3.5 text-blue-400 mt-0.5 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <p className="text-[10px] font-medium text-blue-200 mb-1">Resposta Sugerida:</p>
                                <p className={`text-xs text-blue-100 ${!isExpanded ? 'line-clamp-2' : ''}`}>
                                  {comment.suggested_response}
                                </p>
                                
                                <div className="flex items-center gap-1.5 mt-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleCopyResponse(comment.suggested_response, comment.id)}
                                    className="text-[10px] h-5 px-1.5 border-blue-600/50 text-blue-200 hover:bg-blue-900/30"
                                  >
                                    {copiedId === comment.id ? (
                                      <Check className="h-2.5 w-2.5 mr-1" />
                                    ) : (
                                      <Copy className="h-2.5 w-2.5 mr-1" />
                                    )}
                                    Copiar
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {filteredComments.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>
                        {commentsTab === 'pending' 
                          ? 'Nenhum comentário pendente' 
                          : 'Nenhum comentário respondido'}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </ScrollArea>
          </Tabs>

          {/* Pagination */}
          {commentsData?.pagination && commentsData.pagination.total_pages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2 pt-4 border-t">
              <p className="text-xs sm:text-sm text-muted-foreground">
                Pág. {currentPage}/{commentsData.pagination.total_pages} ({commentsData.pagination.total})
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(commentsData.pagination.total_pages, p + 1))}
                  disabled={currentPage === commentsData.pagination.total_pages}
                >
                  Próxima
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
