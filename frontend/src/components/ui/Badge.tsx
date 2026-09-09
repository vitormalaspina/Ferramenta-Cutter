import React from 'react';
import { cn } from './Button';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
          {
            'bg-zinc-800 text-zinc-300': variant === 'default',
            'bg-green-500/10 text-green-400': variant === 'success',
            'bg-yellow-500/10 text-yellow-400': variant === 'warning',
            'bg-red-500/10 text-red-400': variant === 'error',
            'bg-blue-500/10 text-blue-400': variant === 'info',
          },
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);
Badge.displayName = 'Badge';
