import axios from 'axios';
import { SearchRequest, SearchResponse, TrendAnalysis, ContentInsights, TrendingResponse } from '../types/api';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8001/api/v1',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any authentication headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 500) {
      console.error('Server error:', error.response.data);
    } else if (error.response?.status === 429) {
      console.error('Rate limit exceeded');
    }
    return Promise.reject(error);
  }
);

// Search API functions
export const searchContent = async (params: SearchRequest): Promise<SearchResponse> => {
  try {
    const response = await api.post('/search/', params);
    return response.data;
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
};

export const getSearchSuggestions = async (query: string): Promise<{ query: string; suggestions: string[] }> => {
  try {
    const response = await api.get('/search/suggestions', {
      params: { query, limit: 10 }
    });
    return response.data;
  } catch (error) {
    console.error('Suggestions error:', error);
    throw error;
  }
};

export const getTrendingVideos = async (params: {
  region?: string;
  category_id?: string;
  max_results?: number;
}): Promise<TrendingResponse> => {
  try {
    const queryParams = new URLSearchParams();
    if (params.region) queryParams.append('region', params.region);
    if (params.category_id) queryParams.append('category_id', params.category_id);
    if (params.max_results) queryParams.append('max_results', params.max_results.toString());
    
    const response = await api.get(`/trends/?${queryParams.toString()}`);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || 'Failed to fetch trending videos');
  }
};

export const getVideoCategories = async (region: string): Promise<Array<{id: string; title: string; assignable: boolean}>> => {
  try {
    const response = await api.get(`/trends/categories?region=${region}`);
    return response.data;
  } catch (error: any) {
    console.warn('Failed to get categories:', error);
    return [];
  }
};

// Analytics API functions
export const analyzeTrends = async (
  keywords: string[],
  region: string = 'US',
  timeframe: string = '30d'
): Promise<TrendAnalysis[]> => {
  try {
    const response = await api.get('/analytics/trends', {
      params: { 
        keywords: keywords.join(','), 
        region, 
        timeframe 
      }
    });
    return response.data;
  } catch (error) {
    console.error('Trend analysis error:', error);
    throw error;
  }
};

export const getContentInsights = async (
  topic: string,
  region: string = 'US',
  contentType?: string
): Promise<ContentInsights> => {
  try {
    const response = await api.get('/analytics/content-insights', {
      params: { topic, region, content_type: contentType }
    });
    return response.data;
  } catch (error) {
    console.error('Content insights error:', error);
    throw error;
  }
};

export const analyzeCompetitors = async (
  channels: string[],
  metrics: string[] = ['views', 'engagement', 'frequency']
): Promise<any> => {
  try {
    const response = await api.get('/analytics/competitor-analysis', {
      params: { 
        channels: channels.join(','),
        metrics: metrics.join(',')
      }
    });
    return response.data;
  } catch (error) {
    console.error('Competitor analysis error:', error);
    throw error;
  }
};

export const identifyContentGaps = async (
  niche: string,
  competitorChannels: string[] = [],
  region: string = 'US'
): Promise<any> => {
  try {
    const response = await api.get('/analytics/content-gaps', {
      params: { 
        niche, 
        competitor_channels: competitorChannels.join(','),
        region 
      }
    });
    return response.data;
  } catch (error) {
    console.error('Content gap analysis error:', error);
    throw error;
  }
};

// Health API functions
export const getHealthStatus = async (): Promise<any> => {
  try {
    const response = await api.get('/health/');
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

export const getServiceStatus = async (): Promise<any> => {
  try {
    const response = await api.get('/health/services');
    return response.data;
  } catch (error) {
    console.error('Service status error:', error);
    throw error;
  }
};

export const getMetrics = async (): Promise<any> => {
  try {
    const response = await api.get('/health/metrics');
    return response.data;
  } catch (error) {
    console.error('Metrics error:', error);
    throw error;
  }
};

// Utility functions
export const formatError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  } else if (error.response?.data?.message) {
    return error.response.data.message;
  } else if (error.message) {
    return error.message;
  } else {
    return 'An unexpected error occurred';
  }
};

export const isNetworkError = (error: any): boolean => {
  return !error.response || error.code === 'NETWORK_ERROR';
};

export const isRateLimitError = (error: any): boolean => {
  return error.response?.status === 429;
};

export const isServerError = (error: any): boolean => {
  return error.response?.status >= 500;
};

export default api;