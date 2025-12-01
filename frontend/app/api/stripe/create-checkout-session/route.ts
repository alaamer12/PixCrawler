import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { CheckoutSessionAPI } from '@/components/stripe/checkout/api/create-checkout-session'

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!,
      {
        cookies: {
          get(name: string) {
            return cookieStore.get(name)?.value
          },
        },
      }
    )

    // Get the current user
    const { data: { user }, error: authError } = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const { planId, successUrl, cancelUrl, metadata } = body

    // Create checkout session using the API class
    const result = await CheckoutSessionAPI.createSession({
      planId,
      userId: user.id,
      successUrl,
      cancelUrl,
      metadata: {
        userEmail: user.email || '',
        ...metadata,
      },
    })

    return NextResponse.json({
      checkoutId: result.checkoutId,
      url: result.url,
    })

  } catch (error) {
    console.error('Error creating checkout session:', error)

    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to create checkout session' },
      { status: 500 }
    )
  }
}
