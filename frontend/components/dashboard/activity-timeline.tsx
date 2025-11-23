'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { 
  Activity,
  FolderPlus,
  Database,
  Play,
  CheckCircle,
  XCircle,
  Download,
  Upload,
  Settings,
  User
} from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export interface ActivityItem {
  id: string
  type: 'project_created' | 'dataset_created' | 'job_started' | 'job_completed' | 'job_failed' | 'dataset_downloaded' | 'settings_updated'
  title: string
  description?: string
  timestamp: Date
  user?: string
  metadata?: Record<string, any>
}

interface ActivityTimelineProps {
  activities: ActivityItem[]
  className?: string
  maxItems?: number
}

const activityIcons = {
  project_created: FolderPlus,
  dataset_created: Database,
  job_started: Play,
  job_completed: CheckCircle,
  job_failed: XCircle,
  dataset_downloaded: Download,
  settings_updated: Settings
}

const activityColors = {
  project_created: 'text-blue-500',
  dataset_created: 'text-purple-500',
  job_started: 'text-yellow-500',
  job_completed: 'text-green-500',
  job_failed: 'text-red-500',
  dataset_downloaded: 'text-cyan-500',
  settings_updated: 'text-gray-500'
}

export function ActivityTimeline({ 
  activities, 
  className,
  maxItems = 10 
}: ActivityTimelineProps) {
  const displayActivities = activities.slice(0, maxItems)

  if (activities.length === 0) {
    return (
      <Card className={cn('bg-card/80 backdrop-blur-md', className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Activity className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">No recent activity</p>
            <p className="text-sm text-muted-foreground/70 mt-1">
              Your project activities will appear here
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('bg-card/80 backdrop-blur-md', className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {displayActivities.map((activity, index) => {
            const Icon = activityIcons[activity.type] || Activity
            const color = activityColors[activity.type] || 'text-muted-foreground'
            
            return (
              <div
                key={activity.id}
                className={cn(
                  'flex items-start gap-3 pb-4',
                  index < displayActivities.length - 1 && 'border-b border-border/50'
                )}
              >
                <div className={cn('flex-none grid h-8 w-8 place-items-center rounded-lg bg-muted/50', color)}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {activity.title}
                      </p>
                      {activity.description && (
                        <p className="text-xs text-muted-foreground">
                          {activity.description}
                        </p>
                      )}
                    </div>
                    <time className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDistanceToNow(activity.timestamp, { addSuffix: true })}
                    </time>
                  </div>
                  {activity.user && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <User className="h-3 w-3" />
                      {activity.user}
                    </div>
                  )}
                  {activity.metadata && (
                    <div className="flex gap-2 mt-2">
                      {Object.entries(activity.metadata).map(([key, value]) => (
                        <Badge key={key} variant="outline" className="text-xs">
                          {key}: {value}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        {activities.length > maxItems && (
          <div className="pt-4 border-t border-border/50">
            <p className="text-xs text-muted-foreground text-center">
              Showing {maxItems} of {activities.length} activities
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
