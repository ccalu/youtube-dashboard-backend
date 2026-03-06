import { useState, useCallback, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ChannelsTable } from './ChannelsTable';
import { OurChannelsTable } from './OurChannelsTable';
import { FavoritesTable } from './FavoritesTable';
import { NotificationsTab } from './NotificationsTab';
import { TabelaCanais } from './TabelaCanais';
import { MonetizationTab } from './monetization/MonetizationTab';

import { CommentsTab } from './comments';
import { KanbanTab } from './kanban';
import { CalendarTab } from './calendar';
import { Menu, Star } from 'lucide-react';
import { CollectionHistoryModal } from './CollectionHistoryModal';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { usePullToRefresh } from '@/hooks/usePullToRefresh';
import { PullToRefreshIndicator } from './PullToRefreshIndicator';
import { LastUpdateIndicator } from './LastUpdateIndicator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { AppSidebar } from './AppSidebar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useIsMobile } from '@/hooks/use-mobile';
import { apiService } from '@/services/api';

const DashboardContent = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const isMobile = useIsMobile();
  const [activeTab, setActiveTab] = useState('tabela');
  const [prevTab, setPrevTab] = useState('tabela');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [favoritesOpen, setFavoritesOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [commentsOpen, setCommentsOpen] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefreshData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // 1. Limpar cache do backend
      await apiService.clearCache();
      console.log('Cache do backend limpo com sucesso');
      
      // 2. Invalidar queries do React Query
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['channels'] }),
        queryClient.invalidateQueries({ queryKey: ['our-channels'] }),
        queryClient.invalidateQueries({ queryKey: ['notificacoes'] }),
        queryClient.invalidateQueries({ queryKey: ['favoritos-canais'] }),
        queryClient.invalidateQueries({ queryKey: ['favoritos-videos'] }),
        queryClient.invalidateQueries({ queryKey: ['kanban-structure'] }),
        queryClient.invalidateQueries({ queryKey: ['comments-summary'] }),
        queryClient.invalidateQueries({ queryKey: ['calendar-events'] }),
      ]);
      
      setLastUpdate(new Date());
      toast({
        title: "Dashboard atualizado",
        description: "Cache limpo e dados atualizados com sucesso",
      });
    } catch (error) {
      console.error('Erro ao atualizar:', error);
      toast({
        title: "Erro ao atualizar",
        description: "Não foi possível atualizar o dashboard",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  }, [queryClient, toast]);

  // Pull-to-refresh for mobile
  const { pullDistance, isRefreshing: isPullRefreshing, shouldTrigger } = usePullToRefresh({
    onRefresh: handleRefreshData,
    disabled: !isMobile,
  });

  // Handle tab change with transition
  const handleTabChange = useCallback((newTab: string) => {
    if (newTab !== activeTab) {
      setPrevTab(activeTab);
      setIsTransitioning(true);
      
      // Wait for fade-out, then change tab
      setTimeout(() => {
        setActiveTab(newTab);
        setIsTransitioning(false);
      }, 150);
    }
  }, [activeTab]);

  // Set initial last update
  useEffect(() => {
    setLastUpdate(new Date());
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'tabela':
        return <TabelaCanais />;
      case 'channels':
        return (
          <Card className="glass shadow-glass">
            <CardContent className="pt-2 lg:pt-6">
              <ChannelsTable />
            </CardContent>
          </Card>
        );
      case 'our-channels':
        return (
          <Card className="glass shadow-glass">
            <CardContent className="pt-2 lg:pt-6">
              <OurChannelsTable />
            </CardContent>
          </Card>
        );
      case 'monetization':
        return <MonetizationTab />;
      case 'notifications':
        return <NotificationsTab />;

      case 'comments':
        return <CommentsTab />;
      case 'kanban':
        return <KanbanTab />;
      case 'calendar':
        return <CalendarTab />;
      default:
        return <TabelaCanais />;
    }
  };

  return (
    <>
      {/* Pull-to-refresh indicator for mobile */}
      <PullToRefreshIndicator
        pullDistance={pullDistance}
        isRefreshing={isPullRefreshing}
        shouldTrigger={shouldTrigger}
      />

      <AppSidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onOpenFavorites={() => setFavoritesOpen(true)}
        onOpenHistory={() => setHistoryOpen(true)}
        onOpenComments={() => handleTabChange('comments')}
      />
      
      <main className="flex-1 min-h-screen overflow-x-hidden">
        <div className="container mx-auto px-4 sm:px-6 pt-6 sm:pt-8 pb-4 sm:pb-8">
          {/* Header with gradient line */}
          <div className="mb-6 sm:mb-8 flex items-center justify-center relative">
            <SidebarTrigger className="absolute left-0 h-9 w-9 sm:h-10 sm:w-10 rounded-lg glass hover-glow-red transition-all duration-300">
              <Menu className="h-5 w-5" />
            </SidebarTrigger>

            <div className="text-center">
              <h1 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-red-400 via-red-500 to-orange-400 bg-clip-text text-transparent">
                YouTube Dashboard
              </h1>
              <div className="mt-2 h-px mx-auto bg-gradient-to-r from-transparent via-red-500/50 to-transparent animate-header-line" />
            </div>

            {/* Last update indicator */}
            <div className="absolute right-0">
              <LastUpdateIndicator
                lastUpdate={lastUpdate}
                onRefresh={handleRefreshData}
                isRefreshing={isRefreshing}
              />
            </div>
          </div>

          {/* Main Content with transition */}
          <div
            className={`transition-opacity duration-150 ${
              isTransitioning ? 'opacity-0' : 'opacity-100'
            }`}
          >
            {renderContent()}
          </div>
        </div>
      </main>

      {/* Favorites Modal */}
      <Dialog open={favoritesOpen} onOpenChange={setFavoritesOpen}>
        <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] p-0">
          <DialogHeader className="px-6 pt-6 pb-2">
            <DialogTitle className="flex items-center gap-2 text-xl">
              <Star className="h-5 w-5 fill-yellow-500 text-yellow-500" />
              Favoritos
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[80vh] px-6 pb-6">
            <FavoritesTable />
          </ScrollArea>
        </DialogContent>
      </Dialog>

      <CollectionHistoryModal 
        open={historyOpen} 
        onOpenChange={setHistoryOpen} 
      />
    </>
  );
};

const Dashboard = () => {
  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex min-h-screen w-full overflow-x-hidden">
        <DashboardContent />
      </div>
    </SidebarProvider>
  );
};

export default Dashboard;
