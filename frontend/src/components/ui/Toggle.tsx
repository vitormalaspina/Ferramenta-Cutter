import React from 'react';
import { cn } from './Button';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  description?: string;
}

export const Toggle: React.FC<ToggleProps> = ({ checked, onChange, label, disabled, description }) => {
  return (
    <div className="flex items-center justify-between">
      <div className="flex flex-col">
        {label && <span className="text-sm font-medium text-zinc-200">{label}</span>}
        {description && <span className="text-xs text-zinc-500">{description}</span>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-zinc-900',
          checked ? 'bg-red-600' : 'bg-zinc-700',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
            checked ? 'translate-x-5' : 'translate-x-0'
          )}
        />
      </button>
    </div>
  );
};
