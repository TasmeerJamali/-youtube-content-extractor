import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  FunnelIcon,
  SparklesIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import SearchForm from '../components/SearchForm';
import VideoGrid from '../components/VideoGrid';
import SearchFilters from '../components/SearchFilters';
import LoadingSpinner from '../components/LoadingSpinner';
import TranscriptViewer from '../components/TranscriptViewer';
import BulkTranscriptDownload from '../components/BulkTranscriptDownload';
import { searchContent, getSearchSuggestions } from '../services/api';
import { SearchRequest, SearchResponse, VideoResult } from '../types/api';

const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useState<SearchRequest>({
    idea: '',
    max_results: 50,
    content_types: [],
    language: 'en',
    region: 'US',
    include_transcripts: false,
    include_comments: false
  });
  
  const [showFilters, setShowFilters] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<VideoResult | null>(null);
  const [showTranscriptViewer, setShowTranscriptViewer] = useState(false);

  // Search query
  const {
    data: searchResults,
    isLoading: isSearching,
    error: searchError,
    refetch: performSearch
  } = useQuery<SearchResponse>({
    queryKey: ['search', searchParams],
    queryFn: () => searchContent(searchParams),
    enabled: false, // Only run when manually triggered
    retry: 2
  });

  // Handle search success/error using useEffect
  React.useEffect(() => {
    if (searchError) {
      toast.error(`Search failed: ${(searchError as any)?.message || 'Unknown error'}`);
    }
  }, [searchError]);

  React.useEffect(() => {
    if (searchResults && hasSearched) {
      toast.success('Search completed successfully!');
    }
  }, [searchResults, hasSearched]);

  // Suggestions query
  const {
    data: suggestions,
    isLoading: loadingSuggestions
  } = useQuery({
    queryKey: ['suggestions', searchParams.idea],
    queryFn: () => getSearchSuggestions(searchParams.idea),
    enabled: searchParams.idea.length > 2,
    staleTime: 30000 // 30 seconds
  });

  const handleSearch = async (params: SearchRequest) => {
    setSearchParams(params);
    setHasSearched(true);
    performSearch();
  };

  const handleFilterChange = (filters: Partial<SearchRequest>) => {
    setSearchParams(prev => ({ ...prev, ...filters }));
  };

  const handleApplyFilters = () => {
    if (hasSearched) {
      performSearch();
    }
  };

  const handleVideoSelect = (video: VideoResult) => {
    if (video.transcript) {
      setSelectedVideo(video);
      setShowTranscriptViewer(true);
    } else {
      // Show toast message for unavailable transcripts
      if (searchParams.include_transcripts) {
        toast.error('Transcript not available for this video - may be due to API quota limits or video restrictions');
      }
      // Open YouTube video in new tab
      window.open(`https://www.youtube.com/watch?v=${video.video_id}`, '_blank');
    }
  };

  const closeTranscriptViewer = () => {
    setShowTranscriptViewer(false);
    setSelectedVideo(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <MagnifyingGlassIcon className="w-8 h-8 mr-3 text-blue-600" />
                Content Search
              </h1>
              <p className="text-gray-600 mt-1">
                Discover YouTube content using natural language descriptions
              </p>
            </div>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition duration-200 ${
                showFilters 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700 hover:shadow-sm'
              }`}
            >
              <AdjustmentsHorizontalIcon className="w-5 h-5" />
              <span>{showFilters ? 'Hide Filters' : 'Show Filters'}</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Search Form and Filters */}
          <div className="lg:col-span-1">
            <div className="sticky top-8 space-y-6">
              {/* Search Form */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <SearchForm
                  onSearch={handleSearch}
                  isLoading={isSearching}
                  suggestions={suggestions?.suggestions || []}
                  loadingSuggestions={loadingSuggestions}
                  initialValues={searchParams}
                />
              </div>

              {/* Filters */}
              {showFilters && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex items-center mb-4">
                    <FunnelIcon className="w-5 h-5 mr-2 text-gray-600" />
                    <h3 className="text-lg font-semibold text-gray-900">
                      Search Filters
                    </h3>
                  </div>
                  <SearchFilters
                    filters={searchParams}
                    onChange={handleFilterChange}
                    onApply={handleApplyFilters}
                  />
                </div>
              )}

              {/* Search Tips */}
              <div className="bg-blue-50 rounded-lg p-6">
                <div className="flex items-center mb-3">
                  <SparklesIcon className="w-5 h-5 mr-2 text-blue-600" />
                  <h3 className="text-lg font-semibold text-blue-900">
                    Search Tips
                  </h3>
                </div>
                <ul className="text-sm text-blue-800 space-y-2">
                  <li>• Use natural language to describe your video idea</li>
                  <li>• Be specific about content type (tutorial, review, etc.)</li>
                  <li>• Include keywords related to your topic</li>
                  <li>• Specify skill level (beginner, advanced)</li>
                  <li>• Mention preferred video length or quality</li>
                </ul>
              </div>
              
              {/* Transcript Feature Info */}
              <div className="bg-green-50 rounded-lg p-6">
                <div className="flex items-center mb-3">
                  <DocumentTextIcon className="w-5 h-5 mr-2 text-green-600" />
                  <h3 className="text-lg font-semibold text-green-900">
                    Transcript Features
                  </h3>
                </div>
                <ul className="text-sm text-green-800 space-y-2">
                  <li>📄 Full video transcripts with captions</li>
                  <li>🔍 Enhanced search accuracy with transcript content</li>
                  <li>💾 Download individual or bulk transcripts</li>
                  <li>📊 Word count and reading time analysis</li>
                  <li>🎯 Multiple export formats (TXT, JSON, CSV, ZIP)</li>
                </ul>
                <p className="text-xs text-green-600 mt-3 font-medium">
                  ✨ Enable "Include video transcripts" for full transcript analysis!
                </p>
                
                {/* API Quota Warning */}
                <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                  <div className="flex items-center text-yellow-800">
                    <span className="mr-1">⚠️</span>
                    <strong>Note:</strong> If transcripts show as unavailable, the YouTube API daily quota may be exceeded. Try again tomorrow.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content - Search Results */}
          <div className="lg:col-span-3">
            {isSearching && (
              <div className="flex justify-center items-center py-12">
                <LoadingSpinner size="large" />
              </div>
            )}

            {searchError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <div className="text-red-800 font-semibold mb-2">
                  Search Error
                </div>
                <div className="text-red-600 text-sm">
                  {(searchError as any)?.message || 'An error occurred while searching'}
                </div>
              </div>
            )}

            {searchResults && !isSearching && (searchResults as SearchResponse) && (
              <div>
                {/* Search Results Header */}
                <div className="bg-white rounded-lg shadow-md p-4 mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">
                        Search Results
                      </h2>
                      <p className="text-gray-600 text-sm mt-1">
                        Found {(searchResults as SearchResponse).total_results} videos in {(searchResults as SearchResponse).search_time_ms}ms
                      </p>
                    </div>
                    
                    <div className="text-sm text-gray-500">
                      Quota used: {(searchResults as SearchResponse).quota_used}
                    </div>
                  </div>
                  
                  {/* Bulk Download Options */}
                  {searchParams.include_transcripts && (
                    <div className="border-t pt-4">
                      <BulkTranscriptDownload 
                        videos={(searchResults as SearchResponse).videos}
                        searchQuery={searchParams.idea}
                      />
                    </div>
                  )}
                </div>

                {/* Transcript Statistics */}
                {searchParams.include_transcripts && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                    <div className="flex items-center">
                      <DocumentTextIcon className="w-5 h-5 text-green-600 mr-2" />
                      <h3 className="font-semibold text-green-900">Transcript Analysis</h3>
                    </div>
                    <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-green-800">Available:</span>
                        <span className="ml-2 text-green-700">
                          {(searchResults as SearchResponse).videos.filter(v => v.transcript).length} videos
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-green-800">Coverage:</span>
                        <span className="ml-2 text-green-700">
                          {Math.round(((searchResults as SearchResponse).videos.filter(v => v.transcript).length / (searchResults as SearchResponse).videos.length) * 100)}%
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-green-800">Total Words:</span>
                        <span className="ml-2 text-green-700">
                          {(searchResults as SearchResponse).videos
                            .filter(v => v.transcript)
                            .reduce((acc, v) => acc + (v.transcript?.split(' ').length || 0), 0).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-green-800">Avg Length:</span>
                        <span className="ml-2 text-green-700">
                          {Math.round((searchResults as SearchResponse).videos
                            .filter(v => v.transcript)
                            .reduce((acc, v) => acc + (v.transcript?.split(' ').length || 0), 0) / 
                            (searchResults as SearchResponse).videos.filter(v => v.transcript).length || 1)} words
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-green-600 mt-2">
                      💡 Click on videos with transcript badges to view and download full transcripts
                    </p>
                  </div>
                )}

                {/* Query Information */}
                <div className="bg-white rounded-lg shadow-md p-4 mb-6">
                  <h3 className="font-semibold text-gray-900 mb-2">Search Analysis</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Keywords:</span>
                      <div className="mt-1">
                        {(searchResults as SearchResponse).query_info.processed_keywords.map((keyword, idx) => (
                          <span key={idx} className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mr-1 mb-1">
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Content Types:</span>
                      <div className="mt-1">
                        {(searchResults as SearchResponse).query_info.detected_content_types.map((type, idx) => (
                          <span key={idx} className="inline-block bg-green-100 text-green-800 px-2 py-1 rounded text-xs mr-1 mb-1">
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Intent:</span>
                      <span className="ml-2 text-gray-600 capitalize">
                        {(searchResults as SearchResponse).query_info.intent}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Confidence:</span>
                      <span className="ml-2 text-gray-600">
                        {((searchResults as SearchResponse).query_info.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Video Results */}
                {(searchResults as SearchResponse).videos.length > 0 ? (
                  <VideoGrid 
                    videos={(searchResults as SearchResponse).videos} 
                    showTranscripts={searchParams.include_transcripts}
                    showComments={searchParams.include_comments}
                    onVideoSelect={handleVideoSelect}
                  />
                ) : (
                  <div className="text-center py-12">
                    <MagnifyingGlassIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      No results found
                    </h3>
                    <p className="text-gray-600 mb-6">
                      Try adjusting your search terms or filters
                    </p>
                  </div>
                )}

                {/* Search Suggestions */}
                {(searchResults as SearchResponse).suggestions && (searchResults as SearchResponse).suggestions.length > 0 && (
                  <div className="mt-8 bg-white rounded-lg shadow-md p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">
                      Related Searches
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {(searchResults as SearchResponse).suggestions.map((suggestion, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSearch({ ...searchParams, idea: suggestion })}
                          className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full text-sm transition duration-200"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {!hasSearched && !isSearching && (
              <div className="text-center py-12">
                <MagnifyingGlassIcon className="w-20 h-20 mx-auto text-gray-300 mb-6" />
                <h2 className="text-2xl font-semibold text-gray-600 mb-4">
                  Ready to Discover Content?
                </h2>
                <p className="text-gray-500 max-w-md mx-auto">
                  Enter your video idea in the search form to get started. 
                  Our AI will find the most relevant YouTube content for you.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Transcript Viewer Modal */}
      {selectedVideo && (
        <TranscriptViewer
          video={selectedVideo}
          isOpen={showTranscriptViewer}
          onClose={closeTranscriptViewer}
        />
      )}
    </div>
  );
};

export default SearchPage;