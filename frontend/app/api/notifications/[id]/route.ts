import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { db } from '@/lib/db'
import { notifications } from '@/lib/db/schema'
import { eq, and } from 'drizzle-orm'

/**
 * GET /api/notifications/[id]
 * Fetch a specific notification for the authenticated user
 * Security: Only returns notification if it belongs to the authenticated user
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Authenticate user
    const supabase = await createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const notificationId = parseInt(params.id)

    if (isNaN(notificationId)) {
      return NextResponse.json(
        { error: 'Invalid notification ID' },
        { status: 400 }
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
        { error: 'Notification not found' },
        { status: 404 }
      )
    }

    return NextResponse.json({ notification })
  } catch (error) {
    console.error('Error fetching notification:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
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
  { params }: { params: { id: string } }
) {
  try {
    // Authenticate user
    const supabase = await createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const notificationId = parseInt(params.id)

    if (isNaN(notificationId)) {
      return NextResponse.json(
        { error: 'Invalid notification ID' },
        { status: 400 }
      )
    }

    const body = await request.json()
    const { isRead } = body

    if (typeof isRead !== 'boolean') {
      return NextResponse.json(
        { error: 'Invalid isRead value' },
        { status: 400 }
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
        { error: 'Notification not found' },
        { status: 404 }
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

    return NextResponse.json({ notification: updatedNotification })
  } catch (error) {
    console.error('Error updating notification:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
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
  { params }: { params: { id: string } }
) {
  try {
    // Authenticate user
    const supabase = await createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const notificationId = parseInt(params.id)

    if (isNaN(notificationId)) {
      return NextResponse.json(
        { error: 'Invalid notification ID' },
        { status: 400 }
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
        { error: 'Notification not found' },
        { status: 404 }
      )
    }

    // Delete notification
    await db
      .delete(notifications)
      .where(eq(notifications.id, notificationId))

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting notification:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
