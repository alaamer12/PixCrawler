'use client'

import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'
import { ReactNode } from 'react'

interface StatsCardProps {
  title: string
  value: string | number
  description?: string
  icon: LucideIcon
  trend?: {
    value: number
    label: string
  }
  className?: string
  iconColor?: string
}

export function StatsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
  iconColor = 'text-muted-foreground'
}: StatsCardProps) {
  return (
    <Card className={cn('relative overflow-hidden bg-card/80 backdrop-blur-md border-border/50 hover:shadow-2xl transform transition-all duration-300 hover:scale-[1.02] group', className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <div className="flex items-baseline gap-2">
              <h2 className="text-3xl font-bold tracking-tight">{value}</h2>
              {trend && (
                <span className={cn(
                  'text-xs font-medium',
                  trend.value > 0 ? 'text-green-500' : trend.value < 0 ? 'text-red-500' : 'text-muted-foreground'
                )}>
                  {trend.value > 0 ? '+' : ''}{trend.value}% {trend.label}
                </span>
              )}
            </div>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div className={cn('p-3 rounded-lg bg-muted/50', iconColor)}>
            <Icon className="h-6 w-6 transition-transform duration-300 group-hover:scale-110" />
          </div>
        </div>
      </CardContent>
      <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-primary to-primary/50 transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-700" />
      <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
    </Card>
  )
}

interface QuickStatsCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  description?: string
  className?: string
  accent?: 'primary' | 'blue' | 'green' | 'red' | 'yellow'
  style?: React.CSSProperties
}

export function QuickStatsCard({
  title,
  value,
  icon: Icon,
  description,
  className,
  accent = 'primary',
  style
}: QuickStatsCardProps) {
  const accents: Record<string, { text: string; capsule: string; dot: string; bar: string; overlay: string }> = {
    primary: {
      text: 'group-hover:text-primary',
      capsule: 'bg-primary/10 group-hover:bg-primary/20',
      dot: 'bg-primary',
      bar: 'from-primary to-primary/50',
      overlay: 'bg-primary/5'
    },
    blue: {
      text: 'group-hover:text-blue-600',
      capsule: 'bg-blue-500/10 group-hover:bg-blue-500/20',
      dot: 'bg-blue-500',
      bar: 'from-blue-500 to-blue-400',
      overlay: 'bg-blue-500/5'
    },
    green: {
      text: 'group-hover:text-green-600',
      capsule: 'bg-green-500/10 group-hover:bg-green-500/20',
      dot: 'bg-green-500',
      bar: 'from-green-500 to-green-400',
      overlay: 'bg-green-500/5'
    },
    red: {
      text: 'group-hover:text-red-600',
      capsule: 'bg-red-500/10 group-hover:bg-red-500/20',
      dot: 'bg-red-500',
      bar: 'from-red-500 to-red-400',
      overlay: 'bg-red-500/5'
    },
    yellow: {
      text: 'group-hover:text-yellow-600',
      capsule: 'bg-yellow-500/10 group-hover:bg-yellow-500/20',
      dot: 'bg-yellow-500',
      bar: 'from-yellow-500 to-yellow-400',
      overlay: 'bg-yellow-500/5'
    }
  }
  const ac = accents[accent]
  return (
    <div
      className={cn(
        'relative overflow-hidden group rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground p-4 shadow-sm transform transition-all duration-500 hover:scale-105 hover:shadow-2xl',
        className
      )}
      style={style}
    >
      <div className="flex flex-row items-center justify-between space-y-0 pb-2">
        <h3 className={cn('tracking-tight text-sm font-medium transition-colors duration-300', ac.text)}>
          {title}
        </h3>
        <span className={cn('relative rounded-full p-2 transition-all duration-500', ac.capsule)}>
          <Icon className="size-4 text-muted-foreground transition-transform duration-700 group-hover:scale-125" />
          <span className={cn('absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-bounce', ac.dot)} style={{animationDelay: '0.1s'}} />
          <span className={cn('absolute -top-2 right-1 w-1 h-1 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-bounce', ac.dot)} style={{animationDelay: '0.2s'}} />
          <span className={cn('absolute top-0 -right-2 w-0.5 h-0.5 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-500 group-hover:animate-bounce', ac.dot)} style={{animationDelay: '0.3s'}} />
        </span>
      </div>
      <div className="relative overflow-hidden">
        <span className={cn('inline-block text-2xl font-bold leading-tight tracking-tight transition-transform duration-700 origin-left group-hover:scale-105', ac.text)}>
          {value}
        </span>
      </div>
      {description && (
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      )}
      <div className={cn('absolute bottom-0 left-0 h-1 bg-gradient-to-r transform origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-1000', ac.bar)} />
      <div className={cn('absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-lg', ac.overlay)} />
    </div>
  )
}
