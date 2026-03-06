// src/components/TitlePatternsCarousel.tsx
import { useState, useCallback, useEffect } from 'react';
import React from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ColoredBadge } from '@/components/ui/colored-badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ChevronLeft, ChevronRight, FileText, Eye, Video, Lightbulb } from 'lucide-react';
import { obterCorSubnicho } from '@/utils/subnichoColors';
import { formatNumber } from '@/utils/formatters';
import type { TitlePatternsResponse } from '@/types/analysis';

interface TitlePatternsCarouselProps {
  subniches: string[];
}

export function TitlePatternsCarousel({ subniches }: TitlePatternsCarouselProps) {
  const [currentSubnicheIndex, setCurrentSubnicheIndex] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState<7 | 15 | 30>(30);
  const queryClient = useQueryClient();

  const currentSubniche = subniches[currentSubnicheIndex] || '';

  const { data, isLoading } = useQuery<TitlePatternsResponse>({
    queryKey: ['title-patterns', currentSubniche, selectedPeriod],
    queryFn: () => apiService.getTitlePatterns(currentSubniche, selectedPeriod),
    enabled: !!currentSubniche,
    staleTime: 10 * 60 * 1000,
  });

  // ⚡ OTIMIZAÇÃO: Prefetch dos próximos subnichos
  useEffect(() => {
    const nextIndex = (currentSubnicheIndex + 1) % subniches.length;
    const prevIndex = currentSubnicheIndex > 0 ? currentSubnicheIndex - 1 : subniches.length - 1;
    
    if (subniches[nextIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['title-patterns', subniches[nextIndex], selectedPeriod],
        queryFn: () => apiService.getTitlePatterns(subniches[nextIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
    
    if (subniches[prevIndex] && prevIndex !== nextIndex) {
      queryClient.prefetchQuery({
        queryKey: ['title-patterns', subniches[prevIndex], selectedPeriod],
        queryFn: () => apiService.getTitlePatterns(subniches[prevIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

  // ⚡ OTIMIZAÇÃO: Prefetch no hover das setas
  const handlePreviousHover = useCallback(() => {
    const prevIndex = currentSubnicheIndex > 0 ? currentSubnicheIndex - 1 : subniches.length - 1;
    if (subniches[prevIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['title-patterns', subniches[prevIndex], selectedPeriod],
        queryFn: () => apiService.getTitlePatterns(subniches[prevIndex], selectedPeriod),
        staleTime: 10 * 60 * 1000,
      });
    }
  }, [currentSubnicheIndex, subniches, queryClient, selectedPeriod]);

  const handleNextHover = useCallback(() => {
    const nextIndex = (currentSubnicheIndex + 1) % subniches.length;
    if (subniches[nextIndex]) {
      queryClient.prefetchQuery({
        queryKey: ['title-patterns', subniches[nextIndex], selectedPeriod],
        queryFn: () => apiService.getTitlePatterns(subniches[nextIndex], selectedPeriod),
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
      <CardHeader className="p-3 sm:p-6">
        {/* Desktop Layout */}
        <div className="hidden sm:grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <div className="justify-self-start">
            <CardTitle className="flex items-center gap-2">
              <span className="text-xl">📝</span>
              Top 5 Padrões de Título
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
            <span className="text-lg">📝</span>
            Top 5 Padrões
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
      <CardContent key={`${currentSubniche}-${selectedPeriod}`} className="p-3 sm:p-6 animate-fade-in">

        {isLoading ? (
          <div className="space-y-3 sm:space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-28 sm:h-32 w-full" />
            ))}
          </div>
        ) : data && data.patterns.length > 0 ? (
          <div className="space-y-3 sm:space-y-4">
            {data.patterns.map((pattern, index) => {
              const position = index + 1;
              const medal = getMedalEmoji(position);
              const cores = obterCorSubnicho(currentSubniche);

              return (
                <Card
                  key={pattern.pattern_structure}
                  className="border-0"
                  style={{
                    backgroundColor: cores?.borda,
                  }}
                >
                  <CardContent className="p-3 sm:p-4">
                    <div className="flex items-start gap-2 sm:gap-3">
                      <span className="text-xl sm:text-2xl font-bold text-white">{medal || `${position}º`}</span>

                      <div className="flex-1 space-y-2 sm:space-y-3 min-w-0">
                        <div>
                          <div className="font-semibold text-sm sm:text-lg mb-1 text-white">
                            {pattern.pattern_structure}
                          </div>
                          <div className="text-xs sm:text-sm text-white/70">
                            {pattern.pattern_description}
                          </div>
                        </div>

                        <div className="flex items-start gap-2 bg-white/10 p-2 sm:p-3 rounded-md">
                          <Lightbulb className="h-3 w-3 sm:h-4 sm:w-4 text-white mt-0.5 flex-shrink-0" />
                          <div className="text-xs sm:text-sm text-white min-w-0">
                            <span className="font-medium">Ex:</span>{' '}
                            <span className="italic break-words">&quot;{pattern.example_title}&quot;</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 sm:gap-4 flex-wrap text-xs sm:text-sm">
                          <div className="flex items-center gap-1 sm:gap-2">
                            <Eye className="h-3 w-3 sm:h-4 sm:w-4 text-white/80" />
                            <span className="font-semibold text-white">
                              {formatNumber(pattern.avg_views)}
                            </span>
                            <span className="text-white/70 hidden sm:inline">views médias</span>
                          </div>

                          <div className="flex items-center gap-1 sm:gap-2">
                            <Video className="h-3 w-3 sm:h-4 sm:w-4 text-white/80" />
                            <span className="font-semibold text-white">{pattern.video_count}</span>
                            <span className="text-white/70 hidden sm:inline">vídeos</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Nenhum padrão encontrado para {currentSubniche} nos últimos {selectedPeriod} dias.
          </div>
        )}

        {data && data.patterns.length > 0 && (
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Padrões detectados automaticamente em vídeos com 50k+ views
          </div>
        )}
      </CardContent>
    </Card>
  );
}
