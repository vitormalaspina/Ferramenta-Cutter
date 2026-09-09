import React, { useState } from 'react';
import { useWizard } from '../../context/WizardContext';
import { RadioGroup } from '../ui/Radio';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';
import { Toggle } from '../ui/Toggle';
import { Button } from '../ui/Button';
import { ChevronLeft, ChevronRight, Clock, Sparkles } from 'lucide-react';
import { ClipMode } from '../../types';

export const Step3ClipMode: React.FC = () => {
  const { jobConfig, setJobConfig, setStep } = useWizard();

  // Helper to parse MM:SS string to seconds
  const parseTime = (timeStr: string) => {
    const parts = timeStr.split(':');
    if (parts.length === 2) {
      return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }
    return parseInt(timeStr) || 0;
  };

  // Helper to format seconds to MM:SS
  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const [durationStr, setDurationStr] = useState(formatTime(jobConfig.clip_duration_seconds || 90));

  const handleDurationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value;
    // basic mask
    val = val.replace(/[^0-9:]/g, '');
    setDurationStr(val);
    const secs = parseTime(val);
    if (secs > 0) {
      setJobConfig({ ...jobConfig, clip_duration_seconds: secs });
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Modo de Corte</h2>
      
      <RadioGroup 
        value={jobConfig.clip_mode || 'duration'}
        onChange={(v) => setJobConfig({ ...jobConfig, clip_mode: v as ClipMode })}
        options={[
          {
            value: 'duration',
            label: <div className="flex items-center gap-2"><Clock size={16} /> Cortes por duração fixa</div>,
            description: 'Divide os vídeos em partes iguais de acordo com o tempo configurado.'
          },
          {
            value: 'best_moments',
            label: <div className="flex items-center gap-2"><Sparkles size={16} /> Encontrar melhores momentos com IA</div>,
            description: 'Usa IA para identificar os momentos mais interessantes. (Requer configuração de API, veja README)',
          }
        ]}
      />

      {jobConfig.clip_mode === 'duration' ? (
        <Card className="space-y-4">
          <div className="max-w-xs">
            <Input 
              label="Duração de cada corte (MM:SS)" 
              value={durationStr}
              onChange={handleDurationChange}
              placeholder="01:30"
            />
          </div>
          
          <Toggle 
            checked={!!jobConfig.keep_last_clip}
            onChange={(v) => setJobConfig({ ...jobConfig, keep_last_clip: v })}
            label="Manter último corte"
            description="Se o final do vídeo for menor que a duração configurada, ele será mantido."
          />
        </Card>
      ) : (
        <Card className="space-y-4 opacity-75">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input 
              label="Quantidade de cortes (por vídeo)"
              type="number"
              value={jobConfig.best_moments_count}
              onChange={(e) => setJobConfig({ ...jobConfig, best_moments_count: parseInt(e.target.value) || 5 })}
            />
            <div className="space-y-1">
              <label className="block text-sm font-medium text-zinc-300">Estilo de corte</label>
              <select 
                className="w-full h-10 rounded-lg border border-zinc-700 bg-zinc-900 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-red-500"
                value={jobConfig.best_moments_style}
                onChange={(e) => setJobConfig({ ...jobConfig, best_moments_style: e.target.value as any })}
              >
                <option value="auto">Automático</option>
                <option value="informative">Informativo (Cursos/Tutoriais)</option>
                <option value="funny">Engraçado (Gameplays/Vlogs)</option>
                <option value="controversial">Polêmico (Casts/Entrevistas)</option>
                <option value="emotional">Emocional (Histórias)</option>
                <option value="retention">Alta Retenção (Shorts/TikTok)</option>
              </select>
            </div>
          </div>
        </Card>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
        <Button variant="ghost" onClick={() => setStep(2)}>
          <ChevronLeft size={20} className="mr-1" /> Voltar
        </Button>
        <Button onClick={() => setStep(4)}>
          Continuar <ChevronRight size={20} className="ml-1" />
        </Button>
      </div>
    </div>
  );
};
