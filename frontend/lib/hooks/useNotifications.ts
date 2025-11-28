/**
 * Notifications Hooks
 * 
 * Custom React hooks for notification-related data operations.
 * Provides hooks for fetching, marking as read, and deleting notifications.
 */

import { useState, useEffect, useCallback } from 'react'
import { apiService, type NotificationFilter } from '@/lib/services'
import type { Notification } from '@/lib/db/schema'
import { useToast } from '@/components/ui/use-toast'

interface UseNotificationsResult {
  notifications: Notification[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

interface UseNotificationResult {
  notification: Notification | null
  loading: boolean
  error: Error | null
  notFound: boolean
  refetch: () => Promise<void>
}

interface UseMarkAsReadResult {
  markAsRead: (id: number) => Promise<boolean>
  loading: boolean
  error: Error | null
}

interface UseMarkAllAsReadResult {
  markAllAsRead: () => Promise<boolean>
  loading: boolean
  error: Error | null
}

interface UseDeleteNotificationResult {
  deleteNotification: (id: number) => Promise<boolean>
  loading: boolean
  error: Error | null
}

/**
 * Hook to fetch notifications with optional filtering
 */
export function useNotifications(filter?: NotificationFilter): UseNotificationsResult {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchNotifications = useCallback(async () => {
    setLoading(true)
    setError(null)

    const response = await apiService.getNotifications(filter)

    if (response.error) {
      setError(response.error)
      setNotifications([])
    } else {
      setNotifications(response.data || [])
    }

    setLoading(false)
  }, [filter])

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  return {
    notifications,
    loading,
    error,
    refetch: fetchNotifications,
  }
}

/**
 * Hook to fetch a single notification by ID
 */
export function useNotification(id: number): UseNotificationResult {
  const [notification, setNotification] = useState<Notification | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [notFound, setNotFound] = useState(false)

  const fetchNotification = useCallback(async () => {
    if (!id) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    setNotFound(false)

    const response = await apiService.getNotification(id)

    if (response.error) {
      setError(response.error)
      setNotification(null)

      // Check if it's a 404 error
      if ('statusCode' in response.error && (response.error as any).statusCode === 404) {
        setNotFound(true)
      }
    } else {
      setNotification(response.data)
    }

    setLoading(false)
  }, [id])

  useEffect(() => {
    fetchNotification()
  }, [fetchNotification])

  return {
    notification,
    loading,
    error,
    notFound,
    refetch: fetchNotification,
  }
}

/**
 * Hook to mark a notification as read
 */
export function useMarkAsRead(): UseMarkAsReadResult {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const markAsRead = useCallback(async (id: number): Promise<boolean> => {
    setLoading(true)
    setError(null)

    const response = await apiService.markNotificationAsRead(id)

    if (response.error) {
      setError(response.error)
      console.error('Error marking notification as read:', response.error)
      setLoading(false)
      return false
    }

    setLoading(false)
    return true
  }, [])

  return {
    markAsRead,
    loading,
    error,
  }
}

/**
 * Hook to mark all notifications as read
 */
export function useMarkAllAsRead(): UseMarkAllAsReadResult {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const { toast } = useToast()

  const markAllAsRead = useCallback(async (): Promise<boolean> => {
    setLoading(true)
    setError(null)

    const response = await apiService.markAllNotificationsAsRead()

    if (response.error) {
      setError(response.error)
      toast({
        title: 'Error',
        description: 'Failed to mark all notifications as read',
        variant: 'destructive',
      })
      setLoading(false)
      return false
    }

    toast({
      title: 'Success',
      description: 'All notifications marked as read',
    })

    setLoading(false)
    return true
  }, [toast])

  return {
    markAllAsRead,
    loading,
    error,
  }
}

/**
 * Hook to delete a notification
 */
export function useDeleteNotification(): UseDeleteNotificationResult {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const { toast } = useToast()

  const deleteNotification = useCallback(async (id: number): Promise<boolean> => {
    setLoading(true)
    setError(null)

    const response = await apiService.deleteNotification(id)

    if (response.error) {
      setError(response.error)
      toast({
        title: 'Error',
        description: 'Failed to delete notification',
        variant: 'destructive',
      })
      setLoading(false)
      return false
    }

    toast({
      title: 'Success',
      description: 'Notification deleted',
    })

    setLoading(false)
    return true
  }, [toast])

  return {
    deleteNotification,
    loading,
    error,
  }
}
