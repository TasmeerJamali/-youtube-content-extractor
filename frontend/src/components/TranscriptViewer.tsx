import React, { useState } from 'react';
import {
  ArrowDownTrayIcon,
  XMarkIcon,
  DocumentTextIcon,
  ClipboardDocumentIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import { VideoResult } from '../types/api';

interface TranscriptViewerProps {
  video: VideoResult;
  isOpen: boolean;
  onClose: () => void;
}

const TranscriptViewer: React.FC<TranscriptViewerProps> = ({
  video,
  isOpen,
  onClose
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !video.transcript) return null;

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
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const downloadTranscript = (format: 'txt' | 'json' | 'csv') => {
    if (!video.transcript) return;

    let content = '';
    let filename = '';
    let mimeType = 'text/plain';

    const baseFilename = video.title.replace(/[^a-zA-Z0-9]/g, '_');

    if (format === 'txt') {
      content = `TRANSCRIPT\n${'='.repeat(50)}\n\nTitle: ${video.title}\nChannel: ${video.channel_title}\nPublished: ${formatDate(video.published_at)}\nDuration: ${formatDuration(video.duration)}\nViews: ${formatNumber(video.view_count)}\nURL: https://www.youtube.com/watch?v=${video.video_id}\n\n${'='.repeat(50)}\n\n${video.transcript}`;
      filename = `${baseFilename}_transcript.txt`;
      mimeType = 'text/plain';
    } else if (format === 'json') {
      const data = {
        video_metadata: {
          video_id: video.video_id,
          title: video.title,
          channel_title: video.channel_title,
          published_at: video.published_at,
          duration: video.duration,
          view_count: video.view_count,
          like_count: video.like_count,
          comment_count: video.comment_count,
          url: `https://www.youtube.com/watch?v=${video.video_id}`,
          thumbnail_url: video.thumbnail_url,
          relevance_score: video.relevance_score,
          quality_score: video.quality_score,
          tags: video.tags
        },
        transcript: {
          content: video.transcript,
          word_count: video.transcript.split(' ').length,
          character_count: video.transcript.length
        },
        export_info: {
          exported_at: new Date().toISOString(),
          exported_by: 'YouTube Content Extractor',
          format: 'json'
        }
      };
      content = JSON.stringify(data, null, 2);
      filename = `${baseFilename}_transcript.json`;
      mimeType = 'application/json';
    } else if (format === 'csv') {
      // Split transcript into sentences for CSV format
      const sentences = video.transcript.split(/[.!?]+/).filter(s => s.trim().length > 0);
      const csvRows = [
        'Video ID,Title,Channel,Sentence Number,Content',
        ...sentences.map((sentence, index) => 
          `"${video.video_id}","${video.title.replace(/"/g, '""')}","${video.channel_title.replace(/"/g, '""')}",${index + 1},"${sentence.trim().replace(/"/g, '""')}"`
        )
      ];
      content = csvRows.join('\n');
      filename = `${baseFilename}_transcript.csv`;
      mimeType = 'text/csv';
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

  const copyToClipboard = async () => {
    if (!video.transcript) return;
    
    try {
      await navigator.clipboard.writeText(video.transcript);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy transcript:', err);
    }
  };

  const wordCount = video.transcript.split(' ').length;
  const estimatedReadingTime = Math.ceil(wordCount / 200); // Assuming 200 words per minute

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-5xl w-full max-h-[95vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex-1 mr-4">
            <div className="flex items-center mb-2">
              <DocumentTextIcon className="w-6 h-6 text-blue-600 mr-2" />
              <h2 className="text-xl font-bold text-gray-900">Video Transcript</h2>
            </div>
            <h3 className="text-lg font-semibold text-gray-800 line-clamp-2 mb-2">
              {video.title}
            </h3>
            <div className="flex items-center text-sm text-gray-600 space-x-4">
              <span className="font-medium">{video.channel_title}</span>
              <span>•</span>
              <span>{formatDate(video.published_at)}</span>
              <span>•</span>
              <span>{formatDuration(video.duration)}</span>
              <span>•</span>
              <span>{formatNumber(video.view_count)} views</span>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-full hover:bg-gray-100"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span className="flex items-center">
              <strong className="mr-1">{wordCount.toLocaleString()}</strong> words
            </span>
            <span>•</span>
            <span className="flex items-center">
              <strong className="mr-1">{estimatedReadingTime}</strong> min read
            </span>
            <span>•</span>
            <span className="flex items-center">
              <strong className="mr-1">{video.transcript.length.toLocaleString()}</strong> characters
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={copyToClipboard}
              className="flex items-center px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            >
              {copied ? (
                <>
                  <CheckIcon className="w-4 h-4 mr-1 text-green-600" />
                  Copied!
                </>
              ) : (
                <>
                  <ClipboardDocumentIcon className="w-4 h-4 mr-1" />
                  Copy
                </>
              )}
            </button>

            <button
              onClick={() => downloadTranscript('txt')}
              className="flex items-center px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
            >
              <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
              TXT
            </button>

            <button
              onClick={() => downloadTranscript('json')}
              className="flex items-center px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
            >
              <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
              JSON
            </button>

            <button
              onClick={() => downloadTranscript('csv')}
              className="flex items-center px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200 transition-colors"
            >
              <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
              CSV
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-none">
            <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
              <div className="prose prose-gray max-w-none">
                <div className="whitespace-pre-wrap text-base leading-relaxed text-gray-800 font-medium">
                  {video.transcript}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t bg-gray-50">
          <div className="text-sm text-gray-500">
            <a 
              href={`https://www.youtube.com/watch?v=${video.video_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              Watch on YouTube ↗
            </a>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => downloadTranscript('json')}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center"
            >
              <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
              Download Full Data
            </button>
            
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscriptViewer;