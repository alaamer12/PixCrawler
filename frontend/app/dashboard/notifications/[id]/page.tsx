'use client'

import React, {useEffect, useState} from 'react'
import {useParams, useRouter} from 'next/navigation'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {Skeleton} from '@/components/ui/skeleton'
import {useToast} from '@/components/ui/use-toast'
import {
  ArrowLeft,
  Bell,
  CheckCircle,
  Clock,
  CreditCard,
  Download,
  ExternalLink,
  Package,
  Shield,
  Trash2,
} from 'lucide-react'
import {cn} from '@/lib/utils'
import type {Notification} from '@/lib/db/schema'

const iconMap: Record<string, React.ElementType> = {
  'circle-check-big': CheckCircle,
  'credit-card': CreditCard,
  download: Download,
  package: Package,
  shield: Shield,
}

const colorMap: Record<string, string> = {
  green: 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/20',
  blue: 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/20',
  red: 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/20',
  yellow: 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/20',
}

export default function NotificationDetailPage() {
  const router = useRouter()
  const params = useParams()
  const {toast} = useToast()
  const [notification, setNotification] = useState<Notification | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    fetchNotification()
  }, [params.id])

  const fetchNotification = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/notifications/${params.id}`)

      if (response.status === 404) {
        setNotFound(true)
        return
      }

      if (!response.ok) {
        throw new Error('Failed to fetch notification')
      }

      const data = await response.json()
      setNotification(data.notification)

      // Mark as read if not already
      if (!data.notification.isRead) {
        await markAsRead()
      }
    } catch (error) {
      console.error('Error fetching notification:', error)
      toast({
        title: 'Error',
        description: 'Failed to load notification',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = async () => {
    try {
      await fetch(`/api/notifications/${params.id}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({isRead: true}),
      })
    } catch (error) {
      console.error('Error marking as read:', error)
    }
  }

  const deleteNotification = async () => {
    try {
      const response = await fetch(`/api/notifications/${params.id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error('Failed to delete notification')
      }

      toast({
        title: 'Success',
        description: 'Notification deleted',
      })

      router.push('/notifications')
    } catch (error) {
      console.error('Error deleting notification:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete notification',
        variant: 'destructive',
      })
    }
  }

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      dateStyle: 'full',
      timeStyle: 'short',
    }).format(new Date(date))
  }

  if (loading) {
    return (
      <div className="container max-w-3xl mx-auto p-6 space-y-6">
        <Skeleton className="h-10 w-32"/>
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-3/4"/>
            <Skeleton className="h-4 w-1/2 mt-2"/>
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-20 w-full"/>
            <Skeleton className="h-10 w-full"/>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (notFound || !notification) {
    return (
      <div className="container max-w-3xl mx-auto p-6">
        <Card>
          <CardContent className="text-center py-12">
            <Bell className="h-16 w-16 mx-auto text-muted-foreground mb-4"/>
            <h2 className="text-2xl font-bold mb-2">Notification Not Found</h2>
            <p className="text-muted-foreground mb-6">
              This notification doesn't exist or you don't have permission to view it.
            </p>
            <Button onClick={() => router.push('/notifications')}>
              <ArrowLeft className="h-4 w-4 mr-2"/>
              Back to Notifications
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const Icon = notification.icon
    ? iconMap[notification.icon] || Bell
    : Bell
  const colorClass = notification.iconColor
    ? colorMap[notification.iconColor] || colorMap.blue
    : colorMap.blue

  return (
    <div className="container max-w-3xl mx-auto p-6 space-y-6">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={() => router.push('/notifications')}
        className="gap-2"
      >
        <ArrowLeft className="h-4 w-4"/>
        Back to Notifications
      </Button>

      {/* Notification Detail Card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4 flex-1">
              <div className={cn('p-3 rounded-lg', colorClass)}>
                <Icon className="h-6 w-6"/>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <CardTitle className="text-2xl">{notification.title}</CardTitle>
                  {!notification.isRead && (
                    <Badge variant="default">New</Badge>
                  )}
                </div>
                <CardDescription className="flex items-center gap-2">
                  <Clock className="h-4 w-4"/>
                  {formatDate(notification.createdAt)}
                </CardDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={deleteNotification}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-5 w-5"/>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Message */}
          <div>
            <h3 className="font-semibold mb-2">Message</h3>
            <p className="text-muted-foreground leading-relaxed">
              {String(notification.message)}
            </p>
          </div>

          {/* Metadata */}
          {notification.metadata && (
            <div>
              <h3 className="font-semibold mb-2">Additional Information</h3>
              <div className="bg-muted p-4 rounded-lg">
                <pre className="text-sm overflow-auto">
                  {JSON.stringify(notification.metadata, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Action Button */}
          {notification.actionUrl && (
            <div className="pt-4 border-t">
              <Button
                onClick={() => router.push(notification.actionUrl!)}
                className="w-full"
              >
                View Details
                <ExternalLink className="h-4 w-4 ml-2"/>
              </Button>
            </div>
          )}

          {/* Notification Info */}
          <div className="pt-4 border-t space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Type</span>
              <Badge variant="outline">{notification.type}</Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Status</span>
              <span className="font-medium">
                {notification.isRead ? 'Read' : 'Unread'}
              </span>
            </div>
            {notification.readAt && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Read At</span>
                <span className="font-medium">
                  {formatDate(notification.readAt)}
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
