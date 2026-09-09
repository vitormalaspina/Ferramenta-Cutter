import React, { useState } from 'react';
import { useWizard } from '../../context/WizardContext';
import { api } from '../../api/client';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { CheckCircle2, FileArchive, AlertTriangle } from 'lucide-react';

export const Step7Complete: React.FC = () => {
  const { jobId, jobProgress, setJobProgress, setStep } = useWizard();
  const [isZipping, setIsZipping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateZip = async () => {
    if (!jobId) return;
    try {
      setIsZipping(true);
      setError(null);
      await api.generateZip(jobId);
      // Fetch latest job info to get zip path and size
      const data = await api.getJob(jobId);
      setJobProgress(data);
      setStep(8);
    } catch (err: any) {
      setError(err.message || 'Falha ao gerar o arquivo ZIP');
    } finally {
      setIsZipping(false);
    }
  };

  const hasClips = (jobProgress?.total_clips || 0) > 0;

  return (
    <div className="max-w-2xl mx-auto space-y-6 text-center">
      <CheckCircle2 size={80} className={hasClips ? "text-green-500 mx-auto" : "text-amber-500 mx-auto"} />
      
      <div>
        <h2 className="text-3xl font-bold mb-2">
          {hasClips ? 'Processamento Concluído!' : 'Processamento Finalizado com Avisos'}
        </h2>
        <p className="text-zinc-400">
          {hasClips 
            ? 'Todos os cortes foram gerados com sucesso.' 
            : 'Nenhum corte pôde ser gerado para os vídeos selecionados.'}
        </p>
      </div>

      <Card className="grid grid-cols-2 gap-4 text-left p-6">
        <div>
          <div className="text-3xl font-bold text-white">{jobProgress?.videos_done || 0}</div>
          <div className="text-sm text-zinc-400 font-medium">Vídeos Processados</div>
        </div>
        <div>
          <div className="text-3xl font-bold text-white">{jobProgress?.total_clips || 0}</div>
          <div className="text-sm text-zinc-400 font-medium">Cortes Gerados</div>
        </div>
      </Card>

      {jobProgress?.video_errors && jobProgress.video_errors.length > 0 && (
        <Card className="text-left bg-yellow-500/5 border-yellow-500/20">
          <div className="flex items-center gap-2 text-yellow-500 font-medium mb-2">
            <AlertTriangle size={18} /> Atenção: Alguns erros ocorreram
          </div>
          <div className="max-h-36 overflow-y-auto text-sm space-y-2">
            {jobProgress.video_errors.map((err, i) => (
              <div key={i} className="text-zinc-400">
                <strong className="text-zinc-300">{err.title}</strong>: {err.error}
              </div>
            ))}
          </div>
        </Card>
      )}

      {error && (
        <div className="text-red-500 text-sm bg-red-500/10 p-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="pt-6 flex gap-3 justify-center flex-wrap">
        {hasClips ? (
          <Button size="lg" className="w-full sm:w-auto" onClick={handleGenerateZip} isLoading={isZipping}>
            <FileArchive className="mr-2" size={20} />
            {isZipping ? 'Compactando arquivos...' : 'Gerar Arquivo ZIP'}
          </Button>
        ) : (
          <Button size="lg" variant="secondary" onClick={() => setStep(2)}>
            ← Escolher Outros Vídeos
          </Button>
        )}
      </div>
    </div>
  );
};
