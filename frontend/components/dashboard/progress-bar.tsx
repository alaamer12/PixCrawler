'use client'

import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface ProgressBarProps {
  value: number
  max?: number
  label?: string
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'success' | 'warning' | 'danger'
  className?: string
  animate?: boolean
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showPercentage = true,
  size = 'md',
  variant = 'default',
  className,
  animate = false
}: ProgressBarProps) {
  const percentage = Math.round((value / max) * 100)
  
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  const variantClasses = {
    default: '[&>div]:bg-primary',
    success: '[&>div]:bg-green-500',
    warning: '[&>div]:bg-yellow-500',
    danger: '[&>div]:bg-destructive'
  }

  return (
    <div className={cn('space-y-1', className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center text-sm">
          {label && <span className="text-muted-foreground">{label}</span>}
          {showPercentage && (
            <span className="font-medium">{percentage}%</span>
          )}
        </div>
      )}
      <Progress 
        value={percentage} 
        className={cn(
          sizeClasses[size],
          variantClasses[variant],
          animate && '[&>div]:animate-pulse',
          'bg-muted/50'
        )}
      />
    </div>
  )
}

interface JobProgressProps {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  progress: number
  totalItems?: number
  processedItems?: number
  className?: string
}

export function JobProgress({
  status,
  progress,
  totalItems,
  processedItems,
  className
}: JobProgressProps) {
  const getVariant = () => {
    switch (status) {
      case 'completed': return 'success'
      case 'failed': return 'danger'
      case 'paused': return 'warning'
      default: return 'default'
    }
  }

  const getLabel = () => {
    if (totalItems && processedItems !== undefined) {
      return `${processedItems} / ${totalItems} items`
    }
    switch (status) {
      case 'pending': return 'Waiting to start...'
      case 'running': return 'Processing...'
      case 'completed': return 'Completed'
      case 'failed': return 'Failed'
      case 'paused': return 'Paused'
      default: return ''
    }
  }

  return (
    <ProgressBar
      value={progress}
      label={getLabel()}
      variant={getVariant()}
      animate={status === 'running'}
      className={className}
    />
  )
}
