import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { PaymentService } from '@/lib/payments/service'

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

    // Lemon Squeezy has a universal customer portal
    // No need to fetch customer ID or create a session
    const portalUrl = PaymentService.getCustomerPortalUrl()

    return NextResponse.json({
      url: portalUrl,
    })

  } catch (error) {
    console.error('Error getting customer portal URL:', error)

    return NextResponse.json(
      { error: 'Failed to get customer portal URL' },
      { status: 500 }
    )
  }
}
