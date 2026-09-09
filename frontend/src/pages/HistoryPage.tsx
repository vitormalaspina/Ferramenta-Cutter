import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { JobProgress } from '../types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import { Trash2, Download, AlertCircle } from 'lucide-react';
import { Dialog } from '../components/ui/Dialog';

export const HistoryPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobToDelete, setJobToDelete] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setIsLoading(true);
      const data = await api.listJobs();
      setJobs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleDelete = async () => {
    if (!jobToDelete) return;
    try {
      await api.deleteJobFiles(jobToDelete);
      setJobs(jobs.filter(j => j.job_id !== jobToDelete));
      setJobToDelete(null);
    } catch (err: any) {
      alert(`Error deleting job: ${err.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'completed': return <Badge variant="success">Concluído</Badge>;
      case 'failed': return <Badge variant="error">Falha</Badge>;
      case 'processing': return <Badge variant="info">Processando</Badge>;
      case 'cancelled': return <Badge variant="warning">Cancelado</Badge>;
      default: return <Badge>Pendente</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Histórico de Trabalhos</h1>
        <Button variant="ghost" onClick={fetchJobs} size="sm">Atualizar</Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner size="lg" /></div>
      ) : error ? (
        <Card className="border-red-500/50 bg-red-500/10 text-red-500 flex items-center gap-3">
          <AlertCircle />
          {error}
        </Card>
      ) : jobs.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">
          Nenhum trabalho encontrado no histórico.
        </div>
      ) : (
        <div className="grid gap-4">
          {jobs.map(job => (
            <Card key={job.job_id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-medium text-lg">{job.channel_name || 'Desconhecido'}</h3>
                  {getStatusBadge(job.status)}
                </div>
                <div className="text-sm text-zinc-400 flex flex-wrap gap-x-4 gap-y-1">
                  <span>Data: {formatDate(job.created_at)}</span>
                  <span>Vídeos: {job.total_videos}</span>
                  <span>Cortes: {job.total_clips}</span>
                  {job.zip_size_bytes && (
                    <span>Tamanho: {(job.zip_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                  )}
                </div>
                {job.error_msg && (
                  <div className="text-sm text-red-400 mt-1 line-clamp-1">{job.error_msg}</div>
                )}
              </div>
              
              <div className="flex items-center gap-2 self-end sm:self-auto">
                {job.status === 'completed' && job.zip_path && (
                  <Button 
                    variant="primary" 
                    size="sm"
                    onClick={() => api.downloadZip(job.job_id)}
                  >
                    <Download size={16} className="mr-2" />
                    Baixar
                  </Button>
                )}
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="text-zinc-400 hover:text-red-500"
                  onClick={() => setJobToDelete(job.job_id)}
                >
                  <Trash2 size={16} />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog 
        isOpen={!!jobToDelete} 
        onClose={() => setJobToDelete(null)}
        title="Excluir trabalho"
      >
        <p className="mb-6">Tem certeza que deseja excluir este trabalho? Os arquivos gerados serão apagados permanentemente.</p>
        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={() => setJobToDelete(null)}>Cancelar</Button>
          <Button variant="danger" onClick={handleDelete}>Excluir</Button>
        </div>
      </Dialog>
    </div>
  );
};
