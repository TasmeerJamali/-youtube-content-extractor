import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowTrendingUpIcon,
  GlobeAltIcon,
  TagIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import VideoGrid from '../components/VideoGrid';
import LoadingSpinner from '../components/LoadingSpinner';
import { getTrendingVideos, getVideoCategories } from '../services/api';
import { TrendingResponse, VideoResult } from '../types/api';

const TrendsPage: React.FC = () => {
  const [selectedRegion, setSelectedRegion] = useState('US');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [maxResults, setMaxResults] = useState(50);

  // Trending videos query
  const {
    data: trendingData,
    isLoading: isLoadingTrending,
    error: trendingError,
    refetch: refetchTrending
  } = useQuery<TrendingResponse>({
    queryKey: ['trending', selectedRegion, selectedCategory, maxResults],
    queryFn: () => getTrendingVideos({
      region: selectedRegion,
      category_id: selectedCategory || undefined,
      max_results: maxResults
    }),
    retry: 2
  });

  // Video categories query
  const {
    data: categories,
    isLoading: isLoadingCategories
  } = useQuery({
    queryKey: ['categories', selectedRegion],
    queryFn: () => getVideoCategories(selectedRegion),
    retry: 2
  });

  // Handle errors
  useEffect(() => {
    if (trendingError) {
      toast.error(`Failed to load trending videos: ${(trendingError as any)?.message || 'Unknown error'}`);
    }
  }, [trendingError]);

  const regions = [
    { code: 'US', name: 'United States' },
    { code: 'GB', name: 'United Kingdom' },
    { code: 'CA', name: 'Canada' },
    { code: 'AU', name: 'Australia' },
    { code: 'DE', name: 'Germany' },
    { code: 'FR', name: 'France' },
    { code: 'JP', name: 'Japan' },
    { code: 'KR', name: 'South Korea' },
    { code: 'IN', name: 'India' },
    { code: 'BR', name: 'Brazil' }
  ];

  const handleRegionChange = (region: string) => {
    setSelectedRegion(region);
    setSelectedCategory(''); // Reset category when region changes
  };

  // Convert trending videos to VideoResult format for VideoGrid
  const convertedVideos: VideoResult[] = trendingData?.videos.map(video => ({
    video_id: video.video_id,
    title: video.title,
    description: video.description,
    channel_title: video.channel_title,
    channel_id: video.channel_id,
    published_at: video.published_at,
    duration: video.duration,
    view_count: video.view_count,
    like_count: video.like_count,
    comment_count: video.comment_count,
    thumbnail_url: video.thumbnail_url,
    relevance_score: video.trending_score,
    quality_score: 0.8, // Default quality score
    engagement_rate: video.like_count && video.view_count ? 
      (video.like_count / video.view_count * 100) : undefined,
    tags: video.tags,
    category: video.category
  })) || [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <ArrowTrendingUpIcon className="w-8 h-8 mr-3 text-red-600" />
                Trending Content
              </h1>
              <p className="text-gray-600 mt-1">
                Discover what's popular on YouTube right now
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                {trendingData && (
                  <span>Last updated: {new Date(trendingData.generated_at).toLocaleTimeString()}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Filters */}
          <div className="lg:col-span-1">
            <div className="sticky top-8 space-y-6">
              {/* Region Filter */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center mb-4">
                  <GlobeAltIcon className="w-5 h-5 mr-2 text-gray-600" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    Region
                  </h3>
                </div>
                <select
                  value={selectedRegion}
                  onChange={(e) => handleRegionChange(e.target.value)}
                  className="form-input w-full"
                >
                  {regions.map(region => (
                    <option key={region.code} value={region.code}>
                      {region.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Category Filter */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center mb-4">
                  <TagIcon className="w-5 h-5 mr-2 text-gray-600" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    Category
                  </h3>
                </div>
                {isLoadingCategories ? (
                  <div className="flex justify-center py-4">
                    <LoadingSpinner size="small" />
                  </div>
                ) : (
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="form-input w-full"
                  >
                    <option value="">All Categories</option>
                    {categories?.filter(cat => cat.assignable).map(category => (
                      <option key={category.id} value={category.id}>
                        {category.title}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Results Count */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center mb-4">
                  <ClockIcon className="w-5 h-5 mr-2 text-gray-600" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    Results
                  </h3>
                </div>
                <select
                  value={maxResults}
                  onChange={(e) => setMaxResults(parseInt(e.target.value))}
                  className="form-input w-full"
                >
                  <option value={25}>25 videos</option>
                  <option value={50}>50 videos</option>
                  <option value={100}>100 videos</option>
                </select>
              </div>

              {/* Stats */}
              {trendingData && (
                <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Trending Stats
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Region:</span>
                      <span className="font-medium">{regions.find(r => r.code === selectedRegion)?.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Videos:</span>
                      <span className="font-medium">{trendingData.total_results}</span>
                    </div>
                    {selectedCategory && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Category:</span>
                        <span className="font-medium">
                          {categories?.find(c => c.id === selectedCategory)?.title || 'Unknown'}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Main Content - Trending Videos */}
          <div className="lg:col-span-3">
            {isLoadingTrending && (
              <div className="flex justify-center items-center py-12">
                <LoadingSpinner size="large" />
              </div>
            )}

            {trendingError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <div className="text-red-800 font-semibold mb-2">
                  Error Loading Trending Videos
                </div>
                <div className="text-red-600 text-sm mb-4">
                  {(trendingError as any)?.message || 'An error occurred while loading trending videos'}
                </div>
                <button
                  onClick={() => refetchTrending()}
                  className="btn-primary"
                >
                  Try Again
                </button>
              </div>
            )}

            {convertedVideos.length > 0 && !isLoadingTrending && (
              <div>
                {/* Trending Header */}
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">
                      Trending Videos
                    </h2>
                    <p className="text-gray-600 text-sm mt-1">
                      {trendingData?.total_results} trending videos in {regions.find(r => r.code === selectedRegion)?.name}
                    </p>
                  </div>
                  
                  <button
                    onClick={() => refetchTrending()}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Refresh
                  </button>
                </div>

                {/* Video Grid */}
                <VideoGrid videos={convertedVideos} />
              </div>
            )}

            {convertedVideos.length === 0 && !isLoadingTrending && !trendingError && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                <div className="text-yellow-800 font-semibold mb-2">
                  No Trending Videos Found
                </div>
                <div className="text-yellow-600 text-sm">
                  Try selecting a different region or category.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrendsPage;