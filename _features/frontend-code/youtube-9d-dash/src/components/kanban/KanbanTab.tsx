/**
 * Main Kanban Tab Component
 * Hierarchical view matching Tabela tab style with Monetizados/Não Monetizados sections
 */

import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Kanban } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { kanbanApiService } from '@/services/kanbanApi';
import { supabase } from '@/integrations/supabase/client';
import { KanbanSectionCard } from './KanbanSectionCard';
import { KanbanBoardModal } from './KanbanBoardModal';
import type { KanbanChannel, KanbanSection, KanbanStructure } from '@/types/kanban';

export const KanbanTab = () => {
  const [selectedChannel, setSelectedChannel] = useState<KanbanChannel | null>(null);
  const [boardModalOpen, setBoardModalOpen] = useState(false);

  // Fetch structure with moderate caching - refreshes on mount/focus to stay in sync
  const { data: rawData, isLoading, isError, refetch } = useQuery({
    queryKey: ['kanban-structure'],
    queryFn: () => kanbanApiService.getStructure(),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
  });

  // Helper to normalize strings for comparison
  const normalizeStr = (s: string) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();

  // Excluded subniches (same rules as Tabela)
  const EXCLUDED_SUBNICHOS = ['historias aleatorias', 'contos familiares'];

  // Normalize backend data to ensure correct section placement
  const data: KanbanStructure | undefined = useMemo(() => {
    if (!rawData) return rawData;

    const monetizadosSubnichos = { ...(rawData.monetizados?.subnichos ?? {}) };
    const naoMonetizadosSubnichos = { ...(rawData.nao_monetizados?.subnichos ?? {}) };

    // Move "Desmonetizados" from monetizados to nao_monetizados
    Object.keys(monetizadosSubnichos).forEach((subnicho) => {
      const normalized = normalizeStr(subnicho);
      if (normalized === 'desmonetizado' || normalized === 'desmonetizados') {
        const data = monetizadosSubnichos[subnicho];
        // Merge into nao_monetizados
        if (naoMonetizadosSubnichos[subnicho]) {
          const existing = naoMonetizadosSubnichos[subnicho];
          const mergedCanais = [...(existing.canais ?? []), ...(data.canais ?? [])];
          // Remove duplicates by id
          const uniqueCanais = Array.from(new Map(mergedCanais.map(c => [c.id, c])).values());
          naoMonetizadosSubnichos[subnicho] = { ...existing, canais: uniqueCanais, total: uniqueCanais.length };
        } else {
          naoMonetizadosSubnichos[subnicho] = data;
        }
        delete monetizadosSubnichos[subnicho];
      }
    });

    // Move "Monetizados" from nao_monetizados to monetizados
    Object.keys(naoMonetizadosSubnichos).forEach((subnicho) => {
      const normalized = normalizeStr(subnicho);
      if (normalized === 'monetizados' || normalized === 'monetizado') {
        const data = naoMonetizadosSubnichos[subnicho];
        // Merge into monetizados
        if (monetizadosSubnichos[subnicho]) {
          const existing = monetizadosSubnichos[subnicho];
          const mergedCanais = [...(existing.canais ?? []), ...(data.canais ?? [])];
          const uniqueCanais = Array.from(new Map(mergedCanais.map(c => [c.id, c])).values());
          monetizadosSubnichos[subnicho] = { ...existing, canais: uniqueCanais, total: uniqueCanais.length };
        } else {
          monetizadosSubnichos[subnicho] = data;
        }
        delete naoMonetizadosSubnichos[subnicho];
      }
    });

    // Remove excluded subniches
    Object.keys(monetizadosSubnichos).forEach((subnicho) => {
      if (EXCLUDED_SUBNICHOS.includes(normalizeStr(subnicho))) {
        delete monetizadosSubnichos[subnicho];
      }
    });
    Object.keys(naoMonetizadosSubnichos).forEach((subnicho) => {
      if (EXCLUDED_SUBNICHOS.includes(normalizeStr(subnicho))) {
        delete naoMonetizadosSubnichos[subnicho];
      }
    });

    // Recalculate totals
    const calcSectionTotal = (subnichos: typeof monetizadosSubnichos) =>
      Object.values(subnichos).reduce((sum, sub) => sum + (sub.canais?.length ?? sub.total ?? 0), 0);

    return {
      ...rawData,
      monetizados: {
        ...rawData.monetizados,
        subnichos: monetizadosSubnichos,
        total: calcSectionTotal(monetizadosSubnichos),
      },
      nao_monetizados: {
        ...rawData.nao_monetizados,
        subnichos: naoMonetizadosSubnichos,
        total: calcSectionTotal(naoMonetizadosSubnichos),
      },
    };
  }, [rawData]);

  // 
  // FIX: backend do Kanban nem sempre devolve `lingua`.
  // Para garantir bandeiras corretas, buscamos `lingua` direto do Supabase
  // e “enriquecemos” a estrutura antes de renderizar.
  //
  const channelIds = useMemo(() => {
    const ids: number[] = [];

    const pushSection = (section?: KanbanSection) => {
      if (!section?.subnichos) return;
      Object.values(section.subnichos).forEach((sub) => {
        sub.canais?.forEach((c) => ids.push(c.id));
      });
    };

    pushSection(data?.monetizados);
    pushSection(data?.nao_monetizados);

    return Array.from(new Set(ids));
  }, [data]);

  const { data: languagesById } = useQuery({
    queryKey: ['kanban-channel-languages', channelIds],
    enabled: channelIds.length > 0,
    staleTime: 1000 * 60 * 60, // 1h
    queryFn: async () => {
      const { data, error } = await supabase
        .from('canais_monitorados')
        .select('id, lingua')
        .in('id', channelIds);

      if (error) throw error;
      const map: Record<number, string | null> = {};
      (data ?? []).forEach((row) => {
        map[row.id] = row.lingua ?? null;
      });
      return map;
    },
  });

  const enrichedData: KanbanStructure | undefined = useMemo(() => {
    if (!data) return data;
    if (!languagesById) return data;

    const enrichSection = (section: KanbanSection): KanbanSection => {
      const subnichos = section.subnichos ?? {};
      return {
        ...section,
        subnichos: Object.fromEntries(
          Object.entries(subnichos).map(([subnicho, subData]) => {
            const canais = (subData.canais ?? []).map((c) => ({
              ...c,
              lingua: (languagesById[c.id] ?? (c as any).lingua ?? '') as string,
            }));
            return [subnicho, { ...subData, canais }];
          })
        ),
      };
    };

    return {
      ...data,
      monetizados: enrichSection(data.monetizados),
      nao_monetizados: enrichSection(data.nao_monetizados),
    };
  }, [data, languagesById]);

  const handleChannelClick = (canal: KanbanChannel) => {
    setSelectedChannel(canal);
    setBoardModalOpen(true);
  };

  const handleModalClose = () => {
    setBoardModalOpen(false);
    setSelectedChannel(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Kanban className="h-6 w-6 text-primary" />
            <h2 className="text-xl font-bold text-foreground">Kanban</h2>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-[200px] rounded-lg" />
          <Skeleton className="h-[200px] rounded-lg" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-muted-foreground">Erro ao carregar Kanban</p>
        <Button variant="outline" onClick={() => refetch()}>
          Tentar novamente
        </Button>
      </div>
    );
  }

  const totalMonetizados = enrichedData?.monetizados?.total || 0;
  const totalNaoMonetizados = enrichedData?.nao_monetizados?.total || 0;

  return (
    <div className="space-y-6">
      {/* Header - no refresh button, uses page-level refresh */}
      <div className="flex items-center gap-3">
        <Kanban className="h-6 w-6 text-primary" />
        <div>
          <h2 className="text-xl font-bold text-foreground">Kanban</h2>
          <p className="text-sm text-muted-foreground">
            {totalMonetizados + totalNaoMonetizados} canais • Gerencie status e notas
          </p>
        </div>
      </div>

      {/* Section Cards */}
      {/* items-start evita que um card “estique” e pareça abrir junto do outro */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Monetizados - gradient green card */}
        {enrichedData?.monetizados && (
          <KanbanSectionCard
            key="kanban-monetizados"
            title="MONETIZADOS"
            emoji="💰"
            section={enrichedData.monetizados}
            onChannelClick={handleChannelClick}
            accentColor="#22C55E"
            isMonetized
            gradientFrom="#4ADE80"
            gradientTo="#16A34A"
          />
        )}

        {/* Não Monetizados - gradient red card */}
        {enrichedData?.nao_monetizados && (
          <KanbanSectionCard
            key="kanban-nao-monetizados"
            title="NÃO MONETIZADOS"
            emoji="⛔"
            section={enrichedData.nao_monetizados}
            onChannelClick={handleChannelClick}
            accentColor="#DC2626"
            isMonetized={false}
            gradientFrom="#F87171"
            gradientTo="#B91C1C"
          />
        )}
      </div>

      {/* Board Modal */}
      {selectedChannel && (
        <KanbanBoardModal
          key={selectedChannel.id}
          canalId={selectedChannel.id}
          open={boardModalOpen}
          onOpenChange={(open) => {
            if (!open) handleModalClose();
          }}
          onStatusChanged={() => refetch()}
        />
      )}
    </div>
  );
};
