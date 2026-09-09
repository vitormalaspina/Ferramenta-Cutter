import React from 'react';
import { cn } from './Button';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('rounded-xl border border-zinc-800 bg-zinc-900/50 p-6', className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';
