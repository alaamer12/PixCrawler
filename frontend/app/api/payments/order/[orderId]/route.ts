import { NextRequest, NextResponse } from 'next/server'
import { PaymentService } from '@/lib/payments/service'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

/**
 * Get Lemon Squeezy Order Details
 * GET /api/payments/order/[orderId]
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orderId: string }> }
) {
  try {
    const { orderId } = await params
    const cookieStore = await cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          get(name: string) {
            return cookieStore.get(name)?.value
          },
        },
      }
    )

    // Get authenticated user
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    // Get order details from Lemon Squeezy
    const order = await PaymentService.getOrder(orderId)

    // Verify the order belongs to the authenticated user
    const orderData = order as any
    const customData = orderData.attributes?.first_order_item?.product?.custom_data || {}
    if (customData.userId && customData.userId !== user.id) {
      return NextResponse.json(
        { error: 'Forbidden' },
        { status: 403 }
      )
    }

    return NextResponse.json(orderData)

  } catch (error) {
    console.error('Error fetching order:', error)
    return NextResponse.json(
      { error: 'Failed to fetch order details' },
      { status: 500 }
    )
  }
}
