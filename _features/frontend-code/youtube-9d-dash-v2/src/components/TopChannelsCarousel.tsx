// src/components/TopChannelsCarousel.tsx
import { useState, useEffect, useCallback } from 'react';
import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ChevronLeft, ChevronRight, Eye, UserPlus, ExternalLink } from 'lucide-react';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { formatNumber } from '@/utils/formatters';
import type { TopChannelsResponse } from '@/types/analysis';

interface TopChannelsCarouselProps {
  subniches: string[];
}

export function TopChannelsCarousel({ subniches }: TopChannelsCarouselProps) {
  const [currentSubnicheIndex, setCurrentSubnicheIndex] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState<7 | 15 | 30>(30);
  const queryClient = useQueryClient();

  const currentSubniche = subniches[currentSubnicheIndex] || '';

  const { data, isLoading } = useQuery<TopChannelsResponse>({
    queryKey: ['top-channels', currentSubniche, selectedPeriod],
    queryFn: () => apiService.getTopChannels(currentSubniche, selectedPeriod),
    enabled: !!currentSubniche,
    staleTime: 10 * 60 * 1000,
  });

  // Prefetch dos próximos subnichos para transições instantâneas
  useEffect(() => {
    const nextIndex = (currentSubnicheIndex + 1) % subniches.length;
    const prevIndex = currentSubnicheIndex > 0 ? currentSubnicheIndex - 1 : subniches.length - 1;
    
    if (subniches[nextIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['top-channels', subniches[nextIndex], selectedPeriod],
        queryFn: () => apiService.getTopChannels(subniches[nextIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
    
    if (subniches[prevIndex] && prevIndex !== nextIndex) {
      queryClient.prefetchQuery({
        queryKey: ['top-channels', subniches[prevIndex], selectedPeriod],
        queryFn: () => apiService.getTopChannels(subniches[prevIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

  // ⚡ OTIMIZAÇÃO: Prefetch no hover das setas
  const handlePreviousHover = useCallback(() => {
    const prevIndex = currentSubnicheIndex > 0 ? currentSubnicheIndex - 1 : subniches.length - 1;
    if (subniches[prevIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['top-channels', subniches[prevIndex], selectedPeriod],
        queryFn: () => apiService.getTopChannels(subniches[prevIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

  const handleNextHover = useCallback(() => {
    const nextIndex = (currentSubnicheIndex + 1) % subniches.length;
    if (subniches[nextIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['top-channels', subniches[nextIndex], selectedPeriod],
        queryFn: () => apiService.getTopChannels(subniches[nextIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

  // ⚡ OTIMIZAÇÃO: useCallback para evitar recriação de funções
  const handlePrevious = useCallback(() => {
    setCurrentSubnicheIndex((prev) => (prev > 0 ? prev - 1 : subniches.length - 1));
  }, [subniches.length]);

  const handleNext = useCallback(() => {
    setCurrentSubnicheIndex((prev) => (prev < subniches.length - 1 ? prev + 1 : 0));
  }, [subniches.length]);

  const getMedalEmoji = useCallback((position: number): string => {
    if (position === 1) return '🥇';
    if (position === 2) return '🥈';
    if (position === 3) return '🥉';
    return '';
  }, []);

  const handleOpenChannel = useCallback((url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  }, []);

  const cores = currentSubniche ? obterCorSubnicho(currentSubniche) : null;

  return (
    <Card>
      <CardHeader className="p-3 sm:p-6">
        {/* Desktop Layout */}
        <div className="hidden sm:grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <div className="justify-self-start">
            <CardTitle className="flex items-center gap-2">
              <span className="text-xl">👑</span>
              Top 5 Canais
            </CardTitle>
          </div>

          {currentSubniche && cores && (
            <div className="flex items-center justify-center gap-3 justify-self-center">
              <Button
                variant="ghost"
                size="sm"
                onClick={handlePrevious}
                onMouseEnter={handlePreviousHover}
                disabled={subniches.length <= 1}
                className="h-8 w-8 p-0 rounded-full hover:bg-muted transition-transform hover:scale-110"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              
              <div
                className="px-4 py-1.5 rounded-full font-medium text-sm text-white transition-all duration-300 animate-fade-in"
                style={{ backgroundColor: cores.borda }}
              >
                {currentSubniche}
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={handleNext}
                onMouseEnter={handleNextHover}
                disabled={subniches.length <= 1}
                className="h-8 w-8 p-0 rounded-full hover:bg-muted transition-transform hover:scale-110"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>

              <span className="text-xs text-muted-foreground">
                {currentSubnicheIndex + 1}/{subniches.length}
              </span>
            </div>
          )}

          <div className="flex gap-2 justify-self-end">
            <Button
              variant={selectedPeriod === 7 ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedPeriod(7)}
            >
              7 dias
            </Button>
            <Button
              variant={selectedPeriod === 15 ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedPeriod(15)}
            >
              15 dias
            </Button>
            <Button
              variant={selectedPeriod === 30 ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedPeriod(30)}
            >
              30 dias
            </Button>
          </div>
        </div>

        {/* Mobile Layout */}
        <div className="sm:hidden space-y-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <span className="text-lg">👑</span>
            Top 5 Canais
          </CardTitle>

          {currentSubniche && cores && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handlePrevious}
                  disabled={subniches.length <= 1}
                  className="h-7 w-7 p-0 rounded-full"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                
                <div
                  className="px-3 py-1 rounded-full font-medium text-xs text-white"
                  style={{ backgroundColor: cores.borda }}
                >
                  {currentSubniche}
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleNext}
                  disabled={subniches.length <= 1}
                  className="h-7 w-7 p-0 rounded-full"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <span className="text-xs text-muted-foreground">
                  {currentSubnicheIndex + 1}/{subniches.length}
                </span>
              </div>

              <div className="flex gap-1">
                <Button
                  variant={selectedPeriod === 7 ? 'default' : 'outline'}
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => setSelectedPeriod(7)}
                >
                  7d
                </Button>
                <Button
                  variant={selectedPeriod === 15 ? 'default' : 'outline'}
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => setSelectedPeriod(15)}
                >
                  15d
                </Button>
                <Button
                  variant={selectedPeriod === 30 ? 'default' : 'outline'}
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => setSelectedPeriod(30)}
                >
                  30d
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent key={currentSubniche} className="p-3 sm:p-6 transition-all duration-300 ease-in-out animate-fade-in">

        {isLoading ? (
          <div className="space-y-3 sm:space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-20 sm:h-24 w-full" />
            ))}
          </div>
        ) : data && data.channels.length > 0 ? (
          <div className="space-y-3 sm:space-y-4">
            {data.channels.map((channel, index) => {
              const position = index + 1;
              const medal = getMedalEmoji(position);
              const channelName =
                channel.nome_canal || channel.canais_monitorados?.nome_canal || 'Canal';
              const channelUrl =
                channel.url_canal || channel.canais_monitorados?.url_canal || '';

              return (
                <Card 
                  key={channel.canal_id} 
                  className="hover:shadow-md transition-all duration-300 border-2"
                  style={{
                    backgroundColor: cores?.borda,
                    borderColor: cores?.borda,
                  }}
                >
                  <CardContent className="p-3 sm:p-4">
                    <div className="flex items-center justify-between gap-2 sm:gap-4">
                      <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
                        <span className="text-xl sm:text-2xl font-bold flex-shrink-0 text-white">
                          {medal ? medal : `${position}º`}
                        </span>

                        <div className="flex-1 min-w-0 space-y-1 sm:space-y-2">
                          <div className="font-semibold text-sm sm:text-base truncate text-white">
                            {channelName}
                          </div>

                          <div className="flex flex-wrap items-center gap-x-3 sm:gap-x-4 gap-y-1 text-xs sm:text-sm">
                            <div className="flex items-center gap-1">
                              <Eye className="h-3 w-3 sm:h-4 sm:w-4 text-white/80" />
                              <span className="font-semibold text-white">{formatNumber(channel.views_30d)}</span>
                              <span className="text-white/70 text-[10px] sm:text-xs hidden sm:inline">views</span>
                            </div>

                            <div className="flex items-center gap-1">
                              <UserPlus className="h-3 w-3 sm:h-4 sm:w-4 text-white/80" />
                              <span className="font-semibold text-white">+{formatNumber(channel.subscribers_gained_30d)}</span>
                              <span className="text-white/70 text-[10px] sm:text-xs hidden sm:inline">inscritos</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleOpenChannel(channelUrl)}
                        disabled={!channelUrl}
                        className="flex-shrink-0 bg-white/20 border-white/30 text-white hover:bg-white/30 h-8 w-8 sm:h-9 sm:w-9 p-0"
                      >
                        <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Nenhum canal encontrado para {currentSubniche} nos últimos {selectedPeriod} dias.
          </div>
        )}

        {data && data.channels.length > 0 && (
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Baseado nas views dos últimos {selectedPeriod} dias
          </div>
        )}
      </CardContent>
    </Card>
  );
}
