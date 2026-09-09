import React, { createContext, useContext, useState, ReactNode } from 'react';
import { AnalyzeResponse, JobConfig, JobProgress } from '../types';

interface WizardContextType {
  step: number;
  setStep: React.Dispatch<React.SetStateAction<number>>;
  analyzeResult: AnalyzeResponse | null;
  setAnalyzeResult: React.Dispatch<React.SetStateAction<AnalyzeResponse | null>>;
  selectedVideoIds: string[];
  setSelectedVideoIds: React.Dispatch<React.SetStateAction<string[]>>;
  jobConfig: Partial<JobConfig>;
  setJobConfig: React.Dispatch<React.SetStateAction<Partial<JobConfig>>>;
  jobId: string | null;
  setJobId: React.Dispatch<React.SetStateAction<string | null>>;
  jobProgress: JobProgress | null;
  setJobProgress: React.Dispatch<React.SetStateAction<JobProgress | null>>;
  resetWizard: () => void;
}

const WizardContext = createContext<WizardContextType | undefined>(undefined);

export const WizardProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [step, setStep] = useState(1);
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResponse | null>(null);
  const [selectedVideoIds, setSelectedVideoIds] = useState<string[]>([]);
  const [jobConfig, setJobConfig] = useState<Partial<JobConfig>>({
    clip_mode: 'duration',
    clip_duration_seconds: 90,
    keep_last_clip: false,
    output_format: '9:16',
    resolution: '1080x1920',
    framing: 'center',
    zoom_enabled: false,
    zoom_intensity: 15,
    zoom_mode: 'fixed',
    subtitles_enabled: false,
    subtitle_language: 'pt',
    subtitle_font_size: 24,
    subtitle_position: 'center',
    subtitle_words_per_line: 5,
    audio_mode: 'keep',
    fps: 'original',
    quality: 'high',
    codec: 'h264',
    concurrent_jobs: 2,
    best_moments_count: 5,
    best_moments_min_duration: 30,
    best_moments_max_duration: 90,
    best_moments_style: 'auto'
  });
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<JobProgress | null>(null);

  const resetWizard = () => {
    setStep(1);
    setAnalyzeResult(null);
    setSelectedVideoIds([]);
    setJobId(null);
    setJobProgress(null);
  };

  return (
    <WizardContext.Provider value={{
      step, setStep,
      analyzeResult, setAnalyzeResult,
      selectedVideoIds, setSelectedVideoIds,
      jobConfig, setJobConfig,
      jobId, setJobId,
      jobProgress, setJobProgress,
      resetWizard
    }}>
      {children}
    </WizardContext.Provider>
  );
};

export const useWizard = () => {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error('useWizard must be used within a WizardProvider');
  }
  return context;
};
