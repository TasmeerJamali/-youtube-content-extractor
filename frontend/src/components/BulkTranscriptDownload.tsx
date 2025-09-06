import React from 'react';
import { ArrowDownTrayIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { VideoResult } from '../types/api';

interface BulkTranscriptDownloadProps {
  videos: VideoResult[];
  searchQuery?: string;
}

const BulkTranscriptDownload: React.FC<BulkTranscriptDownloadProps> = ({
  videos,
  searchQuery
}) => {
  const videosWithTranscripts = videos.filter(video => video.transcript);
  
  if (videosWithTranscripts.length === 0) {
    return null;
  }

  const downloadAllTranscripts = async (format: 'txt' | 'json') => {
    if (format === 'json') {
      // Single JSON file with all transcripts
      const allData = {
        search_query: searchQuery || 'Unknown',
        exported_at: new Date().toISOString(),
        total_videos: videosWithTranscripts.length,
        total_words: videosWithTranscripts.reduce((acc, v) => acc + (v.transcript?.split(' ').length || 0), 0),
        videos: videosWithTranscripts.map(video => ({
          video_metadata: {
            video_id: video.video_id,
            title: video.title,
            channel_title: video.channel_title,
            published_at: video.published_at,
            url: `https://www.youtube.com/watch?v=${video.video_id}`,
            view_count: video.view_count,
            relevance_score: video.relevance_score
          },
          transcript: video.transcript,
          word_count: video.transcript?.split(' ').length || 0
        }))
      };
      
      const blob = new Blob([JSON.stringify(allData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `all_transcripts_${searchQuery?.replace(/[^a-zA-Z0-9]/g, '_') || 'search'}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
    } else if (format === 'txt') {
      // Single TXT file with all transcripts
      let content = 'BULK TRANSCRIPT EXPORT\n' + '='.repeat(80) + '\n\n';
      content += `Search Query: ${searchQuery || 'Unknown'}\n`;
      content += `Exported: ${new Date().toLocaleString()}\n`;
      content += `Total Videos: ${videosWithTranscripts.length}\n\n`;
      content += '='.repeat(80) + '\n\n';
      
      videosWithTranscripts.forEach((video, index) => {
        content += `VIDEO ${index + 1}\n`;
        content += '='.repeat(40) + '\n';
        content += `Title: ${video.title}\n`;
        content += `Channel: ${video.channel_title}\n`;
        content += `Published: ${video.published_at}\n`;
        content += `URL: https://www.youtube.com/watch?v=${video.video_id}\n`;
        content += `Words: ${video.transcript?.split(' ').length || 0}\n\n`;
        content += video.transcript + '\n\n';
        content += '='.repeat(80) + '\n\n';
      });
      
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `all_transcripts_${searchQuery?.replace(/[^a-zA-Z0-9]/g, '_') || 'search'}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center text-sm text-gray-600">
        <DocumentTextIcon className="w-4 h-4 mr-1" />
        <span>{videosWithTranscripts.length} transcripts available</span>
      </div>
      
      <div className="flex items-center space-x-1">
        <span className="text-xs text-gray-500">Download all:</span>
        
        <button
          onClick={() => downloadAllTranscripts('txt')}
          className="flex items-center px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
          title="Download all transcripts as single TXT file"
        >
          <ArrowDownTrayIcon className="w-3 h-3 mr-1" />
          TXT
        </button>
        
        <button
          onClick={() => downloadAllTranscripts('json')}
          className="flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
          title="Download all transcripts as single JSON file"
        >
          <ArrowDownTrayIcon className="w-3 h-3 mr-1" />
          JSON
        </button>
      </div>
    </div>
  );
};

export default BulkTranscriptDownload;