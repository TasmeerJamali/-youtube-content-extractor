// API Request/Response Types

export interface SearchRequest {
  idea: string;
  max_results?: number;
  content_types?: string[];
  language?: string;
  region?: string;
  published_after?: string;
  published_before?: string;
  min_duration?: number;
  max_duration?: number;
  include_transcripts?: boolean;
  include_comments?: boolean;
  api_key?: string;
}

export interface VideoResult {
  video_id: string;
  title: string;
  description: string;
  channel_title: string;
  channel_id: string;
  published_at: string;
  duration?: number;
  view_count: number;
  like_count?: number;
  comment_count?: number;
  thumbnail_url: string;
  relevance_score: number;
  quality_score: number;
  engagement_rate?: number;
  tags: string[];
  category?: string;
  transcript?: string;
  top_comments?: string[];
}

export interface SearchResponse {
  query_info: {
    original_idea: string;
    processed_keywords: string[];
    detected_content_types: string[];
    intent: string;
    confidence: number;
    search_terms_used: string[];
  };
  total_results: number;
  videos: VideoResult[];
  search_time_ms: number;
  quota_used: number;
  suggestions: string[];
}

export interface TrendingVideoResult {
  video_id: string;
  title: string;
  description: string;
  channel_title: string;
  channel_id: string;
  published_at: string;
  duration?: number;
  view_count: number;
  like_count?: number;
  comment_count?: number;
  thumbnail_url: string;
  category?: string;
  tags: string[];
  trending_score: number;
}

export interface TrendingResponse {
  region: string;
  category?: string;
  total_results: number;
  videos: TrendingVideoResult[];
  generated_at: string;
}

export interface TrendAnalysis {
  keyword: string;
  trend_score: number;
  search_volume: number;
  competition_level: string;
  related_topics: string[];
  content_opportunities: string[];
}

export interface ContentInsights {
  topic: string;
  total_videos: number;
  avg_view_count: number;
  avg_engagement_rate: number;
  top_creators: Array<{
    channel_id: string;
    channel_title: string;
    total_views: number;
    video_count: number;
  }>;
  content_gaps: string[];
  recommended_formats: string[];
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  services: {
    [serviceName: string]: {
      status: string;
      [key: string]: any;
    };
  };
  performance: {
    response_time_ms: number;
    memory_usage_mb: number;
    cpu_usage_percent: number;
  };
}

// UI Component Types

export interface SearchFormData extends SearchRequest {}

export interface FilterOptions {
  contentTypes: string[];
  languages: string[];
  regions: string[];
  durations: Array<{ label: string; min?: number; max?: number }>;
  publishedDateRanges: Array<{ label: string; value: string }>;
}

export interface VideoCardProps {
  video: VideoResult;
  onSelect?: (video: VideoResult) => void;
  showTranscript?: boolean;
  showComments?: boolean;
}

export interface SearchFiltersProps {
  filters: Partial<SearchRequest>;
  onChange: (filters: Partial<SearchRequest>) => void;
  onApply: () => void;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
  code?: string;
  canRetry?: boolean;
}

// Analytics Types

export interface TrendData {
  keyword: string;
  period: string;
  search_volume: number;
  competition_score: number;
  trending_score: number;
  growth_rate: number;
}

export interface ChannelAnalytics {
  channel_id: string;
  channel_title: string;
  subscriber_count: number;
  total_views: number;
  video_count: number;
  avg_views_per_video: number;
  engagement_rate: number;
  posting_frequency: number;
  content_categories: string[];
}

export interface ContentGap {
  topic: string;
  opportunity_score: number;
  current_competition: number;
  suggested_approach: string;
  estimated_difficulty: 'easy' | 'medium' | 'hard';
  potential_reach: number;
}

export interface CompetitorInsight {
  channel_id: string;
  strengths: string[];
  weaknesses: string[];
  content_strategies: string[];
  posting_patterns: {
    frequency: number;
    best_times: string[];
    content_types: string[];
  };
}

// Chart Data Types

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
  metadata?: any;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface ChartProps {
  data: ChartDataPoint[] | TimeSeriesDataPoint[];
  title?: string;
  description?: string;
  height?: number;
  width?: number;
  showLegend?: boolean;
  interactive?: boolean;
}

// Form Types

export interface FormFieldConfig {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'multiselect' | 'date' | 'checkbox' | 'textarea';
  required?: boolean;
  placeholder?: string;
  options?: Array<{ label: string; value: string | number }>;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: any) => string | null;
  };
}

export interface FormProps {
  fields: FormFieldConfig[];
  initialValues?: Record<string, any>;
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
  submitLabel?: string;
  cancelLabel?: string;
  isLoading?: boolean;
}

// Export/Import Types

export interface ExportOptions {
  format: 'json' | 'csv' | 'xlsx' | 'pdf';
  includeMetadata: boolean;
  includeAnalytics: boolean;
  includeCharts: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface ExportData {
  metadata: {
    exportedAt: string;
    query: string;
    totalResults: number;
    filters: Partial<SearchRequest>;
  };
  results: VideoResult[];
  analytics?: {
    trends: TrendAnalysis[];
    insights: ContentInsights;
  };
}

// Utility Types

export type SortDirection = 'asc' | 'desc';

export interface SortOption {
  field: keyof VideoResult;
  direction: SortDirection;
  label: string;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface FilterState {
  activeFilters: Record<string, any>;
  sortBy: SortOption;
  searchQuery: string;
}

// Theme and UI Types

export interface ThemeConfig {
  primaryColor: string;
  secondaryColor: string;
  backgroundColor: string;
  textColor: string;
  borderColor: string;
  fontFamily: string;
  borderRadius: string;
}

export interface NotificationConfig {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  persistent?: boolean;
  actions?: Array<{
    label: string;
    handler: () => void;
  }>;
}