// 🔧 CORREÇÃO APLICADA: Bug de notificações "sumindo" resolvido!
// PROBLEMA: Notificações de ontem (diffDays = 1) não apareciam em nenhum grupo
// SOLUÇÃO: Alterada linha 632 de "diffDays >= 2" para "diffDays >= 1"

import { useEffect, useState, useRef } from 'react';
import { Bell, Check, CheckCheck, ExternalLink, FileText, Copy, Loader2, Search, Plus, X, Filter, AlertCircle, CheckCircle, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ColoredBadge } from '@/components/ui/colored-badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { MultiSelect } from '@/components/ui/multi-select';
import { useToast } from '@/hooks/use-toast';
import { apiService, Notificacao, NotificacaoStats } from '@/services/api';
import { formatNumber } from '@/utils/formatters';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import NotificationRulesPanel from './NotificationRulesPanel';

const API_URL = "https://youtube-dashboard-backend-production.up.railway.app";

// Cache helpers - expires at 6 AM Brasília time (UTC-3)
const getNext6AMBrasilia = (): number => {
  const now = new Date();
  // Brasília is UTC-3
  const brasiliaOffset = -3 * 60; // minutes
  const localOffset = now.getTimezoneOffset(); // minutes
  const diffMinutes = brasiliaOffset + localOffset;
  
  // Get current time in Brasília
  const brasiliaTime = new Date(now.getTime() + diffMinutes * 60 * 1000);
  
  // Set to 6 AM today in Brasília
  const next6AM = new Date(brasiliaTime);
  next6AM.setHours(6, 0, 0, 0);
  
  // If it's already past 6 AM Brasília, set to tomorrow
  if (brasiliaTime >= next6AM) {
    next6AM.setDate(next6AM.getDate() + 1);
  }
  
  // Convert back to local time
  return next6AM.getTime() - diffMinutes * 60 * 1000;
};

const getCachedData = <T,>(key: string): T | null => {
  try {
    const cached = localStorage.getItem(key);
    if (!cached) return null;
    const { data, expiresAt } = JSON.parse(cached);
    if (Date.now() >= expiresAt) {
      localStorage.removeItem(key);
      return null;
    }
    return data as T;
  } catch {
    return null;
  }
};

const setCachedData = <T,>(key: string, data: T): void => {
  try {
    localStorage.setItem(key, JSON.stringify({ data, expiresAt: getNext6AMBrasilia() }));
  } catch (e) {
  }
};

const clearNotificationCaches = (): void => {
  localStorage.removeItem('notif_vistas_cache');
  localStorage.removeItem('notif_novas_cache');
  localStorage.removeItem('notif_stats_cache');
};

interface Regra {
  id: number;
  nome_regra: string;
  views_minimas: number;
  periodo_dias: number;
  tipo_canal: string;
  subnichos?: string[];
  ativa: boolean;
}

