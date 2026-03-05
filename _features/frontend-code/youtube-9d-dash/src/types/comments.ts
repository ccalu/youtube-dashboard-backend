// Interfaces para o sistema de engajamento de canais

export interface EngagementSummary {
  total_comments: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  actionable_count: number;
  problems_count: number;
}

export interface CommentData {
  comment_id: string;
  author_name: string;
  comment_text_pt: string;
  comment_text_original?: string;
  is_translated: boolean;
  original_language?: string;
  like_count: number;
  insight_text: string;
  problem_type?: string;
  suggested_action?: string;
  published_at: string;
}

export interface VideoEngagement {
  video_id: string;
  video_title: string;
  published_days_ago: number;
  views: number;
  total_comments: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  has_problems: boolean;
  problem_count: number;
  sentiment_score: number;
  positive_comments: CommentData[];
  negative_comments: CommentData[];
  neutral_comments: CommentData[];
  all_comments?: CommentData[];  // API retorna comentários unificados aqui
}

export interface ProblemData {
  video_title: string;
  author: string;
  text_pt: string;
  specific_issue: string;
  suggested_action: string;
}

export interface ProblemsGrouped {
  audio: ProblemData[];
  video: ProblemData[];
  content: ProblemData[];
  technical: ProblemData[];
}

export interface PaginationData {
  page: number;
  limit: number;
  total_videos: number;
  total_pages: number;
}

export interface EngagementData {
  summary: EngagementSummary;
  videos: VideoEngagement[];
  problems_grouped: ProblemsGrouped;
  pagination: PaginationData;
}
