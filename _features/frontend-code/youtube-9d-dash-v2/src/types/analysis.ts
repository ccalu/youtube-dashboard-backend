// src/types/analysis.ts
// Tipos para as novas features de análise

export interface Keyword {
  keyword: string;
  frequency: number;
  avg_views: number;
  video_count: number;
}

export interface KeywordsResponse {
  period_days: number;
  total: number;
  keywords: Keyword[];
}

export interface TitlePattern {
  pattern_structure: string;
  pattern_description: string;
  example_title: string;
  avg_views: number;
  video_count: number;
}

export interface TitlePatternsResponse {
  subniche: string;
  period_days: number;
  total: number;
  patterns: TitlePattern[];
}

export interface TopChannel {
  canal_id: number;
  nome_canal: string;
  url_canal: string;
  views_30d: number;
  subscribers_gained_30d: number;
  subscribers_previous_month?: number;
  growth_percentage?: number;
  rank_position: number;
  canais_monitorados?: {
    nome_canal: string;
    url_canal: string;
  };
}

export interface TopChannelsResponse {
  subniche: string;
  total: number;
  channels: TopChannel[];
}

export interface SubnichesResponse {
  total: number;
  subniches: string[];
}

export interface TopVideo {
  video_id: string;
  titulo: string;
  canal_nome: string;
  views_7d: number;
  subscribers_gained_7d: number;
  url_video: string;
  subnicho?: string;
}

export interface SubnichePerformance {
  subniche: string;
  views_current_week: number;
  views_previous_week: number;
  growth_percentage: number;
  insight: string;
  total_views_7d?: number;
  video_count_7d?: number;
  total_views_30d?: number;
  video_count_30d?: number;
}

export interface Gap {
  type: "duration" | "frequency" | "engagement";
  priority: "high" | "medium";
  title: string;
  your_value: string;
  competitor_value: string;
  difference: number;
  impact_description: string;
  actions: string[];
  priority_text: string;
  effort: string;
  roi: string;
}

export interface RecommendedAction {
  priority: 'urgent' | 'high' | 'medium' | 'low';
  category?: string;
  title: string;
  description: string;
  action: string;
  impact?: string;
  effort?: string;
  avg_views?: number;
}

export interface SubnicheRecommendations {
  status: 'growing' | 'stable' | 'declining';
  growth_percentage: number;
  recommendations: RecommendedAction[];
}

export interface SubnicheTrend {
  subnicho: string;
  total_videos: number;
  avg_views: number;
  engagement_rate: number;
  trend_percent: number;
  period_days: number;
}

export interface SubnicheTrendsResponse {
  success: boolean;
  data: {
    '7d': SubnicheTrend[];
    '15d': SubnicheTrend[];
    '30d': SubnicheTrend[];
  };
  total_7d: number;
  total_15d: number;
  total_30d: number;
}
