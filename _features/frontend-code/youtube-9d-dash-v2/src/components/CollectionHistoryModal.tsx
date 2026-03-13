import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock, CheckCircle, AlertTriangle, XCircle, Loader2, Trash2, Zap, ChevronDown, ChevronUp, Info, Key } from 'lucide-react';
import { API_BASE_URL } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { getSubnichoEmoji } from '@/utils/subnichoEmojis';
interface CollectionHistory {
  id: number;
  data_inicio: string;
  data_fim: string | null;
  status: string;
  canais_total: number;
  canais_sucesso: number;
  canais_erro: number;
  videos_coletados: number;
  duracao_segundos: number | null;
  mensagem_erro: string | null;
  requisicoes_usadas: number;
}

interface ChaveAPI {
  nome: string;
  disponivel: number;
  usado_hoje: number;
  porcentagem_uso: number;
}

interface CanalComErro {
  nome: string;
  subnicho: string;
  tipo: string;
  erro: string;
  lingua?: string;
  url_canal?: string;
}

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
  
  if (!lingua) return '🌐';
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
    'chinese': '🇨🇳',
    'chinês': '🇨🇳',
    'hindi': '🇮🇳',
    'n/a': '',
  };
  return flagMap[normalized] || '🌐';
};

interface CanaisComErro {
  total: number;
  lista: CanalComErro[];
}

interface QuotaInfo {
  total_diario: number;
  usado_hoje: number;
  disponivel: number;
  porcentagem_usada: number;
  chaves_ativas?: number;
  total_chaves?: number;
  chaves_esgotadas?: number;
  requests_por_chave?: Record<string, number>;
  proximo_reset_utc?: string;
  proximo_reset_local?: string;
  total_disponivel?: number;
  chaves?: ChaveAPI[];
  videos_coletados?: number;
}

interface HistoricoResponse {
  historico: CollectionHistory[];
  total: number;
  quota_info: QuotaInfo;
  canais_com_erro?: CanaisComErro;
}

