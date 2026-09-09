import React from 'react';
import { useWizard } from '../context/WizardContext';
import { cn } from './ui/Button';
import { Check } from 'lucide-react';

const STEPS = [
  'Fonte',
  'Vídeos',
  'Cortes',
  'Config',
  'Resumo',
  'Processando',
  'Concluído',
  'Download'
];

// Steps that can be navigated back to by clicking the indicator
// (not during/after processing)
const NAVIGABLE_STEPS = [1, 2, 3, 4, 5];

export const StepIndicator: React.FC = () => {
  const { step, setStep, jobProgress } = useWizard();

  const handleStepClick = (targetStep: number) => {
    // Only allow navigating back to steps 1-5
    if (!NAVIGABLE_STEPS.includes(targetStep)) return;
    // Don't allow navigating forward past current step
    if (targetStep >= step) return;
    // Don't allow navigating back while a job is actively processing
    if (jobProgress?.status === 'processing') return;
    setStep(targetStep);
  };

  return (
    <div className="w-full py-4">
      <div className="flex items-center justify-between relative">
        <div className="absolute left-0 right-0 top-4 h-0.5 -translate-y-1/2 bg-zinc-800 -z-10 hidden md:block"></div>

        {STEPS.map((label, index) => {
          const stepNum = index + 1;
          const isCompleted = stepNum < step;
          const isCurrent = stepNum === step;
          const isNavigable = NAVIGABLE_STEPS.includes(stepNum) && isCompleted && jobProgress?.status !== 'processing';

          return (
            <div
              key={label}
              className={cn(
                "flex flex-col items-center gap-2 relative bg-zinc-950 px-2",
                isNavigable && "cursor-pointer group"
              )}
              onClick={() => isNavigable && handleStepClick(stepNum)}
              title={isNavigable ? `Voltar para ${label}` : undefined}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border-2 transition-colors",
                  isCompleted
                    ? "bg-red-600 border-red-600 text-white"
                    : isCurrent
                      ? "border-red-500 text-red-500 bg-zinc-950"
                      : "border-zinc-700 text-zinc-500 bg-zinc-950",
                  isNavigable && "group-hover:bg-red-500 group-hover:border-red-500 group-hover:text-white"
                )}
              >
                {isCompleted ? <Check size={16} /> : stepNum}
              </div>
              <span
                className={cn(
                  "text-xs font-medium hidden md:block transition-colors",
                  isCompleted ? "text-zinc-300" : isCurrent ? "text-red-500" : "text-zinc-600",
                  isNavigable && "group-hover:text-white"
                )}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
