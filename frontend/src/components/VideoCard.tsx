import React from 'react';
import { VideoItem } from '../types';
import { CheckCircle2, Circle, Clock, Calendar, Eye, Lock } from 'lucide-react';
import { cn } from './ui/Button';

interface VideoCardProps {
  video: VideoItem;
  isSelected: boolean;
  onToggle: (id: string) => void;
}

export const VideoCard: React.FC<VideoCardProps> = ({ video, isSelected, onToggle }) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };

  const formatViewCount = (count: number | null) => {
    if (count === null) return '';
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M visualizações`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K visualizações`;
    return `${count} visualizações`;
  };

  return (
    <div 
      className={cn(
        "group flex flex-col sm:flex-row gap-4 p-4 rounded-xl border transition-all cursor-pointer hover:bg-zinc-800/50",
        isSelected ? "border-red-500 bg-red-500/5" : "border-zinc-800 bg-zinc-900/30"
      )}
      onClick={() => onToggle(video.id)}
    >
      <div className="relative aspect-video w-full sm:w-48 flex-shrink-0 overflow-hidden rounded-lg bg-zinc-800">
        <img 
          src={video.thumbnail} 
          alt={video.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCBmaWxsPSIjMmQzNzQ4IiB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIvPjwvc3ZnPg==';
          }}
        />
        {video.is_members_only && (
          <div className="absolute top-2 left-2 bg-amber-500 text-zinc-950 font-bold px-2 py-0.5 rounded text-xs flex items-center gap-1 shadow-md">
            <Lock size={11} />
            Membros
          </div>
        )}
        <div className="absolute bottom-2 right-2 bg-black/80 px-1.5 py-0.5 rounded text-xs text-white font-medium flex items-center gap-1">
          <Clock size={12} />
          {video.duration_formatted}
        </div>
      </div>
      
      <div className="flex-1 min-w-0 flex flex-col">
        <div className="flex justify-between items-start gap-2">
          <h3 className="text-sm sm:text-base font-medium text-white line-clamp-2" title={video.title}>
            {video.title}
          </h3>
          <button 
            className="text-zinc-400 flex-shrink-0 focus:outline-none"
            onClick={(e) => {
              e.stopPropagation();
              onToggle(video.id);
            }}
          >
            {isSelected ? (
              <CheckCircle2 className="text-red-500" fill="currentColor" size={24} />
            ) : (
              <Circle size={24} className="group-hover:text-zinc-300 transition-colors" />
            )}
          </button>
        </div>
        
        <div className="mt-auto pt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-400">
          {video.published_at && (
            <div className="flex items-center gap-1">
              <Calendar size={12} />
              {formatDate(video.published_at)}
            </div>
          )}
          {video.view_count !== null && (
            <div className="flex items-center gap-1">
              <Eye size={12} />
              {formatViewCount(video.view_count)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
