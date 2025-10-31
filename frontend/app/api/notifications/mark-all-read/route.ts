import {NextResponse} from 'next/server'
import {createClient} from '@/lib/supabase/server'
import {db} from '@/lib/db'
import {notifications} from '@/lib/db/schema'
import {eq} from 'drizzle-orm'

/**
 * POST /api/notifications/mark-all-read
 * Mark all notifications as read for the authenticated user
 */
export async function POST() {
  try {
    // Check for dev bypass
    if (process.env.NODE_ENV === 'development') {
      // In dev mode, just return success
      return NextResponse.json({
        message: 'All notifications marked as read',
        count: 5,
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

    // Update all unread notifications for this user
    const result = await db
      .update(notifications)
      .set({
        isRead: true,
        readAt: new Date(),
      })
      .where(eq(notifications.userId, user.id))
      .returning()

    return NextResponse.json({
      message: 'All notifications marked as read',
      count: result.length,
    })
  } catch (error) {
    console.error('Error marking all as read:', error)
    return NextResponse.json(
      {error: 'Internal server error'},
      {status: 500}
    )
  }
}
