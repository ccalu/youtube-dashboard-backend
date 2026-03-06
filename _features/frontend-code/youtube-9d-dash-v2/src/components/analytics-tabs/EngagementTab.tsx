import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiService, Channel } from '@/services/api';
import { EngagementData, VideoEngagement, CommentData, ProblemData } from '@/types/comments';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  Clock,
  User,
  Heart,
  Languages,
  Lightbulb,
  Volume2,
  Video,
  FileText,
  Wrench,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { formatNumber } from '@/utils/formatters';

interface EngagementTabProps {
  canal: Channel;
}

// Performance color based on views (used for border only, no labels)
const getPerformanceColor = (views: number | null | undefined): string => {
  const v = views ?? 0;
  if (v >= 20000) return '#0d9488';
  if (v >= 10000) return '#10b981';
  if (v >= 5000) return '#eab308';
  return '#fb923c';
};

const CommentCard: React.FC<{ comment: CommentData }> = ({ comment }) => {
  return (
    <div className="p-3 rounded-lg border border-cyan-500/30 bg-cyan-500/5">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <User className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <span className="font-medium text-sm text-foreground truncate">
            {comment.author_name || 'Usuário'}
          </span>
          {comment.is_translated && (
            <Badge variant="outline" className="text-xs py-0 flex-shrink-0">
              <Languages className="h-3 w-3 mr-1" />
              Traduzido
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground flex-shrink-0">
          <Heart className="h-3 w-3" />
          <span className="w-6 text-right">{comment.like_count}</span>
        </div>
      </div>
      
      <p className="text-sm text-foreground mb-2 leading-relaxed font-medium">
        {comment.comment_text_pt || comment.comment_text_original || 'Comentário não disponível'}
      </p>
      
      {comment.insight_text && (
        <div className="flex items-start gap-2 mt-2 p-2 bg-muted/50 rounded">
          <Lightbulb className="h-4 w-4 text-yellow-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-muted-foreground">{comment.insight_text}</p>
        </div>
      )}
      
      {comment.suggested_action && (
        <div className="mt-2 text-xs text-primary">
          💡 Ação: {comment.suggested_action}
        </div>
      )}
    </div>
  );
};

const ProblemCard: React.FC<{ problem: ProblemData }> = ({ problem }) => {
  return (
    <div className="p-3 rounded-lg border border-orange-500/30 bg-orange-500/5">
      <div className="flex items-start gap-2 mb-2">
        <AlertTriangle className="h-4 w-4 text-orange-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-foreground">{problem.specific_issue}</p>
          <p className="text-xs text-muted-foreground mt-1">
            Vídeo: {problem.video_title}
          </p>
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-2">
        "{problem.text_pt}"
      </p>
      <p className="text-xs text-muted-foreground">— {problem.author}</p>
      {problem.suggested_action && (
        <div className="mt-2 p-2 bg-muted/50 rounded text-xs text-primary">
          💡 Sugestão: {problem.suggested_action}
        </div>
      )}
    </div>
  );
};

const VideoAccordion: React.FC<{ video: VideoEngagement }> = ({ video }) => {
  const performanceColor = getPerformanceColor(video.views);
  const [commentPage, setCommentPage] = useState(1);
  const commentsPerPage = 10;

  // Usar all_comments da API (preferencial) ou combinar arrays legados
  const allComments = video.all_comments ?? [
    ...video.positive_comments,
    ...video.negative_comments,
    ...(video.neutral_comments ?? [])
  ];
  
  // Thumbnail do video
  const thumbnailUrl = `https://i.ytimg.com/vi/${video.video_id}/mqdefault.jpg`;

  // Get paginated comments
  const getPaginatedComments = (comments: CommentData[], page: number) => {
    const start = (page - 1) * commentsPerPage;
    return comments.slice(start, start + commentsPerPage);
  };

  const getTotalPages = (count: number) => Math.ceil(count / commentsPerPage);

  return (
    <AccordionItem 
      value={video.video_id} 
      className="border rounded-lg mb-2 overflow-hidden border-l-4"
      style={{ borderLeftColor: performanceColor }}
    >
      <AccordionTrigger className="px-4 py-3 hover:bg-muted/50">
        <div className="flex items-center gap-3 flex-1 text-left">
          {/* Thumbnail */}
          <img 
            src={thumbnailUrl}
            alt={video.video_title || 'Vídeo'}
            className="w-16 h-10 object-cover rounded flex-shrink-0"
            loading="lazy"
          />
          <div className="flex-1 min-w-0">
            <p className="font-medium text-sm text-foreground truncate max-w-[180px]">
              {video.video_title || 'Vídeo sem título'}
            </p>
            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {video.published_days_ago}d atrás
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Badge único de comentários */}
            <Badge variant="outline" className="text-cyan-500 border-cyan-500/50">
              <MessageSquare className="h-3 w-3 mr-1" />
              {video.total_comments}
            </Badge>
            {video.has_problems && (
              <Badge variant="outline" className="text-orange-500 border-orange-500/50">
                <AlertTriangle className="h-3 w-3 mr-1" />
                {video.problem_count}
              </Badge>
            )}
          </div>
        </div>
      </AccordionTrigger>
      <AccordionContent className="px-4 pb-4">
        {/* Lista unificada de comentários */}
        {allComments.length > 0 ? (
          <>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {getPaginatedComments(allComments, commentPage).map((comment) => (
                <CommentCard key={comment.comment_id} comment={comment} />
              ))}
            </div>
            {getTotalPages(allComments.length) > 1 && (
              <div className="flex items-center justify-center gap-2 pt-2 border-t mt-2">
                <Button
                  variant="outline"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => setCommentPage(p => Math.max(1, p - 1))}
                  disabled={commentPage <= 1}
                >
                  <ChevronLeft className="h-3 w-3" />
                </Button>
                <span className="text-xs text-muted-foreground">
                  {commentPage} / {getTotalPages(allComments.length)}
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  className="h-6 w-6"
                  onClick={() => setCommentPage(p => Math.min(getTotalPages(allComments.length), p + 1))}
                  disabled={commentPage >= getTotalPages(allComments.length)}
                >
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">
            Nenhum comentário encontrado
          </p>
        )}
      </AccordionContent>
    </AccordionItem>
  );
};

const getProblemIcon = (category: string) => {
  switch (category) {
    case 'audio': return <Volume2 className="h-4 w-4" />;
    case 'video': return <Video className="h-4 w-4" />;
    case 'content': return <FileText className="h-4 w-4" />;
    case 'technical': return <Wrench className="h-4 w-4" />;
    default: return <AlertTriangle className="h-4 w-4" />;
  }
};

const getProblemLabel = (category: string) => {
  switch (category) {
    case 'audio': return 'Áudio';
    case 'video': return 'Vídeo';
    case 'content': return 'Conteúdo';
    case 'technical': return 'Técnico';
    default: return category;
  }
};

export const EngagementTab: React.FC<EngagementTabProps> = ({ canal }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const limit = 10;

  const { data, isLoading, error } = useQuery<EngagementData>({
    queryKey: ['channel-engagement', canal.id, currentPage],
    queryFn: () => apiService.getChannelEngagement(canal.id, currentPage, limit),
    staleTime: 5 * 60 * 1000,
  });

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const handleNextPage = () => {
    if (data?.pagination && currentPage < data.pagination.total_pages) {
      setCurrentPage(prev => prev + 1);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="pt-4">
                <Skeleton className="h-4 w-20 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-4">
            <Skeleton className="h-4 w-40 mb-4" />
            <div className="space-y-2">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-4">
          <div className="text-center py-8">
            <AlertTriangle className="h-10 w-10 mx-auto text-orange-500 mb-3" />
            <p className="text-foreground font-medium">
              Dados de engajamento temporariamente indisponíveis
            </p>
            <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
              A análise de comentários está sendo processada. 
              Tente novamente em alguns minutos.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="pt-4">
          <div className="text-center py-8">
            <MessageSquare className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
            <p className="text-muted-foreground">
              Nenhum dado de engajamento disponível
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { summary, videos, problems_grouped, pagination } = data;
  const totalProblems = Object.values(problems_grouped).flat().length;

  // Sort videos by publication date (most recent first)
  const sortedVideos = [...videos].sort((a, b) => {
    return a.published_days_ago - b.published_days_ago;
  });

  return (
    <div className="space-y-4 fade-in">
      {/* Summary Cards - Simplified: only Total and Action Needed */}
      <div className="grid grid-cols-2 gap-3">
        <Card className="border-0" style={{ backgroundColor: '#3B82F65E' }}>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-blue-200 mb-1">
              <MessageSquare className="h-4 w-4" />
              <span className="text-xs">Total de Comentários</span>
            </div>
            <p className="text-xl font-bold text-white">
              {formatNumber(summary.total_comments)}
            </p>
          </CardContent>
        </Card>

        <Card className="border-0" style={{ backgroundColor: '#F59E0B5E' }}>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-yellow-200 mb-1">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-xs">Ação Necessária</span>
            </div>
            <p className="text-xl font-bold text-white">
              {summary.actionable_count}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Videos Accordion */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Video className="h-4 w-4" />
              Comentários por Vídeo
            </CardTitle>
            {pagination && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  Página {pagination.page} de {pagination.total_pages}
                </span>
                <div className="flex items-center gap-1">
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-7 w-7"
                    onClick={handlePreviousPage}
                    disabled={currentPage <= 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-7 w-7"
                    onClick={handleNextPage}
                    disabled={currentPage >= pagination.total_pages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
          {pagination && (
            <p className="text-xs text-muted-foreground">
              Total: {pagination.total_videos} vídeos
            </p>
          )}
        </CardHeader>
        <CardContent>
          {sortedVideos.length > 0 ? (
            <Accordion type="single" collapsible className="w-full">
              {sortedVideos.map((video) => (
                <VideoAccordion key={video.video_id} video={video} />
              ))}
            </Accordion>
          ) : (
            <div className="text-center py-6">
              <MessageSquare className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-muted-foreground">Nenhum vídeo com comentários</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Problems Grouped */}
      {totalProblems > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              Problemas Detectados ({totalProblems})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="audio" className="w-full">
              <TabsList className="grid w-full grid-cols-4 mb-3">
                {(['audio', 'video', 'content', 'technical'] as const).map((category) => (
                  <TabsTrigger 
                    key={category} 
                    value={category}
                    className="text-xs"
                    disabled={problems_grouped[category].length === 0}
                  >
                    {getProblemIcon(category)}
                    <span className="ml-1 hidden sm:inline">{getProblemLabel(category)}</span>
                    <Badge variant="secondary" className="ml-1 text-xs">
                      {problems_grouped[category].length}
                    </Badge>
                  </TabsTrigger>
                ))}
              </TabsList>
              {(['audio', 'video', 'content', 'technical'] as const).map((category) => (
                <TabsContent key={category} value={category} className="space-y-2 max-h-64 overflow-y-auto">
                  {problems_grouped[category].length > 0 ? (
                    problems_grouped[category].map((problem, index) => (
                      <ProblemCard key={index} problem={problem} />
                    ))
                  ) : (
                    <div className="text-center py-6">
                      <CheckCircle className="h-8 w-8 mx-auto text-green-500 mb-2" />
                      <p className="text-muted-foreground">
                        Nenhum problema de {getProblemLabel(category).toLowerCase()} detectado
                      </p>
                    </div>
                  )}
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
