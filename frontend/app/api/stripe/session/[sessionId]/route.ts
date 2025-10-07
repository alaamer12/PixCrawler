import { NextRequest, NextResponse } from 'next/server'
import { CheckoutSessionAPI } from '@/components/stripe/checkout/api/create-checkout-session'

export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params

    if (!sessionId) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      )
    }

    // Get session details
    const session = await CheckoutSessionAPI.getSession(sessionId)

    return NextResponse.json(session)

  } catch (error) {
    console.error('Error retrieving session:', error)
    
    return NextResponse.json(
      { error: 'Failed to retrieve session' },
      { status: 500 }
    )
  }
}