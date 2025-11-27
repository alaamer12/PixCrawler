import {NextRequest, NextResponse} from 'next/server'
import {createClient} from '@/lib/supabase/server'
import {db} from '@/lib/db'
import {notifications} from '@/lib/db/schema'
import {desc, eq} from 'drizzle-orm'

/**
 * GET /api/notifications
 * Fetch all notifications for the authenticated user
 */
export async function GET(request: NextRequest) {
  try {
    // Check for dev bypass
    const searchParams = request.nextUrl.searchParams
    const devBypass = searchParams.get('dev_bypass') === 'true'

    // Mock data for development
    if (devBypass || process.env.NODE_ENV === 'development') {
      const unreadOnly = searchParams.get('unread') === 'true'

      const mockNotifications = [
        {
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
          metadata: null,
          createdAt: new Date(Date.now() - 1000 * 60 * 30), // 30 min ago
        },
        {
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
          createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
        },
        {
          id: 3,
          userId: 'dev-user',
          title: 'Dataset exported',
          message: 'Your dataset "Dog Breeds" has been exported to COCO format_',
          type: 'info',
          category: 'dataset',
          icon: 'download',
          color: 'blue',
          actionUrl: '/dashboard/datasets/456',
          actionLabel: 'Download',
          isRead: true,
          readAt: new Date(Date.now() - 1000 * 60 * 60 * 5),
          metadata: null,
          createdAt: new Date(Date.now() - 1000 * 60 * 60 * 6), // 6 hours ago
        },
        {
          id: 4,
          userId: 'dev-user',
          title: 'New feature available',
          message: 'Check out our new AI-powered image tagging feature',
          type: 'info',
          category: 'product',
          icon: 'package',
          color: 'blue',
          actionUrl: '/dashboard',
          actionLabel: 'Learn More',
          isRead: true,
          readAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
          metadata: null,
          createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2), // 2 days ago
        },
        {
          id: 5,
          userId: 'dev-user',
          title: 'Security alert',
          message: 'New login detected from Chrome on Windows',
          type: 'warning',
          category: 'security',
          icon: 'shield',
          color: 'yellow',
          actionUrl: '/dashboard/settings',
          actionLabel: 'Review Activity',
          isRead: true,
          readAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3),
          metadata: {ip: '192.168.1.1', location: 'San Francisco, CA'},
          createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3), // 3 days ago
        },
      ]

      const filtered = unreadOnly
        ? mockNotifications.filter(n => !n.isRead)
        : mockNotifications

      return NextResponse.json({
        notifications: filtered,
        count: filtered.length,
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

    // Get query parameters
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
      query = db.select().from(notifications).where(eq(notifications.isRead, false))
    }

    const userNotifications = await query

    return NextResponse.json({
      notifications: userNotifications,
      count: userNotifications.length,
    })
  } catch (error) {
    console.error('Error fetching notifications:', error)
    return NextResponse.json(
      {error: 'Internal server error'},
      {status: 500}
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
    const {data: {user}, error: authError} = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        {error: 'Unauthorized'},
        {status: 401}
      )
    }

    const body = await request.json()
    const {type, title, message, icon, iconColor, actionUrl, metadata} = body

    // Validate required fields
    if (!type || !title || !message) {
      return NextResponse.json(
        {error: 'Missing required fields: type, title, message'},
        {status: 400}
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

    return NextResponse.json({notification}, {status: 201})
  } catch (error) {
    console.error('Error creating notification:', error)
    return NextResponse.json(
      {error: 'Internal server error'},
      {status: 500}
    )
  }
}
