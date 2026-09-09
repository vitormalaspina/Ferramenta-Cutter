import React from 'react';
import { useWizard } from '../../context/WizardContext';
import { api } from '../../api/client';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Download, PlusCircle, History } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Step8Download: React.FC = () => {
  const { jobId, jobProgress, resetWizard } = useWizard();
  const navigate = useNavigate();

  const handleDownload = () => {
    if (jobId) {
      api.downloadZip(jobId);
    }
  };

  const formatSize = (bytes: number | null | undefined) => {
    if (!bytes) return 'Desconhecido';
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 text-center mt-8">
      <div>
        <h2 className="text-3xl font-bold mb-2">Tudo Pronto!</h2>
        <p className="text-zinc-400">Seus cortes estão prontos para download.</p>
      </div>

      <Card className="p-8 flex flex-col items-center bg-zinc-900/80 border-zinc-700 shadow-xl">
        <div className="w-20 h-20 bg-green-500/10 rounded-full flex items-center justify-center mb-6">
          <Download size={40} className="text-green-500" />
        </div>
        
        <h3 className="text-xl font-bold mb-1">Cortes_Gerados.zip</h3>
        <p className="text-zinc-400 mb-6">Tamanho: {formatSize(jobProgress?.zip_size_bytes)}</p>
        
        <Button size="lg" className="w-full max-w-sm" onClick={handleDownload}>
          <Download className="mr-2" size={20} />
          BAIXAR ARQUIVO ZIP
        </Button>
      </Card>

      <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
        <Button variant="secondary" onClick={resetWizard}>
          <PlusCircle className="mr-2" size={18} />
          Novo Trabalho
        </Button>
        <Button variant="ghost" onClick={() => navigate('/history')}>
          <History className="mr-2" size={18} />
          Ver Histórico
        </Button>
      </div>
    </div>
  );
};