export function NotificationsTab() {
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
  const [stats, setStats] = useState<NotificacaoStats>({
    total: 0,
    nao_vistas: 0,
    vistas: 0,
    hoje: 0,
    esta_semana: 0,
  });
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [showRulesPanel, setShowRulesPanel] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [transcriptionModal, setTranscriptionModal] = useState(false);
  const [currentVideoId, setCurrentVideoId] = useState<string>("");
  const [transcriptionStatus, setTranscriptionStatus] = useState<Record<string, 'idle' | 'loading' | 'success' | 'error'>>(() => {
    try {
      const saved = localStorage.getItem('transcriptionStatus');
      const parsed = saved ? JSON.parse(saved) : {};
      return parsed;
    } catch {
      return {};
    }
  });
  const [transcriptions, setTranscriptions] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem('transcriptions');
      const parsed = saved ? JSON.parse(saved) : {};
      return parsed;
    } catch {
      return {};
    }
  });
  const [transcriptionMessages, setTranscriptionMessages] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem('transcriptionMessages');
      const parsed = saved ? JSON.parse(saved) : {};
      return parsed;
    } catch {
      return {};
    }
  });
  const [jobIds, setJobIds] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem('transcriptionJobIds');
      const parsed = saved ? JSON.parse(saved) : {};
      return parsed;
    } catch {
      return {};
    }
  });
  const [pollingIntervals, setPollingIntervals] = useState<Record<string, NodeJS.Timeout>>({});
  const { toast: toastOld } = useToast();

  // Filtros ativos
  const [activeFilters, setActiveFilters] = useState<{
    regra?: {tipo: string, periodo?: number, views?: number, label: string};
    subnichos: string[];
    linguas: string[];
    periodo?: 'hoje' | 'semana' | 'mes';
    status?: 'novas' | 'vistas';
    tipo_canal?: 'minerado' | 'nosso';
  }>({
    subnichos: [],
    linguas: []
  });
  const [showFiltersDropdown, setShowFiltersDropdown] = useState(false);
  const [regrasDisponiveis, setRegrasDisponiveis] = useState<Regra[]>([]);
  const [subnichosDisponiveis, setSubnichosDisponiveis] = useState<string[]>([]);
  const [linguasDisponiveis, setLinguasDisponiveis] = useState<string[]>([]);
  const filtersDropdownRef = useRef<HTMLDivElement>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const loadNotificacoes = async (forceRefresh = false) => {
    try {
      const cacheKey = showAll ? 'notif_vistas_cache' : 'notif_novas_cache';
      
      // Try cache first (unless forcing refresh)
      if (!forceRefresh) {
        const cached = getCachedData<Notificacao[]>(cacheKey);
        if (cached) {
          setNotificacoes(cached);
          return;
        }
      }
      
      if (showAll) {
        // Busca SOMENTE notificações VISTAS dos últimos 30 dias
        const data = await apiService.getTodasNotificacoes({ 
          limit: 500,
          offset: 0,
          vista: true,
          dias: 30,
          tipo_canal: activeFilters.tipo_canal
        });
        setNotificacoes(data.notificacoes);
        setCachedData(cacheKey, data.notificacoes);
      } else {
        // Busca notificações NÃO VISTAS usando o mesmo endpoint
        const data = await apiService.getTodasNotificacoes({ 
          limit: 500,
          offset: 0,
          vista: false,
          dias: 30,
          tipo_canal: activeFilters.tipo_canal
        });
        setNotificacoes(data.notificacoes);
        setCachedData(cacheKey, data.notificacoes);
      }
    } catch (error) {
      toastOld({
        title: 'Erro',
        description: 'Não foi possível carregar as notificações',
        variant: 'destructive',
        duration: 4000,
      });
    }
  };

  const loadStats = async (forceRefresh = false) => {
    try {
      // Try cache first
      if (!forceRefresh) {
        const cached = getCachedData<NotificacaoStats>('notif_stats_cache');
        if (cached) {
          setStats(cached);
          return;
        }
      }
      const data = await apiService.getNotificacoesStats();
      setStats(data);
      setCachedData('notif_stats_cache', data);
    } catch {
    }
  };

  const loadRegras = async () => {
    try {
      // Try cache first
      const cached = getCachedData<Regra[]>('notif_regras_cache');
      if (cached) {
        setRegrasDisponiveis(cached);
        return;
      }
      const response = await fetch(`${API_URL}/api/regras-notificacoes`);
      const data = await response.json();
      const regras = data.regras || [];
      setRegrasDisponiveis(regras);
      setCachedData('notif_regras_cache', regras);
    } catch {
    }
  };

  const loadSubnichos = async () => {
    try {
      // Try cache first
      const cached = getCachedData<string[]>('notif_subnichos_cache');
      if (cached) {
        setSubnichosDisponiveis(cached);
        return;
      }
      const response = await fetch(`${API_URL}/api/filtros`);
      const data = await response.json();
      const subnichos = data.subnichos || [];
      setSubnichosDisponiveis(subnichos);
      setCachedData('notif_subnichos_cache', subnichos);
    } catch {
    }
  };

  const loadLinguas = async () => {
    try {
      // Try cache first
      const cached = getCachedData<string[]>('notif_linguas_cache');
      if (cached) {
        setLinguasDisponiveis(cached);
        return;
      }
      const response = await fetch(`${API_URL}/api/filtros`);
      const data = await response.json();
      const linguas = data.linguas || [];
      setLinguasDisponiveis(linguas);
      setCachedData('notif_linguas_cache', linguas);
    } catch {
    }
  };

  const loadData = async () => {
    // Only show loading if no cached data
    const hasCache = getCachedData('notif_novas_cache') || getCachedData('notif_vistas_cache');
    if (!hasCache) {
      setLoading(true);
    }
    await Promise.all([loadNotificacoes(), loadStats(), loadRegras(), loadSubnichos(), loadLinguas()]);
    setLoading(false);
  };

  // Persistir estados no localStorage
  useEffect(() => {
    try {
      localStorage.setItem('transcriptionStatus', JSON.stringify(transcriptionStatus));
    } catch {
    }
  }, [transcriptionStatus]);

  useEffect(() => {
    try {
      localStorage.setItem('transcriptions', JSON.stringify(transcriptions));
    } catch {
    }
  }, [transcriptions]);

  useEffect(() => {
    try {
      localStorage.setItem('transcriptionMessages', JSON.stringify(transcriptionMessages));
    } catch {
    }
  }, [transcriptionMessages]);

  useEffect(() => {
    try {
      localStorage.setItem('transcriptionJobIds', JSON.stringify(jobIds));
    } catch {
    }
  }, [jobIds]);

  // Retomar polling de transcrições em andamento
  useEffect(() => {
    
    const resumePolling = () => {
      Object.entries(transcriptionStatus).forEach(([videoId, status]) => {
        
        if (status === 'loading') {
          const jobId = jobIds[videoId];
          if (jobId && !pollingIntervals[videoId]) {
            
            // Retomar polling
            const interval = setInterval(() => {
              pollTranscriptionStatus(videoId, jobId);
            }, 5000);
            
            setPollingIntervals(prev => ({ ...prev, [videoId]: interval }));
            
            // Fazer primeira verificação imediatamente
            pollTranscriptionStatus(videoId, jobId);
          } else if (!jobId) {
            setTranscriptionStatus(prev => ({ ...prev, [videoId]: 'idle' }));
          }
        } else if (status === 'success') {
        }
      });
    };

    // Pequeno delay para garantir que tudo foi carregado
    const timeout = setTimeout(resumePolling, 100);
    
    return () => clearTimeout(timeout);
  }, []); // Executar apenas na montagem

  useEffect(() => {
    loadData();

    // Auto-refresh a cada 30 segundos
    const interval = setInterval(() => {
      loadStats();
      if (!showAll) {
        loadNotificacoes();
      }
    }, 30000);

    return () => {
      clearInterval(interval);
      // Limpar todos os polling intervals ao desmontar
      Object.values(pollingIntervals).forEach(clearInterval);
    };
  }, [showAll]);

  // Fechar dropdown ao clicar fora (mas ignorar interações em popovers/portais do Radix)
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const isInsideContainer = filtersDropdownRef.current?.contains(target);
      const isRadixPortal = !!(
        target.closest('[data-radix-popper-content-wrapper]') ||
        target.closest('[role="listbox"]') ||
        target.closest('[data-radix-popover-content]') ||
        target.closest('[data-radix-select-content]')
      );

      if (!isInsideContainer && !isRadixPortal) {
        setShowFiltersDropdown(false);
      }
    };

    if (showFiltersDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showFiltersDropdown]);


  const marcarVista = async (id: number) => {
    try {
      await apiService.marcarNotificacaoVista(id);
      toast.success('Marcada como vista');
      clearNotificationCaches();
      await loadNotificacoes(true);
      await loadStats(true);
    } catch (error) {
      toast.error('Não foi possível marcar a notificação');
    }
  };

  const desmarcarVista = async (id: number) => {
    try {
      await apiService.desmarcarNotificacaoVista(id);
      toast.success('Notificação desmarcada com sucesso');
      clearNotificationCaches();
      await loadNotificacoes(true);
      await loadStats(true);
    } catch (error) {
      toast.error('Erro ao desmarcar notificação');
    }
  };

  const marcarTodasVistas = async () => {
    try {
      const result = await apiService.marcarTodasNotificacoesVistas();
      toast.success(`${result.count} notificações marcadas como vistas`);
      clearNotificationCaches();
      await loadNotificacoes(true);
      await loadStats(true);
    } catch (error) {
      toast.error('Não foi possível marcar as notificações');
    }
  };

  const marcarFiltradasComoVistas = async () => {
    try {
      // Verificar se há notificações não vistas
      const naoVistas = notificacoesUnicas.filter(n => !n.vista);
      
      if (naoVistas.length === 0) {
        toast.info('Todas as notificações filtradas já estão marcadas como vistas');
        return;
      }
      
      // Preparar filtros para enviar ao backend
      const filtros: {
        lingua?: string;
        tipo_canal?: 'minerado' | 'nosso';
        subnicho?: string;
        periodo_dias?: number;
      } = {};
      
      if (activeFilters.linguas.length === 1) filtros.lingua = activeFilters.linguas[0];
      if (activeFilters.tipo_canal) filtros.tipo_canal = activeFilters.tipo_canal;
      if (activeFilters.subnichos.length === 1) filtros.subnicho = activeFilters.subnichos[0];
      
      // Mapear período para dias
      if (activeFilters.periodo) {
        const periodoMap = { hoje: 1, semana: 7, mes: 30 };
        filtros.periodo_dias = periodoMap[activeFilters.periodo];
      }
      
      // Chamar endpoint otimizado (1 chamada só)
      const result = await apiService.marcarTodasNotificacoesVistas(filtros);
      
      toast.success(`${result.count} notificações marcadas como vistas`);
      clearNotificationCaches();
      await loadNotificacoes(true);
      await loadStats(true);
    } catch (error) {
      toast.error('Erro ao marcar notificações');
    }
  };

  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    if (diffInDays === 0) {
      return 'Hoje';
    } else if (diffInDays === 1) {
      return 'há 1 dia';
    } else {
      return `há ${diffInDays} dias`;
    }
  };

  const formatPeriodo = (dias: number): string => {
    if (dias === 1) return '1 dia';
    return `${dias} dias`;
  };

  const pollTranscriptionStatus = async (videoId: string, jobId: string) => {
    try {
      const response = await fetch(
        `https://youtube-dashboard-backend-production.up.railway.app/api/transcribe/status/${jobId}`
      );
      
      if (!response.ok) {
        throw new Error('Erro ao verificar status');
      }
      
      const data = await response.json();
      
      // Atualizar mensagem de status
      if (data.status === 'downloading') {
        setTranscriptionMessages(prev => ({ ...prev, [videoId]: '⬇️ Baixando vídeo...' }));
      } else if (data.status === 'transcribing') {
        setTranscriptionMessages(prev => ({ ...prev, [videoId]: '🎤 Transcrevendo áudio...' }));
      } else if (data.status === 'completed') {
        // Verificar se já foi processado (evitar duplicatas)
        if (transcriptionStatus[videoId] === 'success') {
          return;
        }
        
        // Parar polling IMEDIATAMENTE
        const interval = pollingIntervals[videoId];
        if (interval) {
          clearInterval(interval);
          setPollingIntervals(prev => {
            const newIntervals = { ...prev };
            delete newIntervals[videoId];
            return newIntervals;
          });
        }
        
        // Armazenar transcrição e atualizar estado
        setTranscriptions(prev => ({ ...prev, [videoId]: data.result.transcription }));
        setTranscriptionStatus(prev => ({ ...prev, [videoId]: 'success' }));
        
        // Mostrar mensagem de sucesso por 4 segundos
        setTranscriptionMessages(prev => ({ ...prev, [videoId]: '✅ Transcrição concluída!' }));
        setTimeout(() => {
          setTranscriptionMessages(prev => {
            const newMessages = { ...prev };
            delete newMessages[videoId];
            return newMessages;
          });
        }, 4000);
        
        toast.success('Transcrição concluída!', {
          description: 'Clique em "Ver Transcrição" para visualizar.',
          duration: 4000
        });
      } else if (data.status === 'failed') {
        // Parar polling
        const interval = pollingIntervals[videoId];
        if (interval) {
          clearInterval(interval);
          setPollingIntervals(prev => {
            const newIntervals = { ...prev };
            delete newIntervals[videoId];
            return newIntervals;
          });
        }
        
        setTranscriptionStatus(prev => ({ ...prev, [videoId]: 'error' }));
        setTranscriptionMessages(prev => {
          const newMessages = { ...prev };
          delete newMessages[videoId];
          return newMessages;
        });
        
        toast.error('Erro ao transcrever', {
          description: data.error || 'Ocorreu um erro. Tente novamente.'
        });
      }
    } catch (error) {
      
      // Parar polling em caso de erro
      const interval = pollingIntervals[videoId];
      if (interval) {
        clearInterval(interval);
        setPollingIntervals(prev => {
          const newIntervals = { ...prev };
          delete newIntervals[videoId];
          return newIntervals;
        });
      }
      
      setTranscriptionStatus(prev => ({ ...prev, [videoId]: 'error' }));
      setTranscriptionMessages(prev => {
        const newMessages = { ...prev };
        delete newMessages[videoId];
        return newMessages;
      });
      
      toast.error('Erro ao verificar status', {
        description: 'Tente novamente.'
      });
    }
  };

  const handleTranscribe = async (videoId: string) => {
    // Se já está transcrevendo, ignorar
    if (transcriptionStatus[videoId] === 'loading') return;
    
    // Limpar qualquer polling anterior para este vídeo
    const existingInterval = pollingIntervals[videoId];
    if (existingInterval) {
      clearInterval(existingInterval);
    }
    
    // Atualizar estado para loading
    setTranscriptionStatus(prev => ({ ...prev, [videoId]: 'loading' }));
    setTranscriptionMessages(prev => ({ ...prev, [videoId]: '🚀 Iniciando transcrição...' }));
    
    toast.info('Transcrição iniciada...', {
      description: 'Você pode continuar usando o dashboard normalmente.'
    });
    
    try {
      const response = await fetch(
        `https://youtube-dashboard-backend-production.up.railway.app/api/transcribe?video_id=${videoId}`,
        {
          method: 'POST'
        }
      );
      
      if (!response.ok) {
        throw new Error('Erro ao iniciar transcrição');
      }
      
      const data = await response.json();
      
      // Verificar se veio do cache (já completado)
      if (data.status === 'completed' && data.from_cache) {
        setTranscriptions(prev => ({ ...prev, [videoId]: data.result.transcription }));
        setTranscriptionStatus(prev => ({ ...prev, [videoId]: 'success' }));
        setTranscriptionMessages(prev => {
          const newMessages = { ...prev };
          delete newMessages[videoId];
          return newMessages;
        });
        
        toast.success('Transcrição recuperada do cache!', {
          description: 'Clique em "Ver Transcrição" para visualizar.'
        });
        return;
      }
      
      // Se retornou job_id, iniciar polling
      if (data.job_id) {
        // Salvar job_id
        setJobIds(prev => ({ ...prev, [videoId]: data.job_id }));
        
        const interval = setInterval(() => {
          pollTranscriptionStatus(videoId, data.job_id);
        }, 5000); // Poll a cada 5 segundos
        
        setPollingIntervals(prev => ({ ...prev, [videoId]: interval }));
        
        // Fazer primeira verificação imediatamente
        pollTranscriptionStatus(videoId, data.job_id);
      }
      
    } catch (error) {
      
      setTranscriptionStatus(prev => ({ ...prev, [videoId]: 'error' }));
      setTranscriptionMessages(prev => {
        const newMessages = { ...prev };
        delete newMessages[videoId];
        return newMessages;
      });
      
      toast.error('Erro ao transcrever', {
        description: 'Ocorreu um erro. Tente novamente.'
      });
    }
  };

  const handleViewTranscription = (videoId: string) => {
    const transcription = transcriptions[videoId];
    if (transcription) {
      setCurrentVideoId(videoId);
      setTranscriptionModal(true);
    }
  };

  const handleCloseTranscriptionModal = () => {
    setTranscriptionModal(false);
    setCurrentVideoId('');
  };

  const handleCopyTitle = (title: string) => {
    navigator.clipboard.writeText(title);
    toast.success('Título copiado!');
  };

  const copiarTodosTitulos = () => {
    const titulos = notificacoesUnicas.map(n => n.nome_video).join('\n');
    
    if (titulos.length === 0) {
      toast.info('Nenhum título para copiar');
      return;
    }
    
    navigator.clipboard.writeText(titulos);
    toast.success(`${notificacoesUnicas.length} títulos copiados!`);
  };

  const handleCopyTranscription = () => {
    const transcription = transcriptions[currentVideoId];
    if (transcription) {
      navigator.clipboard.writeText(transcription);
      toast.success('Transcrição copiada!');
    }
  };

  const addFilter = (type: 'regra' | 'subnicho' | 'lingua' | 'periodo' | 'status' | 'tipo_canal', value: any) => {
    
    if (type === 'regra') {
      setActiveFilters(prev => {
        const newFilters = { ...prev, regra: value };
        return newFilters;
      });
      setShowFiltersDropdown(false);
    } else if (type === 'subnicho') {
      // Para múltiplos subnichos
      setActiveFilters(prev => {
        const newFilters = { ...prev, subnichos: value };
        return newFilters;
      });
    } else if (type === 'lingua') {
      // Para múltiplas línguas
      setActiveFilters(prev => {
        const newFilters = { ...prev, linguas: value };
        return newFilters;
      });
    } else if (type === 'periodo') {
      setActiveFilters(prev => {
        const newFilters = { ...prev, periodo: value };
        return newFilters;
      });
      setShowFiltersDropdown(false);
    } else if (type === 'status') {
      setActiveFilters(prev => {
        const newFilters = { ...prev, status: value };
        return newFilters;
      });
      setShowFiltersDropdown(false);
    } else if (type === 'tipo_canal') {
      setActiveFilters(prev => {
        const newFilters = { ...prev, tipo_canal: value };
        return newFilters;
      });
      setShowFiltersDropdown(false);
    }
  };

  const removeFilter = (type: 'regra' | 'subnicho' | 'lingua' | 'periodo' | 'status' | 'tipo_canal', value?: string) => {
    if (type === 'regra') {
      setActiveFilters(prev => ({ ...prev, regra: undefined }));
    } else if (type === 'subnicho' && value) {
      setActiveFilters(prev => ({
        ...prev,
        subnichos: prev.subnichos.filter(s => s !== value)
      }));
    } else if (type === 'lingua' && value) {
      setActiveFilters(prev => ({
        ...prev,
        linguas: prev.linguas.filter(l => l !== value)
      }));
    } else if (type === 'periodo') {
      setActiveFilters(prev => ({ ...prev, periodo: undefined }));
    } else if (type === 'status') {
      setActiveFilters(prev => ({ ...prev, status: undefined }));
    } else if (type === 'tipo_canal') {
      setActiveFilters(prev => ({ ...prev, tipo_canal: undefined }));
    }
  };

  const clearAllFilters = () => {
    setActiveFilters({ subnichos: [], linguas: [] });
    setSearchTerm("");
  };

  // Aplicar filtros
  const notificacoesFiltradas = notificacoes.filter(notif => {
    // Filtro por regra
    if (activeFilters.regra) {
      const periodoMatch = notif.periodo_dias === activeFilters.regra.periodo;
      const viewsMatch = notif.views_atingidas >= (activeFilters.regra.views || 0);
      if (!periodoMatch || !viewsMatch) return false;
    }

    // Filtro por subnichos
    if (activeFilters.subnichos.length > 0) {
      const subnichoNormalizado = notif.subnicho?.replace(' (Dark History)', '');
      const match = activeFilters.subnichos.some(s => s.replace(' (Dark History)', '') === subnichoNormalizado);
      if (!match) {
        return false;
      }
    }

    // Filtro por línguas
    if (activeFilters.linguas.length > 0) {
      const match = activeFilters.linguas.includes(notif.lingua || '');
      if (!match) {
        return false;
      }
    }

    // Filtro por período
    if (activeFilters.periodo) {
      const now = new Date();
      const notifDate = new Date(notif.data_disparo);
      const diffDays = Math.floor((now.getTime() - notifDate.getTime()) / (1000 * 60 * 60 * 24));
      
      if (activeFilters.periodo === 'hoje' && diffDays !== 0) return false;
      if (activeFilters.periodo === 'semana' && (diffDays < 1 || diffDays > 7)) return false;  // ✅ Consistente com agrupamento visual
      if (activeFilters.periodo === 'mes' && diffDays <= 7) return false;
    }

    // Filtro por status
    if (activeFilters.status) {
      if (activeFilters.status === 'novas' && notif.vista) return false;
      if (activeFilters.status === 'vistas' && !notif.vista) return false;
    }

    // Filtro por tipo de canal
    if (activeFilters.tipo_canal) {
      const match = notif.tipo_canal === activeFilters.tipo_canal;
      if (!match) return false;
    }

    // Filtro por busca
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      const tituloMatch = notif.nome_video?.toLowerCase().includes(searchLower);
      const canalMatch = notif.nome_canal?.toLowerCase().includes(searchLower);
      if (!tituloMatch && !canalMatch) return false;
    }
    
    return true;
  });

  // Remover duplicatas por video_id
  const notificacoesPorVideo = new Map<string, Notificacao>();
  notificacoesFiltradas.forEach(notif => {
    const existing = notificacoesPorVideo.get(notif.video_id);
    if (!existing || new Date(notif.data_disparo) > new Date(existing.data_disparo)) {
      notificacoesPorVideo.set(notif.video_id, notif);
    }
  });
  
  const notificacoesUnicas = Array.from(notificacoesPorVideo.values());

  // Pagination logic
  const totalPages = Math.ceil(notificacoesUnicas.length / itemsPerPage);
  const paginatedNotificacoes = notificacoesUnicas.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [activeFilters, searchTerm, showAll]);

  // Verificar se há filtros ativos
  const hasActiveFilters = 
    activeFilters.regra !== undefined ||
    activeFilters.subnichos.length > 0 ||
    activeFilters.linguas.length > 0 ||
    activeFilters.periodo !== undefined ||
    activeFilters.status !== undefined ||
    activeFilters.tipo_canal !== undefined ||
    searchTerm.trim() !== '';

  // Agrupar por período (usando as notificações paginadas)
  const now = new Date();
  const hoje = paginatedNotificacoes.filter(n => {
    const diffDays = Math.floor((now.getTime() - new Date(n.data_disparo).getTime()) / (1000 * 60 * 60 * 24));
    return diffDays === 0;
  });
  
  const estaSemana = paginatedNotificacoes.filter(n => {
    const diffDays = Math.floor((now.getTime() - new Date(n.data_disparo).getTime()) / (1000 * 60 * 60 * 24));
    return diffDays >= 1 && diffDays <= 7;
  });
  
  const maisAntigas = paginatedNotificacoes.filter(n => {
    const diffDays = Math.floor((now.getTime() - new Date(n.data_disparo).getTime()) / (1000 * 60 * 60 * 24));
    return diffDays > 7;
  });

  const renderNotificationCard = (notif: Notificacao) => {
    const rawStatus = transcriptionStatus[notif.video_id] || 'idle';
    const hasTranscription = !!transcriptions[notif.video_id];
    const status = hasTranscription && rawStatus === 'idle' ? 'success' : rawStatus;
    const statusMessage = transcriptionMessages[notif.video_id];
    const cores = obterCorSubnicho(notif.subnicho?.replace(' (Dark History)', '') || '');
    
    return (
      <>
        {/* Desktop: Card Normal */}
        <div 
          key={`desktop-${notif.id}`}
          className="hidden lg:block p-4 rounded-lg border hover-lift transition-all duration-200"
          style={notif.vista ? {
            backgroundColor: 'rgba(34, 197, 94, 0.12)',
            borderLeft: '4px solid rgb(34, 197, 94)',
            borderColor: 'rgba(34, 197, 94, 0.25)',
            opacity: 0.8
          } : {
            backgroundColor: cores.fundo + '60',
            borderLeft: `4px solid ${cores.borda}`,
            borderColor: cores.borda
          }}
        >
          {/* Linha 1: Status + Métricas */}
          <div className="flex items-center gap-2 text-sm text-notification-detail mb-3">
            <span className={`${notif.vista ? '⚪' : '🔴'}`}>
              {notif.vista ? '⚪' : '🔴'}
            </span>
            <span className="font-medium">{formatNumber(notif.views_atingidas)}</span>
            <span>•</span>
            <span>{formatRelativeTime(notif.data_disparo)}</span>
            <span>•</span>
            <span>{formatPeriodo(notif.periodo_dias)}</span>
            {notif.data_publicacao && (
              <>
                <span>•</span>
                <span>
                  Postado há {Math.floor((new Date().getTime() - new Date(notif.data_publicacao).getTime()) / (1000 * 60 * 60 * 24)) === 0 
                    ? 'hoje' 
                    : Math.floor((new Date().getTime() - new Date(notif.data_publicacao).getTime()) / (1000 * 60 * 60 * 24)) === 1 
                    ? '1 dia' 
                    : `${Math.floor((new Date().getTime() - new Date(notif.data_publicacao).getTime()) / (1000 * 60 * 60 * 24))} dias`}
                </span>
              </>
            )}
          </div>

          {/* Linha 2: Título (DESTAQUE) */}
          <h3 className={`text-lg font-semibold mb-2 line-clamp-2 ${
            notif.vista ? 'text-green-900 dark:text-green-100' : 'text-foreground'
          }`}>
            {notif.nome_video}
          </h3>

          {/* Linha 3: Canal + Subnicho */}
          <div className="flex items-center gap-2 mb-4 text-sm font-medium flex-wrap">
            <span className="text-notification-detail">📺 {notif.tipo_canal === 'nosso' ? '👑 ' : ''}{notif.nome_canal}</span>
            {notif.subnicho && (
              <>
                <span className="text-notification-detail">•</span>
                <span className="text-notification-detail">🎯 {notif.subnicho.replace(' (Dark History)', '')}</span>
              </>
            )}
          </div>

          {/* Linha 4: Botões de ação */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(`https://www.youtube.com/watch?v=${notif.video_id}`, '_blank')}
              className="hover-scale"
            >
              <ExternalLink className="h-4 w-4 mr-1" strokeWidth={2} />
              Assistir
            </Button>
            
            {status === 'idle' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTranscribe(notif.video_id)}
                className="hover-scale"
              >
                <FileText className="h-4 w-4 mr-1" strokeWidth={2} />
                Transcrição
              </Button>
            )}
            
            {status === 'loading' && (
              <Button
                variant="outline"
                size="sm"
                disabled
                className="hover-scale"
              >
                <Loader2 className="h-4 w-4 mr-1 animate-spin" strokeWidth={2} />
                {statusMessage || 'Processando...'}
              </Button>
            )}
            
            {status === 'success' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleViewTranscription(notif.video_id)}
                className="hover-scale text-green-600 hover:text-green-700 border-green-600"
              >
                <CheckCircle className="h-4 w-4 mr-1" strokeWidth={2} />
                Ver Transcrição
              </Button>
            )}
            
            {status === 'error' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTranscribe(notif.video_id)}
                className="hover-scale text-red-600 hover:text-red-700 border-red-600"
              >
                <AlertCircle className="h-4 w-4 mr-1" strokeWidth={2} />
                Tentar Novamente
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopyTitle(notif.nome_video)}
              className="hover-scale"
            >
              <Copy className="h-4 w-4" strokeWidth={2} />
            </Button>

            {!notif.vista ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => marcarVista(notif.id)}
                className="hover-scale ml-auto"
              >
                <Check className="h-4 w-4 mr-1" strokeWidth={2} />
                Marcar Vista
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => desmarcarVista(notif.id)}
                className="hover-scale ml-auto"
              >
                <X className="h-4 w-4 mr-1" strokeWidth={2} />
                Desmarcar
              </Button>
            )}
          </div>
        </div>

        {/* Mobile: Card Otimizado */}
        <div
          key={`mobile-${notif.id}`}
          className="lg:hidden p-4 rounded-lg border space-y-3"
          style={notif.vista ? {
            backgroundColor: 'rgba(34, 197, 94, 0.12)',
            borderLeft: '4px solid rgb(34, 197, 94)',
            borderColor: 'rgba(34, 197, 94, 0.25)',
            opacity: 0.8
          } : {
            backgroundColor: cores.fundo + '60',
            borderLeft: `4px solid ${cores.borda}`,
            borderColor: cores.borda
          }}
        >
          {/* Nome do Canal */}
          <h3 className="text-lg font-bold text-foreground leading-tight">
            {notif.tipo_canal === 'nosso' ? '👑 ' : ''}{notif.nome_canal}
          </h3>

          {/* Subnicho */}
          <div className="mobile-subtitle">
            {notif.subnicho && (
              <ColoredBadge 
                text={notif.subnicho?.replace(' (Dark History)', '') || ''} 
                type="subnicho" 
                className="text-[10px] px-1.5 py-0.5 leading-tight" 
              />
            )}
          </div>

          {/* Métricas */}
          <div className="space-y-2 pt-2 border-t border-dashboard-border">
            <div className="flex items-center text-sm text-notification-detail">
              <span className="mr-2">👥</span>
              <span className="font-normal">{formatNumber(notif.views_atingidas)} views</span>
            </div>
            <div className="flex items-center text-sm text-notification-detail">
              <span className="mr-2">🎬</span>
              <span className="font-normal">Views 7d: {formatNumber(notif.views_atingidas)}</span>
            </div>
            <div className="flex items-center text-sm text-notification-detail">
              <span className="mr-2">📅</span>
              <span className="font-normal">{formatRelativeTime(notif.data_disparo)}</span>
            </div>
          </div>

          {/* Dois Botões Lado a Lado - Só Ícones */}
          <div className="notification-actions">
            <Button
              onClick={() => window.open(`https://www.youtube.com/watch?v=${notif.video_id}`, '_blank')}
              className="notification-action-button"
              variant="default"
              size="icon"
            >
              <span className="notification-action-icon">▶️</span>
            </Button>
            {!notif.vista ? (
              <Button
                onClick={() => marcarVista(notif.id)}
                className="notification-action-button"
                variant="outline"
                size="icon"
              >
                <span className="notification-action-icon">👁️</span>
              </Button>
            ) : (
              <Button
                onClick={() => desmarcarVista(notif.id)}
                className="notification-action-button"
                variant="ghost"
                size="icon"
              >
                <span className="notification-action-icon">❌</span>
              </Button>
            )}
          </div>
        </div>
      </>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <Bell className="h-6 w-6 text-red-500" strokeWidth={2} />
            <CardTitle className="text-2xl font-semibold">Notificações</CardTitle>
            {!showRulesPanel && stats.nao_vistas > 0 && (
              <Badge className="bg-red-500 text-white hover:bg-red-600">
                {stats.nao_vistas}
              </Badge>
            )}
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setShowRulesPanel(!showRulesPanel)}
              className="hover-scale"
            >
              {showRulesPanel ? "← Ver Notificações" : "⚙️ Gerenciar Regras"}
            </Button>
            {!showRulesPanel && (
              <Button
                variant={showAll ? 'outline' : 'default'}
                onClick={() => setShowAll(!showAll)}
                size="sm"
                className="hover-scale"
              >
                {showAll ? 'Ver Novas' : 'Vistas'}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {showRulesPanel ? (
          <NotificationRulesPanel />
        ) : (
          <>
            {/* Stats em mini-cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <div className="bg-secondary/20 rounded-lg p-3 text-center">
                <p className="text-sm text-muted-foreground mb-1">Total</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              
              <div className="bg-red-500/10 rounded-lg p-3 text-center border border-red-500/20">
                <p className="text-sm text-muted-foreground mb-1">Não vistas</p>
                <p className="text-2xl font-bold text-red-500">{stats.nao_vistas}</p>
              </div>
              
              <div className="bg-secondary/20 rounded-lg p-3 text-center">
                <p className="text-sm text-muted-foreground mb-1">Hoje</p>
                <p className="text-2xl font-bold">{stats.hoje}</p>
              </div>
              
              <div className="bg-secondary/20 rounded-lg p-3 text-center">
                <p className="text-sm text-muted-foreground mb-1">Esta semana</p>
                <p className="text-2xl font-bold">{stats.esta_semana}</p>
              </div>
            </div>

            {/* Barra de pesquisa */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                type="text"
                placeholder="Pesquisar..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full bg-dashboard-card border-dashboard-border"
              />
            </div>

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
                      Por Regra
                    </label>
                    <Select 
                      value={activeFilters.regra?.tipo.replace('regra_', '') || "all"}
                      onValueChange={(value) => {
                        if (value === "all") {
                          removeFilter('regra');
                        } else {
                          const regra = regrasDisponiveis.find(r => r.id.toString() === value);
                          if (regra) {
                            addFilter('regra', {
                              tipo: `regra_${regra.id}`,
                              periodo: regra.periodo_dias,
                              views: regra.views_minimas,
                              label: regra.nome_regra
                            });
                          }
                        }
                      }}
                    >
                      <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                        <SelectValue placeholder="Todas" />
                      </SelectTrigger>
                      <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                        <SelectItem value="all">Todas</SelectItem>
                        {regrasDisponiveis.map(regra => (
                          <SelectItem key={regra.id} value={regra.id.toString()}>
                            {regra.nome_regra}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="w-full">
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Por Subnicho
                    </label>
                    <MultiSelect
                      options={subnichosDisponiveis.map(s => ({ label: s, value: s }))}
                      selected={activeFilters.subnichos}
                      onChange={(selected) => addFilter('subnicho', selected)}
                      placeholder="Todos os subnichos"
                      className="w-full"
                    />
                  </div>

                  <div className="w-full">
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Por Lingua
                    </label>
                    <MultiSelect
                      options={linguasDisponiveis.map(l => ({ label: l, value: l }))}
                      selected={activeFilters.linguas}
                      onChange={(selected) => addFilter('lingua', selected)}
                      placeholder="Todas as línguas"
                      className="w-full"
                    />
                  </div>

                  <div className="w-full">
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Por Tipo de Canal
                    </label>
                    <Select 
                      value={activeFilters.tipo_canal || "all"}
                      onValueChange={(value) => {
                        if (value === "all") {
                          removeFilter('tipo_canal');
                        } else {
                          addFilter('tipo_canal', value as 'minerado' | 'nosso');
                        }
                      }}
                    >
                      <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                        <SelectValue placeholder="Todos os tipos" />
                      </SelectTrigger>
                      <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                        <SelectItem value="all">Todos</SelectItem>
                        <SelectItem value="nosso">Nossos Canais</SelectItem>
                        <SelectItem value="minerado">Canais Minerados</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="w-full">
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Por Período
                    </label>
                    <Select 
                      value={activeFilters.periodo || "all"}
                      onValueChange={(value) => {
                        if (value === "all") {
                          removeFilter('periodo');
                        } else {
                          addFilter('periodo', value as any);
                        }
                      }}
                    >
                      <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                        <SelectValue placeholder="Todos" />
                      </SelectTrigger>
                      <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                        <SelectItem value="all">Todos</SelectItem>
                        <SelectItem value="hoje">Hoje</SelectItem>
                        <SelectItem value="semana">Esta Semana</SelectItem>
                        <SelectItem value="mes">Este Mês</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="w-full">
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Por Status
                    </label>
                    <Select 
                      value={activeFilters.status || "all"}
                      onValueChange={(value) => {
                        if (value === "all") {
                          removeFilter('status');
                        } else {
                          addFilter('status', value as any);
                        }
                      }}
                    >
                      <SelectTrigger className="w-full bg-dashboard-card border-dashboard-border">
                        <SelectValue placeholder="Todos" />
                      </SelectTrigger>
                      <SelectContent className="bg-dashboard-card border-dashboard-border z-50">
                        <SelectItem value="all">Todos</SelectItem>
                        <SelectItem value="novas">Novas</SelectItem>
                        <SelectItem value="vistas">Vistas</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* Botões de ação em lote - só aparecem quando há filtros */}
            {hasActiveFilters && notificacoesUnicas.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-blue-400 mr-auto">
                  <Filter className="h-4 w-4" />
                  <span>{notificacoesUnicas.length} notificações filtradas</span>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copiarTodosTitulos}
                  className="gap-2"
                >
                  <Copy className="h-4 w-4" />
                  Copiar todos os títulos
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={marcarFiltradasComoVistas}
                  className="gap-2"
                  disabled={notificacoesUnicas.filter(n => !n.vista).length === 0}
                >
                  <CheckCheck className="h-4 w-4" />
                  Marcar todas como vistas
                </Button>
              </div>
            )}

            <Separator className="mb-6" />

            {/* Lista de notificações com agrupamento */}
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">
                Carregando notificações...
              </div>
            ) : notificacoesUnicas.length === 0 ? (
              <div className="text-center py-12">
                <Bell className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground">
                  Nenhuma notificação encontrada com os filtros selecionados
                </p>
              </div>
            ) : (
              <div className="space-y-8">
                {/* HOJE */}
                {hoje.length > 0 && (
                  <div className="fade-in">
                    <div className="flex items-center gap-3 mb-4 pb-2 border-b border-dashboard-border">
                      <h2 className="text-xl font-semibold">📅 HOJE</h2>
                      <Badge variant="secondary">{hoje.length} {hoje.length === 1 ? 'notificação' : 'notificações'}</Badge>
                    </div>
                    <div className="space-y-3">
                      {hoje.map(renderNotificationCard)}
                    </div>
                  </div>
                )}

                {/* ESTA SEMANA */}
                {estaSemana.length > 0 && (
                  <div className="fade-in">
                    <div className="flex items-center gap-3 mb-4 pb-2 border-b border-dashboard-border">
                      <h2 className="text-xl font-semibold">📆 ESTA SEMANA</h2>
                      <Badge variant="secondary">{estaSemana.length} {estaSemana.length === 1 ? 'notificação' : 'notificações'}</Badge>
                    </div>
                    <div className="space-y-3">
                      {estaSemana.map(renderNotificationCard)}
                    </div>
                  </div>
                )}

                {/* MAIS ANTIGAS */}
                {maisAntigas.length > 0 && (
                  <div className="fade-in">
                    <div className="flex items-center gap-3 mb-4 pb-2 border-b border-dashboard-border">
                      <h2 className="text-xl font-semibold">📋 MAIS ANTIGAS</h2>
                      <Badge variant="secondary">{maisAntigas.length} {maisAntigas.length === 1 ? 'notificação' : 'notificações'}</Badge>
                    </div>
                    <div className="space-y-3">
                      {maisAntigas.map(renderNotificationCard)}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Pagination Controls */}
            {notificacoesUnicas.length > 0 && (
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 mt-6 border-t border-dashboard-border">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Mostrando {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, notificacoesUnicas.length)} de {notificacoesUnicas.length}</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Por página:</span>
                    <Select value={String(itemsPerPage)} onValueChange={(value) => { setItemsPerPage(Number(value)); setCurrentPage(1); }}>
                      <SelectTrigger className="w-[70px] h-8 bg-dashboard-card border-dashboard-border">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-dashboard-card border-dashboard-border">
                        <SelectItem value="25">25</SelectItem>
                        <SelectItem value="50">50</SelectItem>
                        <SelectItem value="100">100</SelectItem>
                        <SelectItem value="200">200</SelectItem>
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
                      {currentPage} / {totalPages || 1}
                    </span>
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => { setCurrentPage(p => Math.min(totalPages, p + 1)); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                      disabled={currentPage === totalPages || totalPages === 0}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>

      {/* Modal de Transcrição */}
      <Dialog open={transcriptionModal} onOpenChange={handleCloseTranscriptionModal}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Transcrição do Vídeo</DialogTitle>
            <DialogDescription>
              Conteúdo transcrito automaticamente
            </DialogDescription>
          </DialogHeader>
          
          <div className="max-h-[400px] overflow-y-auto p-4 bg-secondary/20 rounded-lg">
            <p className="whitespace-pre-wrap text-sm">{transcriptions[currentVideoId]}</p>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={handleCopyTranscription}>
              <Copy className="h-4 w-4 mr-2" strokeWidth={2} />
              Copiar Transcrição
            </Button>
            <Button onClick={handleCloseTranscriptionModal}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
