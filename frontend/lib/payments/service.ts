import crypto from 'crypto'
import {
  createCheckout,
  getOrder,
  listCustomers,
  createCustomer,
  listSubscriptions,
  cancelSubscription,
  updateSubscription,
  getCustomer,
  type Checkout,
  type Order,
  type Customer,
  type Subscription,
} from '@lemonsqueezy/lemonsqueezy.js'
import { LEMONSQUEEZY_CONFIG } from './lemonsqueezy'
import { CheckoutSessionData, PaymentError, LemonSqueezyError } from './types'
import { getPlanById } from './plans'

export class PaymentService {
  /**
   * Create a checkout URL for Lemon Squeezy
   */
  static async createCheckoutSession(data: CheckoutSessionData): Promise<Checkout> {
    try {
      const plan = getPlanById(data.planId)
      if (!plan) {
        throw new PaymentError('Invalid plan ID', 'INVALID_PLAN')
      }

      if (!plan.lemonSqueezyVariantId) {
        throw new PaymentError('Plan does not have a Lemon Squeezy variant ID', 'MISSING_VARIANT_ID')
      }

      const checkout = await createCheckout(
        LEMONSQUEEZY_CONFIG.storeId,
        plan.lemonSqueezyVariantId,
        {
          checkoutOptions: {
            embed: false,
            media: true,
            logo: true,
            desc: true,
            discount: true,
            dark: false,
            subscriptionPreview: true,
          },
          checkoutData: {
            email: data.metadata?.userEmail,
            custom: {
              userId: data.userId,
              planId: data.planId,
              ...data.metadata,
            },
          },
          productOptions: {
            redirectUrl: data.successUrl,
            receiptButtonText: 'Go to Dashboard',
            receiptThankYouNote: 'Thank you for your purchase!',
          },
          expiresAt: null,
          preview: false,
          testMode: LEMONSQUEEZY_CONFIG.testMode,
        }
      )

      if (!checkout.data) {
        throw new PaymentError('Failed to create checkout session: No data returned')
      }

      return checkout.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Retrieve an order by ID
   */
  static async getOrder(orderId: string): Promise<Order> {
    try {
      const order = await getOrder(orderId, {
        include: ['order-items', 'subscriptions', 'license-keys'],
      })

      if (!order.data) {
        throw new PaymentError('Order not found', 'ORDER_NOT_FOUND')
      }

      return order.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Create or retrieve a Lemon Squeezy customer
   */
  static async createOrGetCustomer(userId: string, email?: string, name?: string): Promise<Customer> {
    try {
      // First, try to find existing customer by email
      if (email) {
        const { data: existingCustomers } = await listCustomers({
          filter: {
            storeId: LEMONSQUEEZY_CONFIG.storeId,
            email,
          },
        })

        // listCustomers returns { data: ListCustomers }
        // ListCustomers has a data property which is Customer[]
        const customers = (existingCustomers as any).data as Customer[]

        if (customers && customers.length > 0) {
          return customers[0]
        }
      }

      // Create new customer
      const customer = await createCustomer(LEMONSQUEEZY_CONFIG.storeId, {
        name: name || '',
        email: email || '',
      })

      if (!customer.data) {
        throw new PaymentError('Failed to create customer', 'CUSTOMER_CREATION_FAILED')
      }

      return customer.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Get customer's active subscriptions
   */
  static async getCustomerSubscriptions(customerId: string): Promise<Subscription[]> {
    try {
      // We need to get the customer's email to filter subscriptions, 
      // as listSubscriptions doesn't support filtering by customerId directly.
      const customer = await getCustomer(customerId)
      if (!customer.data) {
        throw new PaymentError('Customer not found', 'CUSTOMER_NOT_FOUND')
      }

      const email = (customer.data as any).attributes.email

      const { data: subscriptions } = await listSubscriptions({
        filter: {
          storeId: LEMONSQUEEZY_CONFIG.storeId,
          userEmail: email,
          status: 'active',
        },
      })

      // subscriptions is ListSubscriptions, which has data: Subscription[]
      return (subscriptions as any)?.data || []
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Cancel a subscription (cancels at period end by default)
   */
  static async cancelSubscription(subscriptionId: string): Promise<Subscription> {
    try {
      const subscription = await cancelSubscription(subscriptionId)

      if (!subscription.data) {
        throw new PaymentError('Failed to cancel subscription', 'CANCEL_FAILED')
      }

      return subscription.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Reactivate a subscription
   */
  static async reactivateSubscription(subscriptionId: string): Promise<Subscription> {
    try {
      const subscription = await updateSubscription(subscriptionId, {
        cancelled: false,
      })

      if (!subscription.data) {
        throw new PaymentError('Failed to reactivate subscription', 'REACTIVATE_FAILED')
      }

      return subscription.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Get customer portal URL
   * Lemon Squeezy has a universal customer portal
   */
  static getCustomerPortalUrl(subscriptionId?: string): string {
    // If we have a subscription ID, we could fetch the subscription
    // and return the customer-specific portal URL from subscription.data.attributes.urls.customer_portal
    // For now, return the universal portal
    return 'https://app.lemonsqueezy.com/my-orders'
  }

  /**
   * Verify webhook signature
   */
  static verifyWebhookSignature(payload: string, signature: string): any {
    try {
      const webhookSecret = process.env.LEMONSQUEEZY_WEBHOOK_SECRET!

      // Create HMAC with SHA-256
      const hmac = crypto.createHmac('sha256', webhookSecret)
      const digest = hmac.update(payload).digest('hex')

      if (digest !== signature) {
        throw new PaymentError('Invalid webhook signature', 'INVALID_SIGNATURE')
      }

      return JSON.parse(payload)
    } catch (error) {
      if (error instanceof PaymentError) {
        throw error
      }
      throw new PaymentError('Invalid webhook signature', 'INVALID_SIGNATURE')
    }
  }

  /**
   * Update subscription plan
   */
  static async updateSubscriptionPlan(
    subscriptionId: string,
    newVariantId: string
  ): Promise<Subscription> {
    try {
      const subscription = await updateSubscription(subscriptionId, {
        variantId: parseInt(newVariantId),
      })

      if (!subscription.data) {
        throw new PaymentError('Failed to update subscription', 'UPDATE_FAILED')
      }

      return subscription.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Pause a subscription
   */
  static async pauseSubscription(subscriptionId: string, resumeAt?: Date): Promise<Subscription> {
    try {
      const subscription = await updateSubscription(subscriptionId, {
        pause: {
          mode: resumeAt ? 'void' : 'free',
          resumesAt: resumeAt?.toISOString(),
        },
      })

      if (!subscription.data) {
        throw new PaymentError('Failed to pause subscription', 'PAUSE_FAILED')
      }

      return subscription.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }

  /**
   * Resume a paused subscription
   */
  static async resumeSubscription(subscriptionId: string): Promise<Subscription> {
    try {
      const subscription = await updateSubscription(subscriptionId, {
        pause: null,
      })

      if (!subscription.data) {
        throw new PaymentError('Failed to resume subscription', 'RESUME_FAILED')
      }

      return subscription.data
    } catch (error) {
      if (error instanceof Error && !(error instanceof PaymentError)) {
        throw new LemonSqueezyError(error.message)
      }
      throw error
    }
  }
}
