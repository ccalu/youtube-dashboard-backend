// src/components/KeywordsRanking.tsx
import { useState, useEffect, useCallback } from 'react';
import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ChevronLeft, ChevronRight, Eye, Video, TrendingUp } from 'lucide-react';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { formatNumber } from '@/utils/formatters';
import type { KeywordsResponse } from '@/types/analysis';

interface KeywordsRankingProps {
  subniches: string[];
}

export function KeywordsRanking({ subniches }: KeywordsRankingProps) {
  const [currentSubnicheIndex, setCurrentSubnicheIndex] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState<7 | 15 | 30>(30);
  const queryClient = useQueryClient();

  const currentSubniche = subniches[currentSubnicheIndex] || '';

  const { data, isLoading } = useQuery<KeywordsResponse>({
    queryKey: ['keywords', currentSubniche, selectedPeriod],
    queryFn: () => apiService.getKeywords(currentSubniche, selectedPeriod),
    enabled: !!currentSubniche,
    staleTime: 10 * 60 * 1000,
  });

  // Prefetch dos próximos subnichos para transições instantâneas
  useEffect(() => {
    const nextIndex = (currentSubnicheIndex + 1) % subniches.length;
    const prevIndex = currentSubnicheIndex > 0 ? currentSubnicheIndex - 1 : subniches.length - 1;
    
    if (subniches[nextIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['keywords', subniches[nextIndex], selectedPeriod],
        queryFn: () => apiService.getKeywords(subniches[nextIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
    
    if (subniches[prevIndex] && prevIndex !== nextIndex) {
      queryClient.prefetchQuery({
        queryKey: ['keywords', subniches[prevIndex], selectedPeriod],
        queryFn: () => apiService.getKeywords(subniches[prevIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

  // ⚡ OTIMIZAÇÃO: Prefetch no hover das setas
  const handlePreviousHover = useCallback(() => {
    const prevIndex = currentSubnicheIndex > 0 ? currentSubnicheIndex - 1 : subniches.length - 1;
    if (subniches[prevIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['keywords', subniches[prevIndex], selectedPeriod],
        queryFn: () => apiService.getKeywords(subniches[prevIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

  const handleNextHover = useCallback(() => {
    const nextIndex = (currentSubnicheIndex + 1) % subniches.length;
    if (subniches[nextIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['keywords', subniches[nextIndex], selectedPeriod],
        queryFn: () => apiService.getKeywords(subniches[nextIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

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

  const cores = currentSubniche ? obterCorSubnicho(currentSubniche) : null;

  return (
    <Card>
      <CardHeader>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <div className="justify-self-start">
            <CardTitle className="flex items-center gap-2">
              <span className="text-xl">🔍</span>
              Top 10 Keywords
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
                style={{
                  backgroundColor: cores.borda,
                }}
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
      </CardHeader>
      
      <CardContent key={currentSubniche} className="transition-all duration-300 ease-in-out animate-fade-in">
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : data && data.keywords.length > 0 ? (
          <>
            {/* Desktop View */}
            <div className="hidden lg:block">
              <div className="space-y-2">
                {data.keywords.slice(0, 10).map((keyword, index) => {
                  const position = index + 1;
                  const medal = getMedalEmoji(position);

                  return (
                    <div
                      key={keyword.keyword}
                      className={`flex items-center justify-between p-3 rounded-lg border transition-colors hover:bg-muted/50 ${
                        position <= 3 ? 'bg-muted/30' : ''
                      }`}
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <div className="flex items-center gap-2 min-w-[80px]">
                          <span className="text-lg font-semibold text-muted-foreground">
                            {medal || `${position}º`}
                          </span>
                        </div>

                        <div className="flex-1">
                          <div className="font-medium text-lg capitalize">
                            {keyword.keyword}
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="flex items-center gap-2">
                            <Eye className="h-4 w-4 text-muted-foreground" />
                            <span className="font-semibold">
                              {formatNumber(keyword.avg_views)}
                            </span>
                            <span className="text-sm text-muted-foreground">views</span>
                          </div>

                          <div className="flex items-center gap-2">
                            <Video className="h-4 w-4 text-muted-foreground" />
                            <span className="font-semibold">{keyword.video_count}</span>
                            <span className="text-sm text-muted-foreground">vídeos</span>
                          </div>

                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-muted-foreground" />
                            <Badge variant="secondary">{keyword.frequency}x</Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Mobile View */}
            <div className="lg:hidden space-y-3">
              {data.keywords.slice(0, 10).map((keyword, index) => {
                const position = index + 1;
                const medal = getMedalEmoji(position);

                return (
                  <Card
                    key={keyword.keyword}
                    className={position <= 3 ? 'border-primary/50 bg-muted/30' : ''}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold text-muted-foreground">
                            {medal || `${position}º`}
                          </span>
                          <span className="font-medium text-lg capitalize">
                            {keyword.keyword}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <div className="flex flex-col">
                          <div className="flex items-center gap-1 text-muted-foreground mb-1">
                            <Eye className="h-3 w-3" />
                            <span className="text-xs">Views</span>
                          </div>
                          <span className="font-semibold">
                            {formatNumber(keyword.avg_views)}
                          </span>
                        </div>

                        <div className="flex flex-col">
                          <div className="flex items-center gap-1 text-muted-foreground mb-1">
                            <Video className="h-3 w-3" />
                            <span className="text-xs">Vídeos</span>
                          </div>
                          <span className="font-semibold">{keyword.video_count}</span>
                        </div>

                        <div className="flex flex-col">
                          <div className="flex items-center gap-1 text-muted-foreground mb-1">
                            <TrendingUp className="h-3 w-3" />
                            <span className="text-xs">Freq.</span>
                          </div>
                          <Badge variant="secondary" className="w-fit">
                            {keyword.frequency}x
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {data.total && (
              <div className="mt-4 text-center text-sm text-muted-foreground">
                Top 10 de {data.total} keywords analisadas (vídeos com 50k+ views)
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Nenhuma keyword encontrada para {currentSubniche} nos últimos {selectedPeriod} dias.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
