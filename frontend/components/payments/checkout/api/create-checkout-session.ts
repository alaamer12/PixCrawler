import { PaymentService } from '@/lib/payments/service'
import { getPlanById } from '@/lib/payments/plans'

export interface CreateCheckoutSessionRequest {
  planId: string
  userId: string
  successUrl?: string
  cancelUrl?: string
  metadata?: Record<string, string>
}

export interface CreateCheckoutSessionResponse {
  checkoutId: string
  url: string
}

export class CheckoutSessionAPI {
  static async createSession(
    data: CreateCheckoutSessionRequest
  ): Promise<CreateCheckoutSessionResponse> {
    const { planId, userId, metadata } = data

    // Get plan details
    const plan = getPlanById(planId)
    if (!plan) {
      throw new Error('Invalid plan ID')
    }

    if (!plan.lemonSqueezyVariantId) {
      throw new Error('Plan does not support online payments')
    }

    // Create checkout with Lemon Squeezy
    const checkout = await PaymentService.createCheckoutSession({
      priceId: plan.lemonSqueezyVariantId,
      userId,
      planId,
      metadata: {
        planName: plan.name,
        ...metadata,
      },
    })

    return {
      checkoutId: checkout.data.id,
      url: checkout.data.attributes.url,
    }
  }

  static async getOrder(orderId: string) {
    return await PaymentService.getOrder(orderId)
  }
}
