import { useState, useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
  useSidebar,
} from '@/components/ui/sidebar';
import { Badge } from '@/components/ui/badge';
import {
  TableIcon,
  Users,
  Home,
  DollarSign,
  Bell,
  Star,
  History,

  MessageSquare,
  Kanban,
  CalendarDays,
  Wallet,
  ExternalLink,
  Rocket,
  Monitor,
  Bot,
  LogOut,
  Image,
  Key,
} from 'lucide-react';
import { apiService, NotificacaoStats } from '@/services/api';
import { kanbanApiService } from '@/services/kanbanApi';
import { calendarApiService } from '@/services/calendarApi';
import { useAuth } from '@/contexts/AuthContext';

type NavigationItem = {
  id: string;
  title: string;
  icon: React.ElementType;
  badge?: number;
  activeColor?: string;
};

interface AppSidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  onOpenFavorites: () => void;
  onOpenHistory: () => void;
  onOpenComments: () => void;
}

export function AppSidebar({
  activeTab,
  onTabChange,
  onOpenFavorites,
  onOpenHistory,
  onOpenComments,
}: AppSidebarProps) {
  const queryClient = useQueryClient();
  const { isMobile, setOpenMobile } = useSidebar();
  const { user, logout } = useAuth();
  const [notificationStats, setNotificationStats] = useState<NotificacaoStats>({
    total: 0,
    nao_vistas: 0,
    vistas: 0,
    hoje: 0,
    esta_semana: 0,
  });
  const [perfisAlertCount, setPerfisAlertCount] = useState(0);

  // Cache expiration at 6 AM Brasília time
  const shouldRefreshCache = useCallback(() => {
    const now = new Date();
    const brasiliaOffset = -3 * 60; // UTC-3 in minutes
    const localOffset = now.getTimezoneOffset();
    const brasiliaTime = new Date(now.getTime() + (localOffset + brasiliaOffset) * 60000);
    
    const lastRefresh = localStorage.getItem('sidebar_stats_last_refresh');
    if (!lastRefresh) return true;
    
    const lastRefreshDate = new Date(lastRefresh);
    const lastRefreshBrasilia = new Date(lastRefreshDate.getTime() + (localOffset + brasiliaOffset) * 60000);
    
    // Check if we've crossed 6 AM Brasília since last refresh
    const today6AM = new Date(brasiliaTime);
    today6AM.setHours(6, 0, 0, 0);
    
    if (brasiliaTime >= today6AM && lastRefreshBrasilia < today6AM) {
      return true;
    }
    
    return false;
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const data = await apiService.getNotificacoesStats();
      setNotificationStats(data);
      localStorage.setItem('sidebar_stats_last_refresh', new Date().toISOString());
    } catch {
    }
  }, []);

  useEffect(() => {
    if (shouldRefreshCache()) {
      loadStats();
    } else {
      // Try to load from cache
      const cachedStats = localStorage.getItem('sidebar_notification_stats');
      if (cachedStats) {
        setNotificationStats(JSON.parse(cachedStats));
      } else {
        loadStats();
      }
    }
    
    const interval = setInterval(() => {
      if (shouldRefreshCache()) {
        loadStats();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [loadStats, shouldRefreshCache]);

  // Save stats to cache when they change
  useEffect(() => {
    if (notificationStats.total > 0) {
      localStorage.setItem('sidebar_notification_stats', JSON.stringify(notificationStats));
    }
  }, [notificationStats]);

  // Perfis alerts badge polling (every 30s)
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch('/api/perfis/alerts-count');
        if (res.ok) {
          const data = await res.json();
          setPerfisAlertCount(data.count || 0);
        }
      } catch {}
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  // Helper para cor do ícone quando não ativo/hover
  const getIconColor = (itemId: string) => ({
    // NAVEGAÇÃO - Vermelhos verdadeiros
    'tabela': 'text-red-500',
    'our-channels': 'text-red-600',
    'channels': 'text-red-700',
    'notifications': 'text-red-500',
    // EMPRESA - Verdes
    'monetization': 'text-green-500',
    'financeiro-ext': 'text-emerald-500',
    'perfis': 'text-teal-500',
    'upload-ext': 'text-purple-500',
    'mission-control-ext': 'text-purple-500',
    'dash-agentes-ext': 'text-purple-500',
    'thumb-ext': 'text-purple-500',
    'chaves-api-ext': 'text-purple-500',
  }[itemId] || 'text-muted-foreground');

  // Empresa nav items (new category)
  const empresaNavItems: NavigationItem[] = [
    { id: 'financeiro-ext', title: 'Financeiro', icon: Wallet, activeColor: 'bg-emerald-500' },
    { id: 'monetization', title: 'Monetização', icon: DollarSign, activeColor: 'bg-green-500' },
    { id: 'perfis', title: 'Perfis', icon: Users, badge: perfisAlertCount, activeColor: 'bg-teal-500' },
  ];

  const mainNavItems: NavigationItem[] = [
    { id: 'tabela', title: 'Tabela', icon: TableIcon, activeColor: 'bg-red-500' },
    { id: 'our-channels', title: 'Nossos Canais', icon: Home, activeColor: 'bg-red-600' },
    { id: 'channels', title: 'Canais Minerados', icon: Users, activeColor: 'bg-red-700' },
    { 
      id: 'notifications', 
      title: 'Notificações', 
      icon: Bell, 
      badge: notificationStats.nao_vistas,
      activeColor: 'bg-red-500'
    },
  ];

  // Prefetch Kanban and Comments data on hover for instant load
  const prefetchKanban = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: ['kanban-structure'],
      queryFn: () => kanbanApiService.getStructure(),
      staleTime: 1000 * 60 * 5, // 5 minutes (matches KanbanTab)
    });
  }, [queryClient]);

  const prefetchComments = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: ['comments-summary'],
      queryFn: () => apiService.getCommentsSummary(),
      staleTime: 1000 * 60 * 60,
    });
    queryClient.prefetchQuery({
      queryKey: ['monetized-channels-comments'],
      queryFn: () => apiService.getMonetizedChannelsComments(),
      staleTime: 1000 * 60 * 60,
    });
  }, [queryClient]);

  const prefetchCalendar = useCallback(() => {
    const now = new Date();
    queryClient.prefetchQuery({
      queryKey: ['calendar-events', now.getFullYear(), now.getMonth() + 1],
      queryFn: () => calendarApiService.getMonth(now.getFullYear(), now.getMonth() + 1),
      staleTime: 1000 * 60 * 5,
    });
  }, [queryClient]);

  // Automações nav items (external links)
  const automacoesNavItems: NavigationItem[] = [
    { id: 'upload-ext', title: 'Upload', icon: Rocket, activeColor: 'bg-purple-500' },
    { id: 'mission-control-ext', title: 'Mission Control', icon: Monitor, activeColor: 'bg-purple-500' },
    { id: 'dash-agentes-ext', title: 'Dash Agentes', icon: Bot, activeColor: 'bg-purple-500' },
    { id: 'thumb-ext', title: 'Thumb', icon: Image, activeColor: 'bg-purple-500' },
    { id: 'chaves-api-ext', title: 'Chaves API', icon: Key, activeColor: 'bg-purple-500' },
  ];

  const toolsItems = [
    { id: 'history', title: 'Histórico de Coleta', icon: History, action: onOpenHistory, color: '#3b82f6', iconColor: 'text-blue-500' },
    { id: 'kanban', title: 'Kanban', icon: Kanban, action: () => handleNavClick('kanban'), onHover: prefetchKanban, color: '#6366f1', iconColor: 'text-indigo-500' },
    { id: 'calendar', title: 'Calendário', icon: CalendarDays, action: () => handleNavClick('calendar'), onHover: prefetchCalendar, color: '#8b5cf6', iconColor: 'text-violet-500' },
    { id: 'comments', title: 'Comentários', icon: MessageSquare, action: onOpenComments, onHover: prefetchComments, color: '#06b6d4', iconColor: 'text-cyan-500' },
    { id: 'favorites', title: 'Favoritos', icon: Star, action: onOpenFavorites, color: '#eab308', iconColor: 'text-yellow-500' },
  ];

  const handleNavClick = (itemId: string) => {
    const externalLinks: Record<string, string> = {
      'financeiro-ext': 'https://financeiro-dashboard-production.up.railway.app/',

      'upload-ext': 'https://youtube-dashboard-backend-production.up.railway.app/dash-upload',
      'mission-control-ext': 'https://youtube-dashboard-backend-production.up.railway.app/mission-control',
      'dash-agentes-ext': 'https://youtube-dashboard-backend-production.up.railway.app/dash-analise-copy',
      'thumb-ext': 'https://web-production-1293.up.railway.app/',
      'chaves-api-ext': 'https://dashboard-next-production-2ea8.up.railway.app/',
    };
    if (externalLinks[itemId]) {
      window.open(externalLinks[itemId], '_blank');
      return;
    }
    onTabChange(itemId);
    if (isMobile) {
      setOpenMobile(false);
    }
  };

  const handleToolClick = (action: () => void) => {
    action();
    if (isMobile) {
      setOpenMobile(false);
    }
  };

  const getItemColors = (itemId: string) => ({
    // NAVEGAÇÃO - Vermelhos verdadeiros
    'tabela': { bg: '#ef4444', hover: 'rgba(239, 68, 68, 0.25)' },
    'our-channels': { bg: '#dc2626', hover: 'rgba(220, 38, 38, 0.25)' },
    'channels': { bg: '#b91c1c', hover: 'rgba(185, 28, 28, 0.25)' },
    'notifications': { bg: '#ef4444', hover: 'rgba(239, 68, 68, 0.25)' },
    // EMPRESA - Verdes
    'monetization': { bg: '#22c55e', hover: 'rgba(34, 197, 94, 0.25)' },
    'financeiro-ext': { bg: '#10b981', hover: 'rgba(16, 185, 129, 0.25)' },
    'perfis': { bg: '#14b8a6', hover: 'rgba(20, 184, 166, 0.25)' },
    'upload-ext': { bg: '#a855f7', hover: 'rgba(168, 85, 247, 0.25)' },
    'mission-control-ext': { bg: '#a855f7', hover: 'rgba(168, 85, 247, 0.25)' },
    'dash-agentes-ext': { bg: '#a855f7', hover: 'rgba(168, 85, 247, 0.25)' },
    'thumb-ext': { bg: '#a855f7', hover: 'rgba(168, 85, 247, 0.25)' },
    'chaves-api-ext': { bg: '#a855f7', hover: 'rgba(168, 85, 247, 0.25)' },
  }[itemId] || { bg: '#6b7280', hover: 'rgba(107, 114, 128, 0.25)' });

  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const renderNavItem = (item: NavigationItem) => {
    const isActive = activeTab === item.id;
    const colors = getItemColors(item.id);
    const isHovered = hoveredItem === item.id;
    const iconColor = getIconColor(item.id);
    
    return (
      <SidebarMenuItem key={item.id}>
        <SidebarMenuButton
          onClick={() => handleNavClick(item.id)}
          onMouseEnter={() => setHoveredItem(item.id)}
          onMouseLeave={() => setHoveredItem(null)}
          isActive={isActive}
          className={`rounded-md h-9 sm:h-10 transition-all duration-200 border ${
            isActive
              ? 'text-white'
              : isHovered
              ? 'text-white shadow-sm'
              : 'text-muted-foreground hover:scale-[1.02]'
          }`}
          style={{
            backgroundColor: isActive ? colors.bg : (isHovered ? colors.hover : 'transparent'),
            borderColor: isHovered || isActive ? colors.bg : 'transparent',
            boxShadow: isActive ? `0 0 12px -2px ${colors.bg}, inset 3px 0 0 0 ${colors.bg}` : undefined,
          }}
          tooltip={item.title}
        >
          <item.icon className={`h-4 w-4 sm:h-[18px] sm:w-[18px] transition-transform duration-200 ${
            isActive || isHovered ? 'text-white' : iconColor
          } ${isHovered && !isActive ? 'scale-110' : ''}`} />
          <span className={`flex-1 font-medium text-sm ${isActive || isHovered ? 'text-white' : ''}`}>{item.title}</span>
          {item.id.endsWith('-ext') && (
            <ExternalLink className={`h-3.5 w-3.5 ${isActive || isHovered ? 'text-white/70' : 'text-muted-foreground/50'}`} />
          )}
          {item.badge !== undefined && item.badge > 0 && (
            <Badge className="ml-auto h-5 min-w-5 flex items-center justify-center px-1.5 text-[10px] font-bold bg-red-500 text-white border-none rounded-full animate-pulse-badge">
              {item.badge}
            </Badge>
          )}
        </SidebarMenuButton>
      </SidebarMenuItem>
    );
  };

  return (
    <Sidebar className="border-r border-white/[0.06] glass-heavy overflow-x-hidden shadow-xl">
      {/* Header com logo */}
      <SidebarHeader className="p-3 sm:p-4 border-b border-white/[0.06] overflow-hidden gradient-line-bottom">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-red-600 to-red-500 flex items-center justify-center shadow-md shadow-red-500/20 shrink-0">
            <svg viewBox="0 0 24 24" className="h-4 w-4 text-white fill-current">
              <path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/>
            </svg>
          </div>
          <h2 className="text-base font-bold truncate bg-gradient-to-r from-red-400 via-red-500 to-orange-400 bg-clip-text text-transparent">YouTube Dashboard</h2>
        </div>
      </SidebarHeader>
      
      <SidebarContent className="px-2 py-2 sm:py-3">
        {/* Navegação Principal */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 px-2 mb-1.5 flex items-center gap-2">
            <span className="h-px flex-1 bg-gradient-to-r from-violet-500/40 to-transparent" />
            <span className="text-violet-400/80">Navegação</span>
            <span className="h-px flex-1 bg-gradient-to-l from-violet-500/40 to-transparent" />
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {mainNavItems.map(renderNavItem)}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <div className="my-2" />

        {/* Empresa Category (BETWEEN Navegação and Ferramentas) */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 px-2 mb-1.5 flex items-center gap-2">
            <span className="h-px flex-1 bg-gradient-to-r from-emerald-500/40 to-transparent" />
            <span className="text-emerald-400/80">Empresa</span>
            <span className="h-px flex-1 bg-gradient-to-l from-emerald-500/40 to-transparent" />
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {empresaNavItems.map(renderNavItem)}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <div className="my-2" />

        {/* Automações */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 px-2 mb-1.5 flex items-center gap-2">
            <span className="h-px flex-1 bg-gradient-to-r from-purple-500/40 to-transparent" />
            <span className="text-purple-400/80">Automações</span>
            <span className="h-px flex-1 bg-gradient-to-l from-purple-500/40 to-transparent" />
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {automacoesNavItems.map(renderNavItem)}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <div className="my-2" />

        {/* Ferramentas */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 px-2 mb-1.5 flex items-center gap-2">
            <span className="h-px flex-1 bg-gradient-to-r from-cyan-500/40 to-transparent" />
            <span className="text-cyan-400/80">Ferramentas</span>
            <span className="h-px flex-1 bg-gradient-to-l from-cyan-500/40 to-transparent" />
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {toolsItems.map((item) => {
                const isToolHovered = hoveredItem === item.id;
                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      onClick={() => handleToolClick(item.action)}
                      onMouseEnter={() => {
                        setHoveredItem(item.id);
                        item.onHover?.();
                      }}
                      onMouseLeave={() => setHoveredItem(null)}
                      className={`rounded-md h-9 sm:h-10 transition-all duration-200 border ${
                        isToolHovered 
                          ? 'text-white shadow-sm scale-[1.02]' 
                          : 'text-muted-foreground hover:scale-[1.02]'
                      }`}
                      style={{ 
                        backgroundColor: isToolHovered ? `${item.color}40` : 'transparent',
                        borderColor: isToolHovered ? item.color : 'transparent'
                      }}
                      tooltip={item.title}
                    >
                      <item.icon className={`h-4 w-4 sm:h-[18px] sm:w-[18px] transition-transform duration-200 ${
                        isToolHovered ? 'text-white scale-110' : item.iconColor
                      } ${item.id === 'favorites' && !isToolHovered ? 'fill-yellow-500' : ''}`} />
                      <span className={`font-medium text-sm ${isToolHovered ? 'text-white' : ''}`}>{item.title}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3 border-t border-white/[0.06]">
        <div className="flex items-center justify-between px-2">
          <span className="text-xs text-muted-foreground truncate">
            {user?.display_name}
          </span>
          <button
            onClick={logout}
            className="text-muted-foreground hover:text-red-400 transition-colors p-1.5 rounded-md hover:bg-white/[0.06]"
            title="Sair"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
