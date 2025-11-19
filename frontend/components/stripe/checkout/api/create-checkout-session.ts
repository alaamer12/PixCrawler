import {PaymentService} from '@/lib/payments/service'
import {createCheckoutSessionSchema} from '@/lib/payments/types'
import {getPlanById} from '@/lib/payments/plans'

export interface CreateCheckoutSessionRequest {
  planId: string
  userId: string
  successUrl?: string
  cancelUrl?: string
  metadata?: Record<string, string>
}

export interface CreateCheckoutSessionResponse {
  sessionId: string
  url: string | null
}

export class CheckoutSessionAPI {
  static async createSession(
    data: CreateCheckoutSessionRequest
  ): Promise<CreateCheckoutSessionResponse> {
    // Validate request data
    const validationResult = createCheckoutSessionSchema.safeParse(data)
    if (!validationResult.success) {
      throw new Error(`Invalid request data: ${validationResult.error.errors.map(e => e.message).join(', ')}`)
    }

    const {planId, userId, successUrl, cancelUrl, metadata} = validationResult.data

    // Get plan details
    const plan = getPlanById(planId)
    if (!plan) {
      throw new Error('Invalid plan ID')
    }

    if (!plan.stripePriceId) {
      throw new Error('Plan does not support online payments')
    }

    // Create checkout session
    const session = await PaymentService.createCheckoutSession({
      priceId: plan.stripePriceId,
      userId,
      planId,
      successUrl: successUrl || `${process.env.NEXT_PUBLIC_APP_URL}/payment/success?session_id={CHECKOUT_SESSION_ID}`,
      cancelUrl: cancelUrl || `${process.env.NEXT_PUBLIC_APP_URL}/payment/cancelled`,
      metadata: {
        planName: plan.name,
        ...metadata,
      },
    })

    return {
      sessionId: session.id,
      url: session.url,
    }
  }

  static async getSession(sessionId: string) {
    return await PaymentService.getCheckoutSession(sessionId)
  }
}