interface CollectionHistoryModalProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export const CollectionHistoryModal = ({ open: externalOpen, onOpenChange }: CollectionHistoryModalProps = {}) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const [showKeyDetails, setShowKeyDetails] = useState(false);
  const [showErrosModal, setShowErrosModal] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const isControlled = externalOpen !== undefined;
  const open = isControlled ? externalOpen : internalOpen;
  const setOpen = isControlled ? onOpenChange! : setInternalOpen;

  const { data, isLoading } = useQuery({
    queryKey: ['coletas-historico'],
    queryFn: async () => {
      // Limpa coletas travadas em background (não bloqueia)
      fetch(`${API_BASE_URL}/api/coletas/cleanup`, { method: 'POST' }).catch(() => {});
      
      // Busca histórico
      const response = await fetch(`${API_BASE_URL}/api/coletas/historico?limit=20`);
      if (!response.ok) throw new Error('Failed to fetch history');
      return response.json() as Promise<HistoricoResponse>;
    },
    enabled: open,
    // Cache herdado do QueryClient global (4h ou até 5h Brasília)
    refetchInterval: open ? 10000 : false,
  });

  const historico = data?.historico;
  const quotaInfo = data?.quota_info;

  // Filtrar coletas das últimas 24 horas
  const historicoFiltrado = historico?.filter(coleta => {
    const dataInicio = new Date(coleta.data_inicio);
    const now = new Date();
    const diffInHours = (now.getTime() - dataInicio.getTime()) / (1000 * 60 * 60);
    return diffInHours <= 24;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sucesso':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'parcial':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'erro':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'sucesso':
        return 'Sucesso';
      case 'parcial':
        return 'Parcial';
      case 'erro':
        return 'Erro';
      default:
        return 'Em progresso';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sucesso':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'parcial':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300';
      case 'erro':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
    }
  };

  const getQuotaColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-red-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getKeyUsageColor = (requests: number) => {
    const percentage = (requests / 10000) * 100;
    if (percentage >= 80) return 'text-red-600 dark:text-red-400';
    if (percentage >= 50) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  const getKeyUsageBackground = (requests: number) => {
    const percentage = (requests / 10000) * 100;
    if (percentage >= 80) return 'bg-red-100 dark:bg-red-900/20';
    if (percentage >= 50) return 'bg-yellow-100 dark:bg-yellow-900/20';
    return 'bg-green-100 dark:bg-green-900/20';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString('pt-BR');
  };

  const handleDelete = async (coletaId: number) => {
    if (!confirm('Tem certeza que deseja deletar esta coleta?')) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/coletas/${coletaId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        toast({
          title: "Coleta deletada",
          description: "Registro removido do histórico",
        });
        queryClient.invalidateQueries({ queryKey: ['coletas-historico'] });
      } else {
        throw new Error('Failed to delete');
      }
    } catch (error) {
      toast({
        title: "Erro ao deletar",
        description: "Tente novamente mais tarde",
        variant: "destructive"
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {!isControlled && (
        <DialogTrigger asChild>
          <Button variant="outline" size="icon" className="relative hover-scale h-8 w-8 sm:h-10 sm:w-10">
            <Clock className="h-4 w-4 sm:h-5 sm:w-5" strokeWidth={2} />
          </Button>
        </DialogTrigger>
      )}
      <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] p-0 flex flex-col overflow-hidden">
        <DialogHeader className="p-4 sm:p-6 pb-3 sm:pb-4 border-b border-border/50 pr-20 sm:pr-24 shrink-0">
          <div className="flex items-center justify-between gap-4">
            <DialogTitle className="text-lg sm:text-xl font-bold">Histórico de Coletas</DialogTitle>
            <Button
              variant="outline"
              size="sm"
              className="text-xs px-3 shrink-0"
              onClick={async () => {
                try {
                  const response = await fetch(`${API_BASE_URL}/api/collect-data`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json'
                    }
                  });
                  
                  if (response.ok) {
                    toast({
                      title: "Coleta iniciada!",
                      description: "Aguarde 10-15 minutos. O histórico será atualizado automaticamente.",
                    });
                    setOpen(false);
                  } else {
                    const result = await response.json();
                    toast({
                      title: "Aviso",
                      description: result.message || "Aguarde antes de iniciar nova coleta",
                      variant: "destructive"
                    });
                  }
                } catch (error) {
                  toast({
                    title: "Erro ao iniciar coleta",
                    description: "Tente novamente mais tarde",
                    variant: "destructive"
                  });
                }
              }}
            >
              🔄 Coletar
            </Button>
          </div>
        </DialogHeader>

        {/* BARRA DE QUOTA DIÁRIA */}
        {quotaInfo && (
          <div className="px-3 sm:px-6 pb-3 sm:pb-4 shrink-0 overflow-y-auto max-h-[40vh] sm:max-h-none">
            <div className="bg-gradient-to-r from-purple-500/20 to-indigo-500/20 dark:from-purple-600/20 dark:to-indigo-600/20 border border-purple-300 dark:border-purple-700 rounded-lg p-3 sm:p-5">
              {/* Cabeçalho */}
              <div className="flex items-center justify-between mb-2 sm:mb-4">
                <div className="flex items-center gap-1.5 sm:gap-2">
                  <Zap className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-500 dark:text-yellow-400" />
                  <span className="font-bold text-sm sm:text-lg">Units de API Diárias</span>
                </div>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p>Cada chave tem 10.000 requests/dia. Reseta à meia-noite UTC (21:00 Horário de Brasília).</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              <div className="space-y-3 sm:space-y-5">
                {/* Barra de Progresso */}
                <div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 sm:h-6 overflow-hidden mb-1 sm:mb-2">
                    <div 
                      className={`h-full transition-all ${getQuotaColor((quotaInfo.usado_hoje / quotaInfo.total_diario) * 100)}`}
                      style={{ width: `${Math.min(100, (quotaInfo.usado_hoje / quotaInfo.total_diario) * 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs sm:text-sm text-muted-foreground">
                      {((quotaInfo.usado_hoje / quotaInfo.total_diario) * 100).toFixed(1)}% usado
                    </span>
                  </div>
                </div>

                {/* Informações abaixo da barra */}
                <div className="space-y-0.5 sm:space-y-1">
                  <div className="text-sm sm:text-base font-medium">
                    Disponível: <span className="font-bold">{(quotaInfo.total_diario - quotaInfo.usado_hoje)?.toLocaleString()} units</span>
                  </div>
                  <div className="text-xs sm:text-sm text-green-600 dark:text-green-400 font-medium">
                    ~{Math.floor((quotaInfo.total_diario - quotaInfo.usado_hoje) / 47000)} coletas completas possíveis por dia
                  </div>
                </div>

                {/* Card de Canais com Erro */}
                {data?.canais_com_erro?.total && data.canais_com_erro.total > 0 && (
                  <div 
                    onClick={() => setShowErrosModal(true)}
                    className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3 mb-3 cursor-pointer hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">⚠️</span>
                        <span className="font-medium text-red-700 dark:text-red-400">
                          {data.canais_com_erro.total} canais com erro
                        </span>
                      </div>
                      <span className="text-red-500 dark:text-red-400 text-sm">Ver detalhes →</span>
                    </div>
                  </div>
                )}

                {/* Grid de 5 Cards - 2 colunas mobile, 5 colunas desktop */}
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-2 sm:gap-3">
                  <div className="bg-card/60 backdrop-blur-sm border border-border/50 rounded-lg p-2 sm:p-4 text-center">
                    <div className="text-xl sm:text-3xl font-bold text-primary mb-0.5 sm:mb-1">{quotaInfo.total_chaves || 0}</div>
                    <div className="text-[10px] sm:text-xs text-muted-foreground leading-tight">Total Chaves</div>
                  </div>
                  <div className="bg-card/60 backdrop-blur-sm border border-border/50 rounded-lg p-2 sm:p-4 text-center">
                    <div className="text-xl sm:text-3xl font-bold text-green-600 dark:text-green-400 mb-0.5 sm:mb-1">{quotaInfo.chaves_ativas || 0}</div>
                    <div className="text-[10px] sm:text-xs text-muted-foreground leading-tight">Chaves Ativas</div>
                  </div>
                  <div className="bg-card/60 backdrop-blur-sm border border-border/50 rounded-lg p-2 sm:p-4 text-center">
                    <div className="text-xl sm:text-3xl font-bold text-red-600 dark:text-red-400 mb-0.5 sm:mb-1">{quotaInfo.chaves_esgotadas || 0}</div>
                    <div className="text-[10px] sm:text-xs text-muted-foreground leading-tight">Esgotadas Hoje</div>
                  </div>
                  <div className="bg-card/60 backdrop-blur-sm border border-border/50 rounded-lg p-2 sm:p-4 text-center">
                    <div className="text-xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400 mb-0.5 sm:mb-1">
                      {formatNumber(quotaInfo.videos_coletados || 0)}
                    </div>
                    <div className="text-[10px] sm:text-xs text-muted-foreground leading-tight flex items-center justify-center gap-1">
                      <span>🎬</span> Vídeos Coletados
                    </div>
                  </div>
                  <div className="bg-card/60 backdrop-blur-sm border border-border/50 rounded-lg p-2 sm:p-4 text-center">
                    <div className="text-sm sm:text-lg font-bold text-primary mb-0 sm:mb-0.5">
                      {quotaInfo.proximo_reset_local?.split(' ')[0] || '22/10/2025'}
                    </div>
                    <div className="text-sm sm:text-base font-semibold text-primary">
                      {quotaInfo.proximo_reset_local?.split(' ')[1] || '21:00'}
                    </div>
                    <div className="text-[10px] sm:text-xs text-muted-foreground leading-tight mt-0.5 sm:mt-1">Próximo Reset</div>
                  </div>
                </div>

                {/* Dropdown de Chaves API */}
                {quotaInfo.chaves && quotaInfo.chaves.length > 0 && (
                  <Collapsible open={showKeyDetails} onOpenChange={setShowKeyDetails}>
                    <CollapsibleTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full flex items-center justify-center gap-2">
                        <Key className="h-4 w-4" />
                        <span className="text-xs font-medium">
                          Uso por Chave API
                        </span>
                        {showKeyDetails ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="mt-3">
                      <div className="space-y-2">
                        {quotaInfo.chaves.map((chave) => (
                          <div 
                            key={chave.nome} 
                            className={`rounded-lg p-3 border ${getKeyUsageBackground(chave.usado_hoje)}`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Key className="h-4 w-4 text-purple-500" />
                                <span className="font-semibold text-sm">{chave.nome}</span>
                              </div>
                              <Badge 
                                variant={chave.disponivel > 0 ? "default" : "destructive"}
                                className="text-xs"
                              >
                                {chave.disponivel > 0 ? "Ativa" : "Esgotada"}
                              </Badge>
                            </div>
                            
                            <div className="space-y-2">
                              <div className="flex justify-between items-center text-xs">
                                <span className="text-muted-foreground">Usado hoje:</span>
                                <span className={`font-semibold ${getKeyUsageColor(chave.usado_hoje)}`}>
                                  {chave.usado_hoje.toLocaleString()} / 10.000
                                </span>
                              </div>
                              
                              {/* Barra de Progresso */}
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                                <div 
                                  className={`h-full transition-all ${
                                    chave.porcentagem_uso >= 80 
                                      ? 'bg-red-500' 
                                      : chave.porcentagem_uso >= 50 
                                      ? 'bg-yellow-500' 
                                      : 'bg-green-500'
                                  }`}
                                  style={{ width: `${chave.porcentagem_uso}%` }}
                                />
                              </div>
                              <div className="text-xs text-right text-muted-foreground">
                                {chave.porcentagem_uso.toFixed(1)}% usado
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                )}
              </div>
            </div>
          </div>
        )}
        
        <ScrollArea className="flex-1 min-h-0 px-3 sm:px-6 pb-4 sm:pb-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : !historicoFiltrado || historicoFiltrado.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              Nenhuma coleta nas últimas 24 horas
            </div>
          ) : (
            <div className="space-y-4">
              {historicoFiltrado.map((coleta) => (
                <div
                  key={coleta.id}
                  className="border rounded-lg p-3 bg-card"
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(coleta.status)}
                      <div>
                        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(coleta.status)}`}>
                            {getStatusText(coleta.status)}
                          </span>
                          <span className="text-xs sm:text-sm text-muted-foreground">
                            {formatDate(coleta.data_inicio)}
                          </span>
                        </div>
                        {coleta.duracao_segundos && (
                          <span className="text-xs text-muted-foreground block mt-1">
                            Duração: {formatDuration(coleta.duracao_segundos)}
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => handleDelete(coleta.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-sm">
                    <div className="bg-muted/50 rounded-lg p-2 text-center">
                      <div className="text-base sm:text-lg font-bold">{formatNumber(coleta.canais_total || 0)}</div>
                      <div className="text-xs text-muted-foreground">Canais</div>
                    </div>
                    <div className="bg-green-500/10 rounded-lg p-2 text-center">
                      <div className="text-base sm:text-lg font-bold text-green-600 dark:text-green-400">{formatNumber(coleta.canais_sucesso || 0)}</div>
                      <div className="text-xs text-muted-foreground">Sucesso</div>
                    </div>
                    <div className="bg-red-500/10 rounded-lg p-2 text-center">
                      <div className="text-base sm:text-lg font-bold text-red-600 dark:text-red-400">{formatNumber(coleta.canais_erro || 0)}</div>
                      <div className="text-xs text-muted-foreground">Erro</div>
                    </div>
                    <div className="bg-blue-500/10 rounded-lg p-2 text-center">
                      <div className="text-base sm:text-lg font-bold text-blue-600 dark:text-blue-400">{formatNumber(coleta.videos_coletados || 0)}</div>
                      <div className="text-xs text-muted-foreground">Vídeos</div>
                    </div>
                    <div className="bg-purple-500/10 rounded-lg p-2 text-center col-span-2 sm:col-span-1">
                      <div className="text-base sm:text-lg font-bold text-purple-600 dark:text-purple-400">{formatNumber(coleta.requisicoes_usadas || 0)}</div>
                      <div className="text-xs text-muted-foreground">Requests</div>
                    </div>
                  </div>

                  {coleta.mensagem_erro && (
                    <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
                      <strong>Erro:</strong> {coleta.mensagem_erro}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Modal de Erros */}
        {showErrosModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-card border border-border rounded-lg w-full max-w-md max-h-[80vh] overflow-hidden">
              <div className="flex justify-between items-center p-4 border-b border-border">
                <h3 className="text-lg font-bold text-red-600 dark:text-red-400">
                  ⚠️ Canais com Erro ({data?.canais_com_erro?.total})
                </h3>
                <button 
                  onClick={() => setShowErrosModal(false)}
                  className="text-muted-foreground hover:text-foreground text-xl"
                >
                  ✕
                </button>
              </div>
              <div className="p-4 overflow-y-auto max-h-[60vh] space-y-4">
                {(() => {
                  // Agrupar canais por subnicho
                  const canaisPorSubnicho = data?.canais_com_erro?.lista?.reduce((acc, canal) => {
                    const subnicho = canal.subnicho || 'Sem subnicho';
                    if (!acc[subnicho]) {
                      acc[subnicho] = [];
                    }
                    acc[subnicho].push(canal);
                    return acc;
                  }, {} as Record<string, typeof data.canais_com_erro.lista>);

                  // Ordenar subnichos alfabeticamente
                  const subnichosOrdenados = Object.keys(canaisPorSubnicho || {}).sort((a, b) => 
                    a.localeCompare(b, 'pt-BR')
                  );

                  return subnichosOrdenados.map((subnicho) => (
                    <div key={subnicho} className="space-y-2">
                      {/* Header do subnicho */}
                      <div className="flex items-center gap-2 sticky top-0 bg-card py-1 border-b border-border/50">
                        <span className="text-lg">{getSubnichoEmoji(subnicho)}</span>
                        <span className="font-semibold text-sm text-foreground">{subnicho}</span>
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                          {canaisPorSubnicho?.[subnicho]?.length || 0}
                        </Badge>
                      </div>
                      
                      {/* Lista de canais do subnicho */}
                      <div className="space-y-2 pl-2">
                        {canaisPorSubnicho?.[subnicho]?.map((canal, i) => (
                          <div key={i} className="border-l-4 border-red-400 pl-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-r flex items-start gap-3">
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-foreground flex items-center gap-1.5">
                                <span>{getLanguageFlag(canal.lingua, canal.nome)}</span>
                                <span className="truncate">{canal.nome}</span>
                              </div>
                              <div className="text-[10px] text-muted-foreground">
                                {canal.tipo}
                              </div>
                              <div className="text-sm text-red-600 dark:text-red-400 mt-1">
                                ❌ {canal.erro}
                              </div>
                            </div>
                            {canal.url_canal && (
                              <button
                                onClick={() => window.open(canal.url_canal, '_blank', 'noopener,noreferrer')}
                                className="w-9 h-9 flex items-center justify-center flex-shrink-0 text-lg hover:scale-110 transition-transform rounded-md hover:bg-red-100 dark:hover:bg-red-800/30"
                                title="Abrir canal no YouTube"
                              >
                                ▶️
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};