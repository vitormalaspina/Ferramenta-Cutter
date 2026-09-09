import React, { useState } from 'react';
import { useWizard } from '../../context/WizardContext';
import { api } from '../../api/client';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Youtube, Search, AlertCircle } from 'lucide-react';

export const Step1Source: React.FC = () => {
  const { setAnalyzeResult, setStep, setJobConfig } = useWizard();
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    try {
      setIsLoading(true);
      setError(null);
      const result = await api.analyze(url);
      setAnalyzeResult(result);
      setJobConfig(prev => ({ ...prev, source_id: result.source_id }));
      setStep(2);
    } catch (err: any) {
      setError(err.message || 'Falha ao analisar a URL. Verifique se ela é válida.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center max-w-2xl mx-auto w-full h-full min-h-[400px]">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <Youtube className="text-red-500" size={32} />
        </div>
        <h1 className="text-3xl font-bold mb-2">Novo Trabalho</h1>
        <p className="text-zinc-400">Insira a URL de um canal, playlist ou vídeo do YouTube</p>
      </div>

      <Card className="w-full">
        <form onSubmit={handleAnalyze} className="flex flex-col gap-4">
          <Input
            placeholder="https://www.youtube.com/@Canal..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
            className="text-lg py-6"
            autoFocus
          />
          
          {error && (
            <div className="flex items-center gap-2 text-red-500 text-sm bg-red-500/10 p-3 rounded-lg">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <Button 
            type="submit" 
            size="lg" 
            className="w-full"
            isLoading={isLoading}
            disabled={!url.trim()}
          >
            <Search className="mr-2" size={20} />
            {isLoading ? 'Analisando...' : 'Analisar'}
          </Button>
        </form>
      </Card>
    </div>
  );
};
