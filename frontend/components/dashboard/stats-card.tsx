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
}

export function QuickStatsCard({
  title,
  value,
  icon: Icon,
  description,
  className
}: QuickStatsCardProps) {
  return (
    <div className={cn('rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground shadow-sm p-4 hover:shadow-md transition-shadow', className)}>
      <div className="flex flex-row items-center justify-between space-y-0 pb-2">
        <h3 className="tracking-tight text-sm font-medium">{title}</h3>
        <Icon className="size-4 text-muted-foreground" />
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {description && (
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      )}
    </div>
  )
}
