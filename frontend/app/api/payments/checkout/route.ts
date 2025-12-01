import { NextRequest, NextResponse } from 'next/server'
import { PaymentService } from '@/lib/payments/service'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

/**
 * Create Lemon Squeezy Checkout Session
 * POST /api/payments/checkout
 */
export async function POST(request: NextRequest) {
  try {
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

    const body = await request.json()
    const { planId, userId } = body

    if (!planId || !userId) {
      return NextResponse.json(
        { error: 'Missing required fields: planId, userId' },
        { status: 400 }
      )
    }

    // Verify user matches authenticated user
    if (user.id !== userId) {
      return NextResponse.json(
        { error: 'User ID mismatch' },
        { status: 403 }
      )
    }

    // Get user profile for email
    const { data: profile } = await supabase
      .from('profiles')
      .select('email, full_name')
      .eq('id', userId)
      .single()

    // Create checkout session
    const checkout = await PaymentService.createCheckoutSession({
      priceId: '', // Not used for Lemon Squeezy
      planId,
      userId,
      successUrl: `${process.env.NEXT_PUBLIC_APP_URL}/payment/success?order_id={order_id}`,
      cancelUrl: `${process.env.NEXT_PUBLIC_APP_URL}/payment/cancelled`,
      metadata: {
        userEmail: profile?.email || user.email || '',
        userName: profile?.full_name || '',
      },
    })

    // Lemon Squeezy checkout response structure
    const checkoutData = checkout as any
    
    return NextResponse.json({
      url: checkoutData.attributes?.url || checkoutData.url,
      checkoutId: checkoutData.id,
    })

  } catch (error) {
    console.error('Error creating checkout session:', error)
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    )
  }
}
