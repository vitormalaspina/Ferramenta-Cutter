export type SourceType = 'channel' | 'playlist' | 'video';
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type ClipMode = 'duration' | 'best_moments';
export type OutputFormat = 'original' | '9:16' | '16:9' | '1:1';
export type Resolution = '1080x1920' | '720x1280' | 'auto';
export type Framing = 'center' | 'auto';
export type ZoomMode = 'fixed' | 'auto';
export type SubtitlePosition = 'top' | 'center' | 'bottom';
export type SubtitleLanguage = 'pt' | 'en' | 'es' | 'auto';
export type AudioMode = 'keep' | 'remove';
export type FPS = 'original' | '30' | '60';
export type Quality = 'auto' | 'high' | 'medium' | 'low';
export type BestMomentsStyle = 'informative' | 'funny' | 'controversial' | 'emotional' | 'retention' | 'auto';
export type SortOrder = 'date_desc' | 'date_asc' | 'duration_desc' | 'duration_asc' | 'title_asc';

export interface VideoItem {
  id: string;
  title: string;
  url: string;
  thumbnail: string;
  duration_seconds: number;
  duration_formatted: string;
  published_at: string | null;
  view_count: number | null;
  is_members_only?: boolean;
}

export interface AnalyzeResponse {
  source_id: string;
  source_type: SourceType;
  channel_name: string;
  channel_avatar: string | null;
  total_videos: number;
  videos: VideoItem[];
  page: number;
  total_pages: number;
}

export interface JobConfig {
  source_id: string;
  selected_video_ids: string[];
  clip_mode: ClipMode;
  clip_duration_seconds: number;
  keep_last_clip: boolean;
  output_format: OutputFormat;
  resolution: Resolution;
  framing: Framing;
  zoom_enabled: boolean;
  zoom_intensity: number;
  zoom_mode: ZoomMode;
  subtitles_enabled: boolean;
  subtitle_language: SubtitleLanguage;
  subtitle_font_size: number;
  subtitle_position: SubtitlePosition;
  subtitle_words_per_line: number;
  audio_mode: AudioMode;
  fps: FPS;
  quality: Quality;
  codec: string;
  concurrent_jobs: number;
  best_moments_count: number;
  best_moments_min_duration: number;
  best_moments_max_duration: number;
  best_moments_style: BestMomentsStyle;
}

export interface JobProgress {
  job_id: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  source_url: string;
  channel_name: string;
  total_videos: number;
  videos_done: number;
  current_video_title: string | null;
  current_video_index: number;
  total_clips: number;
  clips_done: number;
  current_clip_index: number;
  current_clip_total: number;
  progress_percent: number;
  estimated_seconds_remaining: number | null;
  stage?: 'download' | 'clip' | 'completed';
  stage_text?: string;
  clip_percent?: number;
  output_path: string | null;
  zip_path: string | null;
  zip_size_bytes: number | null;
  error_msg: string | null;
  video_errors: Array<{video_id: string; title: string; error: string}>;
}

export interface SSEEvent {
  type: 'progress' | 'video_start' | 'clip_progress' | 'video_done' | 'video_error' | 'completed' | 'cancelled' | 'failed';
  [key: string]: unknown;
}
