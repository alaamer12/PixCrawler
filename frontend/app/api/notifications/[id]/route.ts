import {NextRequest, NextResponse} from 'next/server'
import {createClient} from '@/lib/supabase/server'
import {db} from '@/lib/db'
import {notifications} from '@/lib/db/schema'
import {and, eq} from 'drizzle-orm'

/**
 * GET /api/notifications/[id]
 * Fetch a specific notification for the authenticated user
 * Security: Only returns notification if it belongs to the authenticated user
 */
export async function GET(
  request: NextRequest,
  {params}: { params: { id: string } }
) {
  try {
    const notificationId = parseInt(params.id)

    if (isNaN(notificationId)) {
      return NextResponse.json(
        {error: 'Invalid notification ID'},
        {status: 400}
      )
    }

    // Check for dev bypass
    const searchParams = request.nextUrl.searchParams
    const devBypass = searchParams.get('dev_bypass') === 'true'

    // Mock data for development
    if (devBypass || process.env.NODE_ENV === 'development') {
      const mockNotifications: Record<number, any> = {
        1: {
          id: 1,
          userId: 'dev-user',
          title: 'Crawl job completed',
          message: 'Your "Cat Breeds" dataset is ready with 1,234 images',
          type: 'success',
          category: 'crawl_job',
          icon: 'circle-check-big',
          color: 'green',
          actionUrl: '/dashboard/datasets/123',
          actionLabel: 'View Dataset',
          isRead: false,
          readAt: null,
          metadata: {jobId: '123', imageCount: 1234},
          createdAt: new Date(Date.now() - 1000 * 60 * 30),
        },
        2: {
          id: 2,
          userId: 'dev-user',
          title: 'Payment successful',
          message: 'Your payment of $49.99 has been processed successfully',
          type: 'success',
          category: 'payment',
          icon: 'credit-card',
          color: 'blue',
          actionUrl: '/dashboard/billing',
          actionLabel: 'View Invoice',
          isRead: false,
          readAt: null,
          metadata: {amount: 49.99, currency: 'USD'},
          createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2),
        },
      }

      const notification = mockNotifications[notificationId]

      if (!notification) {
        return NextResponse.json(
          {error: 'Notification not found'},
          {status: 404}
        )
      }

      return NextResponse.json({notification})
    }

    // Authenticate user
    const supabase = await createClient()
    const {data: {user}, error: authError} = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        {error: 'Unauthorized'},
        {status: 401}
      )
    }

    // Fetch notification with user authorization check
    const [notification] = await db
      .select()
      .from(notifications)
      .where(
        and(
          eq(notifications.id, notificationId),
          eq(notifications.userId, user.id) // Security: Only fetch user's own notifications
        )
      )
      .limit(1)

    if (!notification) {
      return NextResponse.json(
        {error: 'Notification not found'},
        {status: 404}
      )
    }

    return NextResponse.json({notification})
  } catch (error) {
    console.error('Error fetching notification:', error)
    return NextResponse.json(
      {error: 'Internal server error'},
      {status: 500}
    )
  }
}

/**
 * PATCH /api/notifications/[id]
 * Mark a notification as read/unread
 * Security: Only allows updating user's own notifications
 */
export async function PATCH(
  request: NextRequest,
  {params}: { params: { id: string } }
) {
  try {
    const notificationId = parseInt(params.id)

    if (isNaN(notificationId)) {
      return NextResponse.json(
        {error: 'Invalid notification ID'},
        {status: 400}
      )
    }

    const body = await request.json()
    const {isRead} = body

    if (typeof isRead !== 'boolean') {
      return NextResponse.json(
        {error: 'Invalid isRead value'},
        {status: 400}
      )
    }

    // Check for dev bypass
    const searchParams = request.nextUrl.searchParams
    const devBypass = searchParams.get('dev_bypass') === 'true'

    // Mock data for development
    if (devBypass || process.env.NODE_ENV === 'development') {
      return NextResponse.json({
        notification: {
          id: notificationId,
          isRead,
          readAt: isRead ? new Date() : null,
        },
      })
    }

    // Authenticate user
    const supabase = await createClient()
    const {data: {user}, error: authError} = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        {error: 'Unauthorized'},
        {status: 401}
      )
    }

    // Verify notification belongs to user before updating
    const [existingNotification] = await db
      .select()
      .from(notifications)
      .where(
        and(
          eq(notifications.id, notificationId),
          eq(notifications.userId, user.id)
        )
      )
      .limit(1)

    if (!existingNotification) {
      return NextResponse.json(
        {error: 'Notification not found'},
        {status: 404}
      )
    }

    // Update notification
    const [updatedNotification] = await db
      .update(notifications)
      .set({
        isRead,
        readAt: isRead ? new Date() : null,
      })
      .where(eq(notifications.id, notificationId))
      .returning()

    return NextResponse.json({notification: updatedNotification})
  } catch (error) {
    console.error('Error updating notification:', error)
    return NextResponse.json(
      {error: 'Internal server error'},
      {status: 500}
    )
  }
}

/**
 * DELETE /api/notifications/[id]
 * Delete a notification
 * Security: Only allows deleting user's own notifications
 */
export async function DELETE(
  request: NextRequest,
  {params}: { params: { id: string } }
) {
  try {
    const notificationId = parseInt(params.id)

    if (isNaN(notificationId)) {
      return NextResponse.json(
        {error: 'Invalid notification ID'},
        {status: 400}
      )
    }

    // Check for dev bypass
    const searchParams = request.nextUrl.searchParams
    const devBypass = searchParams.get('dev_bypass') === 'true'

    // Mock data for development
    if (devBypass || process.env.NODE_ENV === 'development') {
      return NextResponse.json({success: true})
    }

    // Authenticate user
    const supabase = await createClient()
    const {data: {user}, error: authError} = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        {error: 'Unauthorized'},
        {status: 401}
      )
    }

    // Verify notification belongs to user before deleting
    const [existingNotification] = await db
      .select()
      .from(notifications)
      .where(
        and(
          eq(notifications.id, notificationId),
          eq(notifications.userId, user.id)
        )
      )
      .limit(1)

    if (!existingNotification) {
      return NextResponse.json(
        {error: 'Notification not found'},
        {status: 404}
      )
    }

    // Delete notification
    await db
      .delete(notifications)
      .where(eq(notifications.id, notificationId))

    return NextResponse.json({success: true})
  } catch (error) {
    console.error('Error deleting notification:', error)
    return NextResponse.json(
      {error: 'Internal server error'},
      {status: 500}
    )
  }
}
