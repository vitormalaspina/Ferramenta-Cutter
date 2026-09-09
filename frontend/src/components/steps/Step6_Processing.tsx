import React, { useEffect, useState, useCallback } from 'react';
import { useWizard } from '../../context/WizardContext';
import { useSSE } from '../../hooks/useSSE';
import { api } from '../../api/client';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { ProgressBar } from '../ui/ProgressBar';
import { Dialog } from '../ui/Dialog';
import { Loader2, AlertTriangle, XCircle, Download, Scissors } from 'lucide-react';
import { SSEEvent, JobProgress } from '../../types';

export const Step6Processing: React.FC = () => {
  const { jobId, jobProgress, setJobProgress, setStep } = useWizard();
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  // Fetch initial status when mounting
  useEffect(() => {
    if (jobId) {
      api.getJob(jobId).then(data => setJobProgress(data)).catch(console.error);
    }
  }, [jobId]);

  // Fallback poller every 5 seconds in case SSE drops
  useEffect(() => {
    if (!jobId) return;
    const timer = setInterval(() => {
      if (jobProgress?.status === 'processing') {
        api.getJob(jobId).then(data => {
          if (data.status === 'completed') {
            setJobProgress(data);
            setStep(7);
          } else if (data.status === 'failed' || data.status === 'cancelled') {
            setJobProgress(data);
          }
        }).catch(() => {});
      }
    }, 5000);

    return () => clearInterval(timer);
  }, [jobId, jobProgress?.status]);

  const handleSSEEvent = useCallback((event: SSEEvent) => {
    if (event.type === 'progress') {
      setJobProgress(prev => {
        if (!prev) return event as unknown as JobProgress;
        return {
          ...prev,
          status: (event.status as any) || prev.status,
          total_videos: (event.total_videos as number) ?? prev.total_videos,
          videos_done: (event.videos_done as number) ?? prev.videos_done,
          current_video_title: (event.current_video_title as string) ?? prev.current_video_title,
          current_video_index: (event.current_video_index as number) ?? prev.current_video_index,
          current_clip_index: (event.current_clip_index as number) ?? prev.current_clip_index,
          current_clip_total: (event.current_clip_total as number) ?? prev.current_clip_total,
          progress_percent: (event.progress_percent as number) ?? prev.progress_percent,
          estimated_seconds_remaining: event.estimated_seconds_remaining !== undefined ? (event.estimated_seconds_remaining as number | null) : prev.estimated_seconds_remaining,
          stage: (event.stage as any) ?? prev.stage,
          stage_text: (event.stage_text as string) ?? prev.stage_text,
          clip_percent: (event.clip_percent as number) ?? prev.clip_percent,
        };
      });
    } else if (event.type === 'video_done') {
      setJobProgress(prev => prev ? {
        ...prev,
        videos_done: (event.videos_done as number) ?? (prev.videos_done + 1),
        progress_percent: (event.progress_percent as number) ?? prev.progress_percent,
      } : null);
    } else if (event.type === 'completed') {
      if (jobId) {
        api.getJob(jobId).then(data => {
          setJobProgress(data);
          setStep(7);
        }).catch(() => setStep(7));
      } else {
        setStep(7);
      }
    } else if (event.type === 'cancelled') {
      setJobProgress(prev => prev ? { ...prev, status: 'cancelled' } : null);
    } else if (event.type === 'failed') {
      setJobProgress(prev => prev ? {
        ...prev,
        status: 'failed',
        error_msg: (event.error as string) || prev.error_msg
      } : null);
    }
  }, [jobId, setJobProgress, setStep]);

  useSSE(jobId, handleSSEEvent);

  const handleCancel = async () => {
    if (!jobId) return;
    try {
      setIsCancelling(true);
      await api.cancelJob(jobId);
      setShowCancelDialog(false);
      const data = await api.getJob(jobId);
      setJobProgress(data);
    } catch (err: any) {
      alert(`Erro ao cancelar: ${err.message}`);
    } finally {
      setIsCancelling(false);
    }
  };

  const formatETA = (secs: number | null | undefined) => {
    if (secs === null || secs === undefined || secs < 0) return 'Calculando...';
    if (secs === 0) return 'Quase pronto...';
    if (secs < 60) return `${Math.ceil(secs)}s`;
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}m ${s}s`;
  };

  if (!jobProgress) {
    return (
      <div className="flex flex-col items-center py-20">
        <Loader2 className="animate-spin mb-4 text-red-500" size={36} />
        <span className="text-zinc-400">Conectando ao processamento...</span>
      </div>
    );
  }

  const isFailed = jobProgress.status === 'failed';
  const isCancelled = jobProgress.status === 'cancelled';

  if (isFailed || isCancelled) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12 space-y-6">
        <XCircle size={64} className="text-red-500" />
        <div>
          <h2 className="text-2xl font-bold mb-2">
            {isFailed ? 'Processamento Falhou' : 'Processamento Cancelado'}
          </h2>
          {jobProgress.error_msg && (
            <p className="text-red-400 bg-red-500/10 p-4 rounded-lg mt-4 max-w-lg mx-auto text-sm">
              {jobProgress.error_msg}
            </p>
          )}
        </div>
        <div className="flex gap-3 flex-wrap justify-center">
          <Button onClick={() => setStep(5)} variant="secondary">
            ← Voltar para Configurações
          </Button>
          <Button onClick={() => setStep(1)} variant="ghost">
            Iniciar Novo Trabalho
          </Button>
        </div>
      </div>
    );
  }

  const isDownload = jobProgress.stage === 'download';
  const clipPercent = jobProgress.clip_percent ?? 0;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <Loader2 className="animate-spin mx-auto text-red-500" size={48} />
        <h2 className="text-2xl font-bold">Processando Cortes...</h2>
        <p className="text-zinc-400">
          {jobProgress.stage_text || 'Baixando e gerando cortes no formato vertical 9:16...'}
        </p>
      </div>

      <Card className="space-y-6">
        {/* Overall Progress */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="font-semibold text-white">Progresso Geral</span>
            <span className="text-zinc-400 font-mono text-xs">
              Vídeos: {jobProgress.videos_done} / {jobProgress.total_videos}
            </span>
          </div>
          <ProgressBar
            value={jobProgress.progress_percent || 0}
            className="h-4"
          />
          <div className="flex justify-between text-xs text-zinc-400 mt-2 font-medium">
            <span className="text-red-400 font-semibold">{Math.round(jobProgress.progress_percent || 0)}% Concluído</span>
            <span>Tempo restante: {formatETA(jobProgress.estimated_seconds_remaining)}</span>
          </div>
        </div>

        {/* Current Active Video & Step Details */}
        {jobProgress.current_video_title && (
          <div className="bg-zinc-800/40 p-4 rounded-lg border border-zinc-700/60 space-y-3">
            <div className="flex items-center justify-between text-xs text-zinc-400">
              <span>Vídeo Atual ({jobProgress.current_video_index} de {jobProgress.total_videos})</span>
              <span className="flex items-center gap-1 text-zinc-300 font-medium">
                {isDownload ? (
                  <>
                    <Download size={14} className="text-blue-400 animate-pulse" />
                    Download em andamento
                  </>
                ) : (
                  <>
                    <Scissors size={14} className="text-red-400" />
                    Gerando corte {jobProgress.current_clip_index} de {jobProgress.current_clip_total || '?'}
                  </>
                )}
              </span>
            </div>

            <div className="font-medium text-white text-sm line-clamp-1" title={jobProgress.current_video_title}>
              {jobProgress.current_video_title}
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs text-zinc-400">
                <span>{jobProgress.stage_text || (isDownload ? 'Baixando stream do YouTube...' : 'Renderizando clipes...')}</span>
                <span className="font-mono text-white">{clipPercent}%</span>
              </div>
              <ProgressBar
                value={clipPercent}
                className="h-2"
              />
            </div>
          </div>
        )}

        {/* Non-fatal Errors */}
        {jobProgress.video_errors && jobProgress.video_errors.length > 0 && (
          <div className="mt-4 pt-4 border-t border-zinc-800">
            <div className="flex items-center gap-2 text-yellow-500 text-sm mb-2 font-medium">
              <AlertTriangle size={16} /> Avisos / Erros ({jobProgress.video_errors.length})
            </div>
            <div className="max-h-24 overflow-y-auto text-xs space-y-1">
              {jobProgress.video_errors.map((err, i) => (
                <div key={i} className="text-zinc-400">
                  <span className="text-zinc-300 font-medium">[{err.title}]</span>: {err.error}
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <div className="flex justify-center">
        <Button variant="ghost" className="text-zinc-500 hover:text-red-400" onClick={() => setShowCancelDialog(true)}>
          Cancelar Processamento
        </Button>
      </div>

      <Dialog
        isOpen={showCancelDialog}
        onClose={() => setShowCancelDialog(false)}
        title="Cancelar Processamento"
      >
        <p className="mb-6 text-zinc-300">Tem certeza que deseja cancelar? O progresso atual será perdido e nenhum arquivo final será gerado.</p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setShowCancelDialog(false)}>Continuar Processando</Button>
          <Button variant="danger" onClick={handleCancel} isLoading={isCancelling}>Sim, Cancelar</Button>
        </div>
      </Dialog>
    </div>
  );
};
