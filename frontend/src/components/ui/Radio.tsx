import React from 'react';
import { cn } from './Button';

interface RadioOption {
  label: string | React.ReactNode;
  value: string;
  description?: string;
  disabled?: boolean;
}

interface RadioGroupProps {
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
  layout?: 'vertical' | 'horizontal';
}

export const RadioGroup: React.FC<RadioGroupProps> = ({ options, value, onChange, className, layout = 'vertical' }) => {
  return (
    <div className={cn('space-y-3', layout === 'horizontal' && 'flex space-y-0 space-x-4', className)}>
      {options.map((option) => (
        <label
          key={option.value}
          className={cn(
            'flex cursor-pointer items-start space-x-3 rounded-lg border p-4 transition-colors',
            value === option.value
              ? 'border-red-500 bg-red-500/5'
              : 'border-zinc-800 hover:border-zinc-700 bg-zinc-900/50',
            option.disabled && 'opacity-50 cursor-not-allowed'
          )}
        >
          <div className="flex h-5 items-center">
            <input
              type="radio"
              className="h-4 w-4 border-zinc-700 bg-zinc-800 text-red-600 focus:ring-red-600 focus:ring-offset-zinc-900 cursor-pointer"
              checked={value === option.value}
              onChange={() => !option.disabled && onChange(option.value)}
              disabled={option.disabled}
            />
          </div>
          <div className="flex flex-col">
            <span className={cn('text-sm font-medium', value === option.value ? 'text-white' : 'text-zinc-300')}>
              {option.label}
            </span>
            {option.description && (
              <span className="text-xs text-zinc-500 mt-1">{option.description}</span>
            )}
          </div>
        </label>
      ))}
    </div>
  );
};
