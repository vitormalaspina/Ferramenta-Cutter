import React from 'react';
import { cn } from './Button';

interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  subLabel?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ value, label, subLabel, className }) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div className={cn('w-full', className)}>
      {(label || subLabel) && (
        <div className="flex justify-between items-center mb-1 text-sm">
          {label && <span className="font-medium text-zinc-200">{label}</span>}
          {subLabel && <span className="text-zinc-400">{subLabel}</span>}
        </div>
      )}
      <div className="w-full bg-zinc-800 rounded-full h-2.5 overflow-hidden">
        <div
          className="bg-red-600 h-2.5 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${clampedValue}%` }}
        ></div>
      </div>
    </div>
  );
};
