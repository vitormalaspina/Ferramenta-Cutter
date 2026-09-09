import React from 'react';
import { useWizard } from '../../context/WizardContext';
import { Card } from '../ui/Card';
import { Toggle } from '../ui/Toggle';
import { Button } from '../ui/Button';
import { Collapsible } from '../ui/Collapsible';
import { ChevronLeft, ChevronRight, Smartphone, Monitor, Square } from 'lucide-react';

export const Step4Config: React.FC = () => {
  const { jobConfig, setJobConfig, setStep } = useWizard();

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Configurações Visuais</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="space-y-4">
          <h3 className="font-medium">Formato e Resolução</h3>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setJobConfig({ ...jobConfig, output_format: '9:16' })}
              className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-colors ${
                jobConfig.output_format === '9:16' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 bg-zinc-900/50 hover:border-zinc-500'
              }`}
            >
              <Smartphone size={24} />
              <span className="text-xs">9:16 (Shorts/Reels)</span>
            </button>
            <button
              onClick={() => setJobConfig({ ...jobConfig, output_format: '16:9' })}
              className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-colors ${
                jobConfig.output_format === '16:9' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 bg-zinc-900/50 hover:border-zinc-500'
              }`}
            >
              <Monitor size={24} />
              <span className="text-xs">16:9 (Padrão)</span>
            </button>
            <button
              onClick={() => setJobConfig({ ...jobConfig, output_format: '1:1' })}
              className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-colors ${
                jobConfig.output_format === '1:1' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 bg-zinc-900/50 hover:border-zinc-500'
              }`}
            >
              <Square size={24} />
              <span className="text-xs">1:1 (Feed)</span>
            </button>
            <button
              onClick={() => setJobConfig({ ...jobConfig, output_format: 'original' })}
              className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-colors ${
                jobConfig.output_format === 'original' ? 'border-red-500 bg-red-500/10' : 'border-zinc-700 bg-zinc-900/50 hover:border-zinc-500'
              }`}
            >
              <span className="text-2xl font-bold mt-1">Orig</span>
              <span className="text-xs">Manter Original</span>
            </button>
          </div>

          {jobConfig.output_format === '9:16' && (
            <div className="pt-2">
              <label className="block text-sm font-medium text-zinc-300 mb-1">Resolução</label>
              <select 
                className="w-full h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-white"
                value={jobConfig.resolution}
                onChange={(e) => setJobConfig({ ...jobConfig, resolution: e.target.value as any })}
              >
                <option value="1080x1920">1080x1920 (FHD)</option>
                <option value="720x1280">720x1280 (HD)</option>
                <option value="auto">Auto (Origem)</option>
              </select>
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <h3 className="font-medium">Efeitos e Legendas</h3>
          
          <Toggle 
            checked={!!jobConfig.zoom_enabled}
            onChange={(v) => setJobConfig({ ...jobConfig, zoom_enabled: v })}
            label="Zoom (Pan & Scan)"
            description="Aplica um leve zoom animado para dar movimento."
          />
          {jobConfig.zoom_enabled && (
            <div className="pl-4 border-l-2 border-zinc-800 space-y-3 pt-2">
              <div>
                <label className="flex justify-between text-xs text-zinc-400 mb-1">
                  <span>Intensidade: {jobConfig.zoom_intensity}%</span>
                </label>
                <input 
                  type="range" 
                  min="5" max="50" 
                  className="w-full accent-red-500"
                  value={jobConfig.zoom_intensity}
                  onChange={(e) => setJobConfig({ ...jobConfig, zoom_intensity: parseInt(e.target.value) })}
                />
              </div>
            </div>
          )}

          <div className="h-px bg-zinc-800 my-4" />

          <Toggle 
            checked={!!jobConfig.subtitles_enabled}
            onChange={(v) => setJobConfig({ ...jobConfig, subtitles_enabled: v })}
            label="Gerar Legendas (IA)"
            description="Transcreve o áudio usando Whisper e sobrepõe no vídeo."
          />
          {jobConfig.subtitles_enabled && (
            <div className="pl-4 border-l-2 border-zinc-800 space-y-3 pt-2">
              <select 
                className="w-full h-8 rounded-lg border border-zinc-700 bg-zinc-900 px-2 text-sm text-white"
                value={jobConfig.subtitle_language}
                onChange={(e) => setJobConfig({ ...jobConfig, subtitle_language: e.target.value as any })}
              >
                <option value="pt">Português (Brasil)</option>
                <option value="en">Inglês</option>
                <option value="es">Espanhol</option>
                <option value="auto">Auto Detectar</option>
              </select>
            </div>
          )}
        </Card>
      </div>

      <Collapsible title="Opções Avançadas">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1">FPS (Quadros por segundo)</label>
            <select 
              className="w-full h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-white"
              value={jobConfig.fps}
              onChange={(e) => setJobConfig({ ...jobConfig, fps: e.target.value as any })}
            >
              <option value="original">Manter Original</option>
              <option value="30">30 FPS</option>
              <option value="60">60 FPS</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1">Qualidade de Codificação</label>
            <select 
              className="w-full h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-white"
              value={jobConfig.quality}
              onChange={(e) => setJobConfig({ ...jobConfig, quality: e.target.value as any })}
            >
              <option value="high">Alta (Arquivos maiores)</option>
              <option value="medium">Média (Balanceado)</option>
              <option value="low">Baixa (Mais rápido)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-1">Processos simultâneos (Vídeos)</label>
            <select 
              className="w-full h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-white"
              value={jobConfig.concurrent_jobs}
              onChange={(e) => setJobConfig({ ...jobConfig, concurrent_jobs: parseInt(e.target.value) })}
            >
              <option value="1">1 (Mais seguro)</option>
              <option value="2">2 (Recomendado)</option>
              <option value="4">4 (Requer PC forte)</option>
            </select>
          </div>
          <div>
             <label className="block text-sm font-medium text-zinc-300 mb-1">Áudio</label>
             <select 
              className="w-full h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-white"
              value={jobConfig.audio_mode}
              onChange={(e) => setJobConfig({ ...jobConfig, audio_mode: e.target.value as any })}
            >
              <option value="keep">Manter</option>
              <option value="remove">Remover (Mudo)</option>
            </select>
          </div>
        </div>
      </Collapsible>

      <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
        <Button variant="ghost" onClick={() => setStep(3)}>
          <ChevronLeft size={20} className="mr-1" /> Voltar
        </Button>
        <Button onClick={() => setStep(5)}>
          Continuar <ChevronRight size={20} className="ml-1" />
        </Button>
      </div>
    </div>
  );
};
