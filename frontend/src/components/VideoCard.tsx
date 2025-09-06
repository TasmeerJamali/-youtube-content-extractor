import React, { useState } from 'react';
import { 
  PlayIcon, 
  EyeIcon, 
  HandThumbUpIcon, 
  ChatBubbleLeftIcon,
  ClockIcon,
  StarIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { VideoCardProps } from '../types/api';

const VideoCard: React.FC<VideoCardProps> = ({
  video,
  onSelect,
  showTranscript = false,
  showComments = false
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [showTranscriptModal, setShowTranscriptModal] = useState(false);

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  const getRelevanceColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getQualityStars = (score: number): number => {
    return Math.round(score * 5);
  };

  const handleImageError = () => {
    setImageError(true);
  };

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(video);
    } else {
      // Open YouTube video in new tab
      window.open(`https://www.youtube.com/watch?v=${video.video_id}`, '_blank');
    }
  };

  const downloadTranscript = (format: 'txt' | 'json') => {
    if (!video.transcript) return;

    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === 'txt') {
      content = `Transcript for: ${video.title}\n\nChannel: ${video.channel_title}\nPublished: ${video.published_at}\nURL: https://www.youtube.com/watch?v=${video.video_id}\n\n${video.transcript}`;
      filename = `${video.title.replace(/[^a-zA-Z0-9]/g, '_')}_transcript.txt`;
      mimeType = 'text/plain';
    } else {
      const data = {
        video_id: video.video_id,
        title: video.title,
        channel: video.channel_title,
        published_at: video.published_at,
        url: `https://www.youtube.com/watch?v=${video.video_id}`,
        transcript: video.transcript,
        exported_at: new Date().toISOString()
      };
      content = JSON.stringify(data, null, 2);
      filename = `${video.title.replace(/[^a-zA-Z0-9]/g, '_')}_transcript.json`;
      mimeType = 'application/json';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadComments = () => {
    if (!video.top_comments || video.top_comments.length === 0) return;

    const data = {
      video_id: video.video_id,
      title: video.title,
      channel: video.channel_title,
      published_at: video.published_at,
      url: `https://www.youtube.com/watch?v=${video.video_id}`,
      top_comments: video.top_comments,
      exported_at: new Date().toISOString()
    };

    const content = JSON.stringify(data, null, 2);
    const filename = `${video.title.replace(/[^a-zA-Z0-9]/g, '_')}_comments.json`;
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="video-card bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
      {/* Thumbnail and Play Button */}
      <div className="relative group cursor-pointer" onClick={handleCardClick}>
        {!imageError ? (
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className="w-full h-48 object-cover"
            onError={handleImageError}
          />
        ) : (
          <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
            <PlayIcon className="w-12 h-12 text-gray-400" />
          </div>
        )}
        
        {/* Play overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center">
          <PlayIcon className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
        </div>

        {/* Duration badge */}
        {video.duration && (
          <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
            {formatDuration(video.duration)}
          </div>
        )}

        {/* Transcript indicator - show even if no transcript to indicate feature availability */}
        {(video.transcript || showTranscript) && (
          <div className={`absolute top-2 left-2 text-white text-xs px-2 py-1 rounded flex items-center ${
            video.transcript 
              ? 'bg-green-600 bg-opacity-90' 
              : 'bg-gray-600 bg-opacity-90'
          }`}>
            <DocumentTextIcon className="w-3 h-3 mr-1" />
            {video.transcript ? 'Transcript' : 'No Transcript'}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title */}
        <h3 
          className="font-semibold text-gray-900 line-clamp-2 cursor-pointer hover:text-blue-600 transition-colors"
          onClick={handleCardClick}
          title={video.title}
        >
          {video.title}
        </h3>

        {/* Channel and Date */}
        <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
          <span className="truncate">{video.channel_title}</span>
          <span className="flex items-center ml-2">
            <ClockIcon className="w-4 h-4 mr-1" />
            {formatDate(video.published_at)}
          </span>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <EyeIcon className="w-4 h-4 mr-1" />
              {formatNumber(video.view_count)}
            </span>
            
            {video.like_count && (
              <span className="flex items-center">
                <HandThumbUpIcon className="w-4 h-4 mr-1" />
                {formatNumber(video.like_count)}
              </span>
            )}
            
            {video.comment_count && (
              <span className="flex items-center">
                <ChatBubbleLeftIcon className="w-4 h-4 mr-1" />
                {formatNumber(video.comment_count)}
              </span>
            )}
          </div>
        </div>

        {/* Scores */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center space-x-3">
            {/* Relevance Score */}
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getRelevanceColor(video.relevance_score)}`}>
              {Math.round(video.relevance_score * 100)}% match
            </div>

            {/* Quality Stars */}
            <div className="flex items-center">
              {[...Array(5)].map((_, i) => (
                <StarIcon
                  key={i}
                  className={`w-4 h-4 ${
                    i < getQualityStars(video.quality_score)
                      ? 'text-yellow-400 fill-current'
                      : 'text-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Engagement Rate */}
          {video.engagement_rate && (
            <div className="text-xs text-gray-500">
              {(video.engagement_rate * 100).toFixed(1)}% engagement
            </div>
          )}
        </div>

        {/* Tags */}
        {video.tags && video.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {video.tags.slice(0, 3).map((tag, idx) => (
              <span
                key={idx}
                className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded"
              >
                #{tag}
              </span>
            ))}
            {video.tags.length > 3 && (
              <span className="text-xs text-gray-500">
                +{video.tags.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-3">
          {/* Transcript Button */}
          {showTranscript && (
            <div className="flex-1">
              {video.transcript ? (
                <button
                  onClick={() => setShowTranscriptModal(true)}
                  className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                >
                  <DocumentTextIcon className="w-4 h-4 mr-1" />
                  View Transcript
                </button>
              ) : (
                <div className="flex items-center px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded-md">
                  <DocumentTextIcon className="w-4 h-4 mr-1" />
                  <span className="text-xs">No transcript available</span>
                  <div className="ml-2 group relative">
                    <span className="text-xs text-gray-400 cursor-help">ℹ️</span>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
                      API quota exceeded - try again later
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Toggle Details */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center text-sm text-gray-500 hover:text-gray-700 transition-colors ml-auto"
          >
            {showDetails ? (
              <>
                <span>Less details</span>
                <ChevronUpIcon className="w-4 h-4 ml-1" />
              </>
            ) : (
              <>
                <span>More details</span>
                <ChevronDownIcon className="w-4 h-4 ml-1" />
              </>
            )}
          </button>
        </div>

        {/* Expanded Details */}
        {showDetails && (
          <div className="mt-4 space-y-3 border-t pt-3">
            {/* Description */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-1">Description</h4>
              <p className="text-sm text-gray-600 line-clamp-3">
                {video.description || 'No description available'}
              </p>
            </div>

            {/* Transcript Preview */}
            {showTranscript && video.transcript && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-900">Transcript Preview</h4>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => downloadTranscript('txt')}
                      className="flex items-center text-xs text-blue-600 hover:text-blue-800"
                      title="Download as TXT"
                    >
                      <ArrowDownTrayIcon className="w-3 h-3 mr-1" />
                      TXT
                    </button>
                    <button
                      onClick={() => downloadTranscript('json')}
                      className="flex items-center text-xs text-blue-600 hover:text-blue-800"
                      title="Download as JSON"
                    >
                      <ArrowDownTrayIcon className="w-3 h-3 mr-1" />
                      JSON
                    </button>
                    <button
                      onClick={() => setShowTranscriptModal(true)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      View Full
                    </button>
                  </div>
                </div>
                <div className="bg-gray-50 rounded p-3 max-h-32 overflow-y-auto">
                  <p className="text-sm text-gray-600 line-clamp-4">
                    {video.transcript.substring(0, 200)}...
                  </p>
                </div>
              </div>
            )}

            {/* Comments */}
            {showComments && video.top_comments && video.top_comments.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-900">Top Comments ({video.top_comments.length})</h4>
                  <button
                    onClick={downloadComments}
                    className="flex items-center text-xs text-blue-600 hover:text-blue-800"
                    title="Download Comments"
                  >
                    <ArrowDownTrayIcon className="w-3 h-3 mr-1" />
                    Download
                  </button>
                </div>
                <div className="space-y-2 bg-gray-50 rounded p-3 max-h-32 overflow-y-auto">
                  {video.top_comments.slice(0, 3).map((comment, idx) => (
                    <p key={idx} className="text-sm text-gray-600 border-b border-gray-200 pb-1 last:border-b-0">
                      {comment}
                    </p>
                  ))}
                  {video.top_comments.length > 3 && (
                    <p className="text-xs text-gray-500 italic">
                      +{video.top_comments.length - 3} more comments available for download
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Transcript Modal */}
      {showTranscriptModal && video.transcript && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Video Transcript</h3>
                <p className="text-sm text-gray-600 truncate">{video.title}</p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => downloadTranscript('txt')}
                  className="flex items-center px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                >
                  <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
                  Download TXT
                </button>
                <button
                  onClick={() => downloadTranscript('json')}
                  className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                >
                  <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
                  Download JSON
                </button>
                <button
                  onClick={() => setShowTranscriptModal(false)}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="prose max-w-none">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="mb-4 text-sm text-gray-600">
                    <p><strong>Channel:</strong> {video.channel_title}</p>
                    <p><strong>Published:</strong> {formatDate(video.published_at)}</p>
                    <p><strong>Duration:</strong> {formatDuration(video.duration)}</p>
                    <p><strong>Views:</strong> {formatNumber(video.view_count)}</p>
                  </div>
                  <hr className="my-4" />
                  <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
                    {video.transcript}
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-4 border-t bg-gray-50">
              <div className="text-sm text-gray-600">
                Word count: {video.transcript.split(' ').length} words
              </div>
              <button
                onClick={() => setShowTranscriptModal(false)}
                className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoCard;