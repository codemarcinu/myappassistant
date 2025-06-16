'use client';
import { cn } from '@/lib/utils';
import React from 'react';

interface FABProps {
  onClick: () => void;
  icon: React.ComponentType<{ className?: string }>;
  label?: string;
  variant?: 'regular' | 'small' | 'large' | 'extended';
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
}

export function FloatingActionButton({
  onClick,
  icon: Icon,
  label,
  variant = 'regular',
  position = 'bottom-right'
}: FABProps) {
  const positionClasses = {
    'bottom-right': 'bottom-8 right-8',
    'bottom-left': 'bottom-8 left-8',
    'top-right': 'top-8 right-8',
    'top-left': 'top-8 left-8',
  };

  const sizeClasses = {
    small: 'h-10 w-10',
    regular: 'h-14 w-14',
    large: 'h-16 w-16',
    extended: 'h-14 px-6',
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'fixed z-50 flex items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform duration-300 ease-in-out hover:scale-105',
        positionClasses[position],
        sizeClasses[variant],
        variant === 'extended' ? 'rounded-full' : 'rounded-full'
      )}
    >
      <Icon className={cn('h-6 w-6', variant === 'extended' && label && 'mr-2')} />
      {variant === 'extended' && label && (
        <span className="font-medium">{label}</span>
      )}
    </button>
  );
}
