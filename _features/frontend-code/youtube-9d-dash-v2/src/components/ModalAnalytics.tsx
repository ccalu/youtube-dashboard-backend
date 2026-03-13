import React from 'react';
import { Channel } from '@/services/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ColoredBadge } from '@/components/ui/colored-badge';
import {
  LayoutDashboard,
  BarChart3,
  Video,
  Stethoscope,
  MessageSquare,
} from 'lucide-react';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import {
  OverviewTab,
  MetricsTab,
  TopVideosTab,
  DiagnosticsTab,
  EngagementTab,
} from '@/components/analytics-tabs';

interface ModalAnalyticsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  canal: Channel | null;
}

export const ModalAnalytics: React.FC<ModalAnalyticsProps> = ({
  open,
  onOpenChange,
  canal,
}) => {
  if (!canal) return null;

  const cores = obterCorSubnicho(canal.subnicho);
  const isNosso = canal.tipo === 'nosso';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col w-[95vw] sm:w-auto">
        {/* Header */}
        <DialogHeader className="flex-shrink-0">
          <div 
            className="flex items-center gap-3 pb-2 border-b-2" 
            style={{ borderBottomColor: cores.borda }}
          >
            <DialogTitle className="text-lg font-bold text-foreground">
              {canal.nome_canal}
            </DialogTitle>
            <div className="flex items-center gap-2">
              <ColoredBadge text={canal.subnicho} type="subnicho" />
              <Badge variant="outline" className="capitalize text-xs">
                {canal.tipo}
              </Badge>
            </div>
          </div>
        </DialogHeader>

        {/* Tabs Content */}
        <Tabs defaultValue="overview" className="flex-1 overflow-hidden flex flex-col">
          <TabsList 
            className={`grid w-full ${isNosso ? 'grid-cols-5' : 'grid-cols-4'} flex-shrink-0`}
          >
            <TabsTrigger value="overview" className="text-xs">
              <LayoutDashboard className="h-3 w-3 mr-1 max-sm:mr-0" />
              <span className="max-sm:hidden">Visão Geral</span>
            </TabsTrigger>
            <TabsTrigger value="metrics" className="text-xs">
              <BarChart3 className="h-3 w-3 mr-1 max-sm:mr-0" />
              <span className="max-sm:hidden">Métricas</span>
            </TabsTrigger>
            <TabsTrigger value="videos" className="text-xs">
              <Video className="h-3 w-3 mr-1 max-sm:mr-0" />
              <span className="max-sm:hidden">Top Vídeos</span>
            </TabsTrigger>
            <TabsTrigger value="diagnostics" className="text-xs">
              <Stethoscope className="h-3 w-3 mr-1 max-sm:mr-0" />
              <span className="max-sm:hidden">Diagnóstico</span>
            </TabsTrigger>
            {isNosso && (
              <TabsTrigger value="engagement" className="text-xs">
                <MessageSquare className="h-3 w-3 mr-1 max-sm:mr-0" />
                <span className="max-sm:hidden">Engajamento</span>
              </TabsTrigger>
            )}
          </TabsList>

          <div className="flex-1 overflow-y-auto mt-4 pr-1">
            <TabsContent value="overview" className="mt-0">
              <OverviewTab canal={canal} />
            </TabsContent>

            <TabsContent value="metrics" className="mt-0">
              <MetricsTab canal={canal} />
            </TabsContent>

            <TabsContent value="videos" className="mt-0">
              <TopVideosTab canal={canal} />
            </TabsContent>

            <TabsContent value="diagnostics" className="mt-0">
              <DiagnosticsTab canal={canal} />
            </TabsContent>

            {isNosso && (
              <TabsContent value="engagement" className="mt-0">
                <EngagementTab canal={canal} />
              </TabsContent>
            )}
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
