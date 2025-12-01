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
        { error: 'Order ID is required' },
        { status: 400 }
      )
    }

    // Get order details from Lemon Squeezy
    const order = await CheckoutSessionAPI.getOrder(sessionId)

    return NextResponse.json(order)

  } catch (error) {
    console.error('Error retrieving order:', error)

    return NextResponse.json(
      { error: 'Failed to retrieve order' },
      { status: 500 }
    )
  }
}
