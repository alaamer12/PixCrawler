'use client'

import React, { useCallback, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Bell,
  CheckCheck,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  CreditCard,
  Download,
  Filter,
  Package,
  Shield,
  Trash2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Notification } from '@/lib/db/schema'
import {
  useNotifications,
  useMarkAsRead,
  useMarkAllAsRead,
  useDeleteNotification
} from '@/lib/hooks/useNotifications'

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

const ITEMS_PER_PAGE = 10

export default function NotificationsPage() {
  const router = useRouter()
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  const {
    notifications,
    paginatedNotifications,
    loading,
    refetch,
    pagination: { currentPage, totalPages, setPage }
  } = useNotifications({
    filter: filter === 'unread' ? { unread: true } : undefined,
    pageSize: ITEMS_PER_PAGE
  })

  const { markAsRead } = useMarkAsRead()
  const { markAllAsRead } = useMarkAllAsRead()
  const { deleteNotification } = useDeleteNotification()

  const handleMarkAllAsRead = useCallback(async () => {
    const success = await markAllAsRead()
    if (success) {
      refetch()
    }
  }, [markAllAsRead, refetch])

  const handleDelete = useCallback(async (id: number) => {
    const success = await deleteNotification(id)
    if (success) {
      refetch()
    }
  }, [deleteNotification, refetch])

  const handleNotificationClick = useCallback(async (notification: Notification) => {
    if (!notification.isRead) {
      await markAsRead(notification.id)
      refetch()
    }
    router.push(`/notifications/${notification.id}`)
  }, [markAsRead, refetch, router])

  const getTimeAgo = useCallback((date: Date | string) => {
    const now = new Date()
    const notificationDate = new Date(date)
    const diffInMs = now.getTime() - notificationDate.getTime()
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60))
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60))
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

    if (diffInMinutes < 60) {
      return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''} ago`
    } else if (diffInHours < 24) {
      return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`
    } else {
      return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`
    }
  }, [])

  // Memoized calculations
  const unreadCount = useMemo(() =>
    notifications.filter(n => !n.isRead).length,
    [notifications]
  )

  const handlePageChange = useCallback((page: number) => {
    setPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [setPage])

  return (
    <div className="container max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Notifications</h1>
          <p className="text-muted-foreground">
            Stay updated with your latest activity
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFilter(filter === 'all' ? 'unread' : 'all')}
          >
            <Filter className="h-4 w-4 mr-2" />
            {filter === 'all' ? 'Show Unread' : 'Show All'}
          </Button>
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={handleMarkAllAsRead}>
              <CheckCheck className="h-4 w-4 mr-2" />
              Mark All Read
            </Button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{notifications.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Unread</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">{unreadCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Read</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-muted-foreground">
              {notifications.length - unreadCount}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notifications List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Notifications</CardTitle>
          <CardDescription>
            Click on a notification to view details
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex items-start gap-4">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium">No notifications</p>
              <p className="text-sm text-muted-foreground">
                {filter === 'unread'
                  ? "You're all caught up!"
                  : "You'll see notifications here when you have them"}
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {paginatedNotifications.map(notification => {
                  const Icon = notification.icon
                    ? iconMap[notification.icon] || Bell
                    : Bell
                  const colorClass = notification.color
                    ? colorMap[notification.color] || colorMap.blue
                    : colorMap.blue

                  return (
                    <div
                      key={notification.id}
                      className={cn(
                        'flex items-start gap-4 p-4 rounded-lg border cursor-pointer hover:bg-accent/20',
                        !notification.isRead && 'bg-primary/5 border-primary/20'
                      )}
                      onClick={() => handleNotificationClick(notification)}
                    >
                      <div className={cn('p-2 rounded-lg', colorClass)}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <p className="font-medium text-sm">
                              {notification.title}
                            </p>
                            <p className="text-sm text-muted-foreground mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {getTimeAgo(notification.createdAt)}
                            </p>
                          </div>
                          {!notification.isRead && (
                            <Badge variant="default" className="ml-2">
                              New
                            </Badge>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={e => {
                          e.stopPropagation()
                          handleDelete(notification.id)
                        }}
                        className="hover:bg-destructive/10 hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  )
                })}
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Showing {((currentPage - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(currentPage * ITEMS_PER_PAGE, notifications.length)} of {notifications.length} notifications
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" />
                      Previous
                    </Button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                        <Button
                          key={page}
                          variant={currentPage === page ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => handlePageChange(page)}
                          className="w-9"
                        >
                          {page}
                        </Button>
                      ))}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
