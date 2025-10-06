import Stripe from 'stripe'
import { stripe, STRIPE_CONFIG } from './stripe'
import { 
  PaymentIntentData, 
  CheckoutSessionData, 
  PaymentError, 
  StripeError,
  TransactionData 
} from './types'
import { getPlanById, isSubscriptionPlan } from './plans'

export class PaymentService {
  /**
   * Create a payment intent for one-time payments
   */
  static async createPaymentIntent(data: PaymentIntentData): Promise<Stripe.PaymentIntent> {
    try {
      const plan = getPlanById(data.planId)
      if (!plan) {
        throw new PaymentError('Invalid plan ID', 'INVALID_PLAN')
      }

      const paymentIntent = await stripe.paymentIntents.create({
        amount: Math.round(data.amount * 100), // Convert to cents
        currency: data.currency,
        metadata: {
          userId: data.userId,
          planId: data.planId,
          ...data.metadata,
        },
        automatic_payment_methods: {
          enabled: true,
        },
      })

      return paymentIntent
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to create payment intent')
    }
  }

  /**
   * Create a checkout session for subscriptions or one-time payments
   */
  static async createCheckoutSession(data: CheckoutSessionData): Promise<Stripe.Checkout.Session> {
    try {
      const plan = getPlanById(data.planId)
      if (!plan) {
        throw new PaymentError('Invalid plan ID', 'INVALID_PLAN')
      }

      if (!plan.stripePriceId) {
        throw new PaymentError('Plan does not have a Stripe price ID', 'MISSING_PRICE_ID')
      }

      // Determine if this is a subscription or one-time payment
      const mode = isSubscriptionPlan(data.planId) ? 'subscription' : 'payment'

      const sessionConfig: Stripe.Checkout.SessionCreateParams = {
        mode,
        payment_method_types: STRIPE_CONFIG.payment_method_types,
        line_items: [
          {
            price: plan.stripePriceId,
            quantity: 1,
          },
        ],
        success_url: data.successUrl || STRIPE_CONFIG.success_url,
        cancel_url: data.cancelUrl || STRIPE_CONFIG.cancel_url,
        metadata: {
          userId: data.userId,
          planId: data.planId,
          ...data.metadata,
        },
        customer_email: undefined, // Will be set if user email is available
      }

      // For subscriptions, add additional configuration
      if (mode === 'subscription') {
        sessionConfig.subscription_data = {
          metadata: {
            userId: data.userId,
            planId: data.planId,
          },
        }
      }

      const session = await stripe.checkout.sessions.create(sessionConfig)
      return session
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to create checkout session')
    }
  }

  /**
   * Retrieve a checkout session
   */
  static async getCheckoutSession(sessionId: string): Promise<Stripe.Checkout.Session> {
    try {
      const session = await stripe.checkout.sessions.retrieve(sessionId, {
        expand: ['line_items', 'payment_intent', 'subscription'],
      })
      return session
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to retrieve checkout session')
    }
  }

  /**
   * Create or retrieve a Stripe customer
   */
  static async createOrGetCustomer(userId: string, email?: string, name?: string): Promise<Stripe.Customer> {
    try {
      // First, try to find existing customer by metadata
      const existingCustomers = await stripe.customers.list({
        limit: 1,
        metadata: { userId },
      })

      if (existingCustomers.data.length > 0) {
        return existingCustomers.data[0]
      }

      // Create new customer
      const customer = await stripe.customers.create({
        email,
        name,
        metadata: { userId },
      })

      return customer
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to create or retrieve customer')
    }
  }

  /**
   * Get customer's active subscriptions
   */
  static async getCustomerSubscriptions(customerId: string): Promise<Stripe.Subscription[]> {
    try {
      const subscriptions = await stripe.subscriptions.list({
        customer: customerId,
        status: 'active',
        expand: ['data.items.data.price'],
      })
      return subscriptions.data
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to retrieve customer subscriptions')
    }
  }

  /**
   * Cancel a subscription
   */
  static async cancelSubscription(subscriptionId: string, cancelAtPeriodEnd: boolean = true): Promise<Stripe.Subscription> {
    try {
      const subscription = await stripe.subscriptions.update(subscriptionId, {
        cancel_at_period_end: cancelAtPeriodEnd,
      })
      return subscription
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to cancel subscription')
    }
  }

  /**
   * Reactivate a subscription
   */
  static async reactivateSubscription(subscriptionId: string): Promise<Stripe.Subscription> {
    try {
      const subscription = await stripe.subscriptions.update(subscriptionId, {
        cancel_at_period_end: false,
      })
      return subscription
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to reactivate subscription')
    }
  }

  /**
   * Create a billing portal session
   */
  static async createBillingPortalSession(customerId: string, returnUrl: string): Promise<Stripe.BillingPortal.Session> {
    try {
      const session = await stripe.billingPortal.sessions.create({
        customer: customerId,
        return_url: returnUrl,
      })
      return session
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to create billing portal session')
    }
  }

  /**
   * Verify webhook signature
   */
  static verifyWebhookSignature(payload: string, signature: string): Stripe.Event {
    try {
      const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!
      return stripe.webhooks.constructEvent(payload, signature, webhookSecret)
    } catch (error) {
      throw new PaymentError('Invalid webhook signature', 'INVALID_SIGNATURE')
    }
  }

  /**
   * Get payment method details
   */
  static async getPaymentMethod(paymentMethodId: string): Promise<Stripe.PaymentMethod> {
    try {
      return await stripe.paymentMethods.retrieve(paymentMethodId)
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to retrieve payment method')
    }
  }

  /**
   * Refund a payment
   */
  static async refundPayment(paymentIntentId: string, amount?: number): Promise<Stripe.Refund> {
    try {
      const refundData: Stripe.RefundCreateParams = {
        payment_intent: paymentIntentId,
      }

      if (amount) {
        refundData.amount = Math.round(amount * 100) // Convert to cents
      }

      return await stripe.refunds.create(refundData)
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to process refund')
    }
  }

  /**
   * Get usage records for metered billing
   */
  static async createUsageRecord(subscriptionItemId: string, quantity: number, timestamp?: number): Promise<Stripe.UsageRecord> {
    try {
      return await stripe.subscriptionItems.createUsageRecord(subscriptionItemId, {
        quantity,
        timestamp: timestamp || Math.floor(Date.now() / 1000),
        action: 'increment',
      })
    } catch (error) {
      if (error instanceof Stripe.errors.StripeError) {
        throw new StripeError(error.message, error.code)
      }
      throw new PaymentError('Failed to create usage record')
    }
  }
}