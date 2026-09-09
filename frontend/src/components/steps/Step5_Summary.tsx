import React, { useState } from 'react';
import { useWizard } from '../../context/WizardContext';
import { api } from '../../api/client';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { ChevronLeft, Play, AlertCircle } from 'lucide-react';
import { JobConfig } from '../../types';

export const Step5Summary: React.FC = () => {
  const { analyzeResult, selectedVideoIds, jobConfig, setJobId, setStep } = useWizard();
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const formatTime = (seconds: number = 0) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleStart = async () => {
    try {
      setIsStarting(true);
      setError(null);
      // Ensure selected videos are passed to config
      const finalConfig = { ...jobConfig, selected_video_ids: selectedVideoIds } as JobConfig;
      const res = await api.createJob(finalConfig);
      setJobId(res.job_id);
      setStep(6);
    } catch (err: any) {
      setError(err.message || 'Falha ao iniciar o processamento');
      setIsStarting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Resumo do Trabalho</h2>
        <p className="text-zinc-400 mt-1">Revise as configurações antes de iniciar</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="space-y-3">
          <h3 className="font-semibold text-lg text-white">Fonte</h3>
          <div className="text-sm">
            <span className="text-zinc-400">Canal: </span>
            <span className="font-medium">{analyzeResult?.channel_name}</span>
          </div>
          <div className="text-sm">
            <span className="text-zinc-400">Vídeos Selecionados: </span>
            <span className="font-medium">{selectedVideoIds.length}</span>
          </div>
          <div className="max-h-32 overflow-y-auto pr-2 space-y-1 mt-2">
            {analyzeResult?.videos.filter(v => selectedVideoIds.includes(v.id)).map(v => (
              <div key={v.id} className="text-xs bg-zinc-800/50 p-1.5 rounded truncate">
                {v.title}
              </div>
            ))}
          </div>
        </Card>

        <Card className="space-y-3">
          <h3 className="font-semibold text-lg text-white">Configurações</h3>
          
          <div className="grid grid-cols-2 gap-y-2 text-sm">
            <div className="text-zinc-400">Modo:</div>
            <div className="font-medium">{jobConfig.clip_mode === 'duration' ? 'Por duração fixa' : 'Melhores momentos (IA)'}</div>
            
            {jobConfig.clip_mode === 'duration' && (
              <>
                <div className="text-zinc-400">Duração do Corte:</div>
                <div className="font-medium">{formatTime(jobConfig.clip_duration_seconds)}</div>
              </>
            )}

            <div className="text-zinc-400">Formato:</div>
            <div className="font-medium uppercase">{jobConfig.output_format} {jobConfig.output_format === '9:16' ? `(${jobConfig.resolution})` : ''}</div>
            
            <div className="text-zinc-400">Zoom:</div>
            <div className="font-medium">{jobConfig.zoom_enabled ? `Sim (${jobConfig.zoom_intensity}%)` : 'Não'}</div>
            
            <div className="text-zinc-400">Legendas (IA):</div>
            <div className="font-medium">{jobConfig.subtitles_enabled ? `Sim (${jobConfig.subtitle_language})` : 'Não'}</div>
            
            <div className="text-zinc-400">FPS / Qualidade:</div>
            <div className="font-medium">{jobConfig.fps} / {jobConfig.quality}</div>
          </div>
        </Card>
      </div>

      {error && (
        <Card className="bg-red-500/10 border-red-500/50 text-red-500 flex items-center gap-2">
          <AlertCircle size={20} />
          {error}
        </Card>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
        <Button variant="ghost" onClick={() => setStep(4)} disabled={isStarting}>
          <ChevronLeft size={20} className="mr-1" /> Voltar
        </Button>
        <Button size="lg" onClick={handleStart} isLoading={isStarting}>
          <Play size={20} className="mr-2" fill="currentColor" /> 
          Iniciar Processamento
        </Button>
      </div>
    </div>
  );
};
