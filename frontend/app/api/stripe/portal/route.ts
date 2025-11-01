import {NextRequest, NextResponse} from 'next/server'
import {createServerClient} from '@supabase/ssr'
import {cookies} from 'next/headers'
import {PaymentService} from '@/lib/payments/service'

export async function POST(request: NextRequest) {
  try {
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!,
      {
        cookies: {
          get(name: string) {
            return cookies().get(name)?.value
          },
        },
      }
    )

    // Get the current user
    const {data: {user}, error: authError} = await supabase.auth.getUser()

    if (authError || !user) {
      return NextResponse.json(
        {error: 'Unauthorized'},
        {status: 401}
      )
    }

    const {returnUrl} = await request.json()

    // Get user's Stripe customer ID
    const {data: profile} = await supabase
      .from('user_profiles')
      .select('stripe_customer_id')
      .eq('user_id', user.id)
      .single()

    if (!profile?.stripe_customer_id) {
      return NextResponse.json(
        {error: 'No billing information found'},
        {status: 404}
      )
    }

    // Create billing portal session
    const session = await PaymentService.createBillingPortalSession(
      profile.stripe_customer_id,
      returnUrl || `${process.env.NEXT_PUBLIC_APP_URL}/dashboard/billing`
    )

    return NextResponse.json({
      url: session.url,
    })

  } catch (error) {
    console.error('Error creating billing portal session:', error)

    return NextResponse.json(
      {error: 'Failed to create billing portal session'},
      {status: 500}
    )
  }
}
