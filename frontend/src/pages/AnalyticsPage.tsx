import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  UserGroupIcon,
  LightBulbIcon,
  EyeIcon,
  HeartIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import LoadingSpinner from '../components/LoadingSpinner';
import { 
  analyzeTrends, 
  getContentInsights, 
  analyzeCompetitors, 
  identifyContentGaps 
} from '../services/api';
import { TrendAnalysis, ContentInsights } from '../types/api';

const AnalyticsPage: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [trendKeywords, setTrendKeywords] = useState(['AI', 'React', 'YouTube']);
  const [newKeyword, setNewKeyword] = useState('');
  const [contentTopic, setContentTopic] = useState('programming tutorials');
  const [competitorChannels, setCompetitorChannels] = useState(['UCWv7vMbMWH4-V0ZXdmDpPBA']);
  const [newChannel, setNewChannel] = useState('');
  const [contentNiche, setContentNiche] = useState('web development');

  // Trends Analysis Query
  const {
    data: trendsData,
    isLoading: isLoadingTrends,
    error: trendsError,
    refetch: refetchTrends
  } = useQuery<TrendAnalysis[]>({
    queryKey: ['trends', trendKeywords],
    queryFn: () => analyzeTrends(trendKeywords),
    enabled: trendKeywords.length > 0,
    retry: 2
  });

  // Content Insights Query
  const {
    data: contentInsights,
    isLoading: isLoadingInsights,
    error: insightsError,
    refetch: refetchInsights
  } = useQuery<ContentInsights>({
    queryKey: ['content-insights', contentTopic],
    queryFn: () => getContentInsights(contentTopic),
    enabled: !!contentTopic,
    retry: 2
  });

  // Competitor Analysis Query
  const {
    data: competitorData,
    isLoading: isLoadingCompetitors,
    error: competitorError,
    refetch: refetchCompetitors
  } = useQuery({
    queryKey: ['competitors', competitorChannels],
    queryFn: () => analyzeCompetitors(competitorChannels),
    enabled: competitorChannels.length > 0,
    retry: 2
  });

  // Content Gaps Query
  const {
    data: contentGaps,
    isLoading: isLoadingGaps,
    error: gapsError,
    refetch: refetchGaps
  } = useQuery({
    queryKey: ['content-gaps', contentNiche],
    queryFn: () => identifyContentGaps(contentNiche),
    enabled: !!contentNiche,
    retry: 2
  });

  // Handle errors
  useEffect(() => {
    if (trendsError) toast.error('Failed to load trends data');
    if (insightsError) toast.error('Failed to load content insights');
    if (competitorError) toast.error('Failed to load competitor data');
    if (gapsError) toast.error('Failed to load content gaps');
  }, [trendsError, insightsError, competitorError, gapsError]);

  const addKeyword = () => {
    if (newKeyword.trim() && !trendKeywords.includes(newKeyword.trim())) {
      setTrendKeywords([...trendKeywords, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const removeKeyword = (keyword: string) => {
    setTrendKeywords(trendKeywords.filter(k => k !== keyword));
  };

  const addChannel = () => {
    if (newChannel.trim() && !competitorChannels.includes(newChannel.trim())) {
      setCompetitorChannels([...competitorChannels, newChannel.trim()]);
      setNewChannel('');
    }
  };

  const removeChannel = (channel: string) => {
    setCompetitorChannels(competitorChannels.filter(c => c !== channel));
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'trends', name: 'Trend Analysis', icon: ArrowTrendingUpIcon },
    { id: 'insights', name: 'Content Insights', icon: LightBulbIcon },
    { id: 'competitors', name: 'Competitors', icon: UserGroupIcon },
    { id: 'gaps', name: 'Content Gaps', icon: EyeIcon }
  ];

  const mockOverviewStats = {
    totalSearches: 1247,
    avgRelevanceScore: 0.87,
    topContentTypes: ['Tutorial', 'Review', 'Vlog'],
    searchesToday: 23
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <ChartBarIcon className="w-8 h-8 mr-3 text-blue-600" />
                Analytics Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Analyze trends, insights, and opportunities in YouTube content
              </p>
            </div>
            
            <div className="text-sm text-gray-500">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-md mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                      selectedTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-8">
          {/* Overview Tab */}
          {selectedTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <ChartBarIcon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Searches</p>
                    <p className="text-2xl font-bold text-gray-900">{mockOverviewStats.totalSearches.toLocaleString()}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <ArrowTrendingUpIcon className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Avg Relevance</p>
                    <p className="text-2xl font-bold text-gray-900">{(mockOverviewStats.avgRelevanceScore * 100).toFixed(0)}%</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <EyeIcon className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Searches Today</p>
                    <p className="text-2xl font-bold text-gray-900">{mockOverviewStats.searchesToday}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <HeartIcon className="w-6 h-6 text-orange-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Top Content</p>
                    <p className="text-sm font-bold text-gray-900">{mockOverviewStats.topContentTypes.join(', ')}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Trends Tab */}
          {selectedTab === 'trends' && (
            <div className="space-y-6">
              {/* Keywords Management */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trend Keywords</h3>
                <div className="flex flex-wrap gap-2 mb-4">
                  {trendKeywords.map((keyword) => (
                    <span
                      key={keyword}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                    >
                      {keyword}
                      <button
                        onClick={() => removeKeyword(keyword)}
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
                    placeholder="Add keyword..."
                    className="form-input flex-1"
                  />
                  <button onClick={addKeyword} className="btn-primary">
                    Add
                  </button>
                  <button onClick={() => refetchTrends()} className="btn-secondary">
                    Refresh
                  </button>
                </div>
              </div>

              {/* Trends Results */}
              {isLoadingTrends ? (
                <div className="bg-white rounded-lg shadow-md p-6 flex justify-center">
                  <LoadingSpinner size="large" />
                </div>
              ) : trendsData && trendsData.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {trendsData.map((trend, index) => (
                    <div key={index} className="bg-white rounded-lg shadow-md p-6">
                      <h4 className="text-lg font-semibold text-gray-900 mb-2">{trend.keyword}</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Trend Score:</span>
                          <span className="font-medium">{(trend.trend_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Search Volume:</span>
                          <span className="font-medium">{trend.search_volume.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Competition:</span>
                          <span className={`font-medium capitalize ${
                            trend.competition_level === 'high' ? 'text-red-600' :
                            trend.competition_level === 'medium' ? 'text-yellow-600' : 'text-green-600'
                          }`}>{trend.competition_level}</span>
                        </div>
                      </div>
                      <div className="mt-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">Opportunities:</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {trend.content_opportunities.slice(0, 2).map((opp, i) => (
                            <li key={i}>• {opp}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-md p-6 text-center">
                  <p className="text-gray-600">No trends data available. Add keywords and click refresh.</p>
                </div>
              )}
            </div>
          )}

          {/* Content Insights Tab */}
          {selectedTab === 'insights' && (
            <div className="space-y-6">
              {/* Topic Input */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Content Analysis</h3>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={contentTopic}
                    onChange={(e) => setContentTopic(e.target.value)}
                    placeholder="Enter content topic..."
                    className="form-input flex-1"
                  />
                  <button onClick={() => refetchInsights()} className="btn-primary">
                    Analyze
                  </button>
                </div>
              </div>

              {/* Insights Results */}
              {isLoadingInsights ? (
                <div className="bg-white rounded-lg shadow-md p-6 flex justify-center">
                  <LoadingSpinner size="large" />
                </div>
              ) : contentInsights ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Content Metrics</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Videos:</span>
                        <span className="font-medium">{contentInsights.total_videos.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Avg Views:</span>
                        <span className="font-medium">{contentInsights.avg_view_count.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Avg Engagement:</span>
                        <span className="font-medium">{(contentInsights.avg_engagement_rate * 100).toFixed(2)}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow-md p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Top Creators</h4>
                    <div className="space-y-2">
                      {contentInsights.top_creators.slice(0, 5).map((creator, index) => (
                        <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0">
                          <span className="text-sm text-gray-900">{creator.channel_title}</span>
                          <span className="text-xs text-gray-600">{creator.total_views.toLocaleString()} views</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg shadow-md p-6 lg:col-span-2">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Content Gaps & Recommendations</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium text-gray-700 mb-2">Identified Gaps:</h5>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {contentInsights.content_gaps.map((gap, index) => (
                            <li key={index}>• {gap}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h5 className="font-medium text-gray-700 mb-2">Recommended Formats:</h5>
                        <div className="flex flex-wrap gap-2">
                          {contentInsights.recommended_formats.map((format, index) => (
                            <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                              {format}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-md p-6 text-center">
                  <p className="text-gray-600">Enter a topic and click analyze to get content insights.</p>
                </div>
              )}
            </div>
          )}

          {/* Competitors Tab */}
          {selectedTab === 'competitors' && (
            <div className="space-y-6">
              {/* Channel Management */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Competitor Channels</h3>
                <div className="flex flex-wrap gap-2 mb-4">
                  {competitorChannels.map((channel) => (
                    <span
                      key={channel}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800"
                    >
                      {channel}
                      <button
                        onClick={() => removeChannel(channel)}
                        className="ml-2 text-purple-600 hover:text-purple-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newChannel}
                    onChange={(e) => setNewChannel(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addChannel()}
                    placeholder="Add channel ID..."
                    className="form-input flex-1"
                  />
                  <button onClick={addChannel} className="btn-primary">
                    Add
                  </button>
                  <button onClick={() => refetchCompetitors()} className="btn-secondary">
                    Analyze
                  </button>
                </div>
              </div>

              {/* Competitor Results */}
              {isLoadingCompetitors ? (
                <div className="bg-white rounded-lg shadow-md p-6 flex justify-center">
                  <LoadingSpinner size="large" />
                </div>
              ) : competitorData ? (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h4>
                  <p className="text-sm text-gray-600 mb-4">Analyzed {competitorData.channels_analyzed} channels</p>
                  
                  {competitorData.insights && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h5 className="font-medium text-blue-900 mb-2">Key Insights:</h5>
                      <ul className="text-sm text-blue-800 space-y-1">
                        {competitorData.insights.map((insight: string, index: number) => (
                          <li key={index}>• {insight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-md p-6 text-center">
                  <p className="text-gray-600">Add competitor channel IDs and click analyze.</p>
                </div>
              )}
            </div>
          )}

          {/* Content Gaps Tab */}
          {selectedTab === 'gaps' && (
            <div className="space-y-6">
              {/* Niche Input */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Content Gap Analysis</h3>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={contentNiche}
                    onChange={(e) => setContentNiche(e.target.value)}
                    placeholder="Enter content niche..."
                    className="form-input flex-1"
                  />
                  <button onClick={() => refetchGaps()} className="btn-primary">
                    Find Gaps
                  </button>
                </div>
              </div>

              {/* Gaps Results */}
              {isLoadingGaps ? (
                <div className="bg-white rounded-lg shadow-md p-6 flex justify-center">
                  <LoadingSpinner size="large" />
                </div>
              ) : contentGaps ? (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Content Opportunities</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Found {contentGaps.identified_gaps?.length || 0} content gaps in {contentGaps.niche}
                  </p>
                  
                  {contentGaps.recommendations && (
                    <div className="space-y-3">
                      {contentGaps.recommendations.map((rec: string, index: number) => (
                        <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <p className="text-sm text-green-800">{rec}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-white rounded-lg shadow-md p-6 text-center">
                  <p className="text-gray-600">Enter a content niche and click "Find Gaps" to discover opportunities.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;