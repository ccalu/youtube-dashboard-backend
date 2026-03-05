import { useState, useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  Sidebar,
  SidebarContent,
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
  Wallet,
  MessageSquare,
  Kanban,
  CalendarDays,
} from 'lucide-react';
import { apiService, NotificacaoStats } from '@/services/api';
import { kanbanApiService } from '@/services/kanbanApi';
import { calendarApiService } from '@/services/calendarApi';

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
  const [notificationStats, setNotificationStats] = useState<NotificacaoStats>({
    total: 0,
    nao_vistas: 0,
    vistas: 0,
    hoje: 0,
    esta_semana: 0,
  });

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
    } catch (error) {
      console.error('Erro ao carregar stats de notificações:', error);
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

  // Helper para cor do ícone quando não ativo/hover
  const getIconColor = (itemId: string) => ({
    // NAVEGAÇÃO - Vermelhos verdadeiros
    'tabela': 'text-red-500',
    'our-channels': 'text-red-600',
    'channels': 'text-red-700',
    'notifications': 'text-red-500',
    // EMPRESA - Verdes
    'monetization': 'text-green-500',
    'financeiro': 'text-emerald-500',
  }[itemId] || 'text-muted-foreground');

  // Empresa nav items (new category)
  const empresaNavItems: NavigationItem[] = [
    { id: 'monetization', title: 'Monetização', icon: DollarSign, activeColor: 'bg-green-500' },
    { id: 'financeiro', title: 'Financeiro', icon: Wallet, activeColor: 'bg-emerald-500' },
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

  const toolsItems = [
    { id: 'history', title: 'Histórico de Coleta', icon: History, action: onOpenHistory, color: '#3b82f6', iconColor: 'text-blue-500' },
    { id: 'kanban', title: 'Kanban', icon: Kanban, action: () => handleNavClick('kanban'), onHover: prefetchKanban, color: '#6366f1', iconColor: 'text-indigo-500' },
    { id: 'calendar', title: 'Calendário', icon: CalendarDays, action: () => handleNavClick('calendar'), onHover: prefetchCalendar, color: '#8b5cf6', iconColor: 'text-violet-500' },
    { id: 'comments', title: 'Comentários', icon: MessageSquare, action: onOpenComments, onHover: prefetchComments, color: '#06b6d4', iconColor: 'text-cyan-500' },
    { id: 'favorites', title: 'Favoritos', icon: Star, action: onOpenFavorites, color: '#eab308', iconColor: 'text-yellow-500' },
  ];

  const handleNavClick = (itemId: string) => {
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
    'financeiro': { bg: '#10b981', hover: 'rgba(16, 185, 129, 0.25)' },
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
            isActive || isHovered
              ? 'text-white shadow-sm' 
              : 'text-muted-foreground hover:scale-[1.02]'
          }`}
          style={{ 
            backgroundColor: isActive ? colors.bg : (isHovered ? colors.hover : 'transparent'),
            borderColor: isHovered || isActive ? colors.bg : 'transparent'
          }}
          tooltip={item.title}
        >
          <item.icon className={`h-4 w-4 sm:h-[18px] sm:w-[18px] transition-transform duration-200 ${
            isActive || isHovered ? 'text-white' : iconColor
          } ${isHovered && !isActive ? 'scale-110' : ''}`} />
          <span className={`flex-1 font-medium text-sm ${isActive || isHovered ? 'text-white' : ''}`}>{item.title}</span>
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
    <Sidebar className="border-r border-border/50 bg-gradient-to-b from-card to-card/95 overflow-x-hidden shadow-xl">
      {/* Header com logo */}
      <SidebarHeader className="p-3 sm:p-4 border-b border-border/30 overflow-hidden">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-red-600 to-red-500 flex items-center justify-center shadow-md shrink-0">
            <svg viewBox="0 0 24 24" className="h-4 w-4 text-white fill-current">
              <path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/>
            </svg>
          </div>
          <h2 className="text-base font-bold text-foreground truncate">YouTube Dashboard</h2>
        </div>
      </SidebarHeader>
      
      <SidebarContent className="px-2 py-2 sm:py-3">
        {/* Navegação Principal */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 px-2 mb-1.5 flex items-center gap-2">
            <span className="h-px flex-1 bg-gradient-to-r from-red-500/50 to-transparent" />
            <span className="text-red-400">🚀 Navegação</span>
            <span className="h-px flex-1 bg-gradient-to-l from-red-500/50 to-transparent" />
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
            <span className="h-px flex-1 bg-gradient-to-r from-emerald-500/50 to-transparent" />
            <span className="text-emerald-400">💰 Empresa</span>
            <span className="h-px flex-1 bg-gradient-to-l from-emerald-500/50 to-transparent" />
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {empresaNavItems.map(renderNavItem)}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <div className="my-2" />

        {/* Ferramentas */}
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/70 px-2 mb-1.5 flex items-center gap-2">
            <span className="h-px flex-1 bg-gradient-to-r from-blue-500/50 to-transparent" />
            <span className="text-blue-400">🛠️ Ferramentas</span>
            <span className="h-px flex-1 bg-gradient-to-l from-blue-500/50 to-transparent" />
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
    </Sidebar>
  );
}
