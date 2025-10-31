import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { db } from '@/lib/db'
import { notifications } from '@/lib/db/schema'
import { eq, desc } from 'drizzle-orm'

/**
 * GET /api/notifications
 * Fetch all notifications for the authenticated user
 */
export async function GET(request: NextRequest) {
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

    // Get query parameters
    const searchParams = request.nextUrl.searchParams
    const limit = parseInt(searchParams.get('limit') || '50')
    const unreadOnly = searchParams.get('unread') === 'true'

    // Build query
    let query = db
      .select()
      .from(notifications)
      .where(eq(notifications.userId, user.id))
      .orderBy(desc(notifications.createdAt))
      .limit(limit)

    // Filter for unread only if requested
    if (unreadOnly) {
      query = query.where(eq(notifications.isRead, false)) as any
    }

    const userNotifications = await query

    return NextResponse.json({
      notifications: userNotifications,
      count: userNotifications.length,
    })
  } catch (error) {
    console.error('Error fetching notifications:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

/**
 * POST /api/notifications
 * Create a new notification (admin/system only)
 */
export async function POST(request: NextRequest) {
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

    const body = await request.json()
    const { type, title, message, icon, iconColor, actionUrl, metadata } = body

    // Validate required fields
    if (!type || !title || !message) {
      return NextResponse.json(
        { error: 'Missing required fields: type, title, message' },
        { status: 400 }
      )
    }

    // Create notification
    const [notification] = await db
      .insert(notifications)
      .values({
        userId: user.id,
        type,
        title,
        message,
        icon,
        iconColor,
        actionUrl,
        metadata,
      })
      .returning()

    return NextResponse.json({ notification }, { status: 201 })
  } catch (error) {
    console.error('Error creating notification:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
