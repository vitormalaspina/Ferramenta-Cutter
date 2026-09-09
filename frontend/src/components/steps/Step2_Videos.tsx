import React, { useState, useEffect } from 'react';
import { useWizard } from '../../context/WizardContext';
import { api } from '../../api/client';
import { VideoItem } from '../../types';
import { VideoCard } from '../VideoCard';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';
import { Spinner } from '../ui/Spinner';
import { Search, ChevronRight, ChevronLeft } from 'lucide-react';

export const Step2Videos: React.FC = () => {
  const { analyzeResult, selectedVideoIds, setSelectedVideoIds, setStep } = useWizard();
  
  const [videos, setVideos] = useState<VideoItem[]>(analyzeResult?.videos || []);
  const [page, setPage] = useState(analyzeResult?.page || 1);
  const [totalPages, setTotalPages] = useState(analyzeResult?.total_pages || 1);
  
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('date_desc');
  const [isLoading, setIsLoading] = useState(false);

  const fetchVideos = async (p: number, sSearch: string, sSort: string) => {
    if (!analyzeResult?.source_id) return;
    try {
      setIsLoading(true);
      const res = await api.getVideos(analyzeResult.source_id, p, sSearch, sSort);
      if (p === 1) {
        setVideos(res.videos);
      } else {
        setVideos(prev => [...prev, ...res.videos]);
      }
      setPage(res.page);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle search and sort changes
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchVideos(1, search, sort);
    }, 500);
    return () => clearTimeout(timer);
  }, [search, sort]);

  const handleToggle = (id: string) => {
    setSelectedVideoIds(prev => 
      prev.includes(id) ? prev.filter(vid => vid !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    const allIds = new Set([...selectedVideoIds, ...videos.map(v => v.id)]);
    setSelectedVideoIds(Array.from(allIds));
  };

  const handleDeselectAll = () => {
    setSelectedVideoIds([]);
  };

  const handleSelectFirstN = (n: number) => {
    const newSelection = videos.slice(0, n).map(v => v.id);
    setSelectedVideoIds(Array.from(new Set([...selectedVideoIds, ...newSelection])));
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex items-center gap-4 bg-zinc-900/50 p-4 rounded-xl border border-zinc-800">
        {analyzeResult?.channel_avatar && (
          <img src={analyzeResult.channel_avatar} alt="Avatar" className="w-12 h-12 rounded-full" />
        )}
        <div>
          <h2 className="text-lg font-bold">{analyzeResult?.channel_name || 'Desconhecido'}</h2>
          <p className="text-sm text-zinc-400">{analyzeResult?.total_videos} vídeos encontrados</p>
        </div>
      </div>

      <Card className="flex flex-col md:flex-row gap-4 items-end">
        <div className="flex-1 w-full">
          <Input 
            placeholder="Buscar por título..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search size={18} className="text-zinc-500" />}
          />
        </div>
        <div className="w-full md:w-48">
          <select 
            className="w-full h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-red-500"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="date_desc">Mais recentes</option>
            <option value="date_asc">Mais antigos</option>
            <option value="duration_desc">Mais longos</option>
            <option value="duration_asc">Mais curtos</option>
            <option value="title_asc">A-Z</option>
          </select>
        </div>
      </Card>

      <div className="flex flex-wrap gap-2 items-center">
        <Button variant="secondary" size="sm" onClick={handleSelectAll}>Selecionar Tudo</Button>
        <Button variant="ghost" size="sm" onClick={handleDeselectAll}>Limpar</Button>
        <div className="h-4 w-px bg-zinc-700 mx-2"></div>
        <Button variant="secondary" size="sm" onClick={() => handleSelectFirstN(5)}>Primeiros 5</Button>
        <Button variant="secondary" size="sm" onClick={() => handleSelectFirstN(10)}>Primeiros 10</Button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 min-h-[300px] border border-zinc-800 p-2 rounded-xl bg-zinc-950">
        {videos.map(video => (
          <VideoCard 
            key={video.id} 
            video={video} 
            isSelected={selectedVideoIds.includes(video.id)}
            onToggle={handleToggle}
          />
        ))}
        {isLoading && <div className="flex justify-center py-4"><Spinner /></div>}
        {page < totalPages && !isLoading && (
          <Button 
            variant="ghost" 
            className="w-full" 
            onClick={() => fetchVideos(page + 1, search, sort)}
          >
            Carregar mais
          </Button>
        )}
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
        <div>
          <Button variant="ghost" onClick={() => setStep(1)}>
            <ChevronLeft size={20} className="mr-1" /> Voltar
          </Button>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">
            {selectedVideoIds.length} {selectedVideoIds.length === 1 ? 'vídeo selecionado' : 'vídeos selecionados'}
          </span>
          <Button 
            onClick={() => setStep(3)} 
            disabled={selectedVideoIds.length === 0}
          >
            Continuar <ChevronRight size={20} className="ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
};
