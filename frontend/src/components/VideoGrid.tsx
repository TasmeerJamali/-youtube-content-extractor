import React from 'react';
import { VideoResult } from '../types/api';
import VideoCard from './VideoCard';

interface VideoGridProps {
  videos: VideoResult[];
  onVideoSelect?: (video: VideoResult) => void;
  showTranscripts?: boolean;
  showComments?: boolean;
}

const VideoGrid: React.FC<VideoGridProps> = ({
  videos,
  onVideoSelect,
  showTranscripts = false,
  showComments = false
}) => {
  if (!videos || videos.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No videos found</p>
      </div>
    );
  }

  return (
    <div className="search-results-grid">
      {videos.map((video) => (
        <VideoCard
          key={video.video_id}
          video={video}
          onSelect={onVideoSelect}
          showTranscript={showTranscripts}
          showComments={showComments}
        />
      ))}
    </div>
  );
};

export default VideoGrid;