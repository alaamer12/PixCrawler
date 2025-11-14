import {z} from 'zod'

// Pricing Plans
export interface PricingPlan {
  id: string
  name: string
  description: string
  price: number
  currency: string
  interval?: 'month' | 'year' | null
  features: string[]
  popular?: boolean
  stripePriceId?: string
  credits?: number
  maxDatasets?: number
  maxImagesPerDataset?: number
}

// Payment Intent Types
export interface PaymentIntentData {
  amount: number
  currency: string
  planId: string
  userId: string
  metadata?: Record<string, string>
}

// Checkout Session Types
export interface CheckoutSessionData {
  priceId: string
  userId: string
  planId: string
  successUrl?: string
  cancelUrl?: string
  metadata?: Record<string, string>
}

// Subscription Types
export interface SubscriptionData {
  userId: string
  stripeCustomerId: string
  stripeSubscriptionId: string
  stripePriceId: string
  planId: string
  status: 'active' | 'canceled' | 'incomplete' | 'incomplete_expired' | 'past_due' | 'trialing' | 'unpaid'
  currentPeriodStart: Date
  currentPeriodEnd: Date
  cancelAtPeriodEnd: boolean
  createdAt: Date
  updatedAt: Date
}

// Transaction Types
export interface TransactionData {
  id: string
  userId: string
  stripePaymentIntentId: string
  amount: number
  currency: string
  status: 'succeeded' | 'pending' | 'failed' | 'canceled'
  planId: string
  metadata?: Record<string, string>
  createdAt: Date
  updatedAt: Date
}

// Webhook Event Types
export interface StripeWebhookEvent {
  id: string
  type: string
  data: {
    object: any
  }
  created: number
}

// Validation Schemas
export const createPaymentIntentSchema = z.object({
  planId: z.string().min(1, 'Plan ID is required'),
  userId: z.string().min(1, 'User ID is required'),
  metadata: z.record(z.string()).optional(),
})

export const createCheckoutSessionSchema = z.object({
  priceId: z.string().min(1, 'Price ID is required'),
  planId: z.string().min(1, 'Plan ID is required'),
  userId: z.string().min(1, 'User ID is required'),
  successUrl: z.string().url().optional(),
  cancelUrl: z.string().url().optional(),
  metadata: z.record(z.string()).optional(),
})

export const webhookEventSchema = z.object({
  type: z.string(),
  data: z.object({
    object: z.any(),
  }),
})

// Error Types
export class PaymentError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number
  ) {
    super(message)
    this.name = 'PaymentError'
  }
}

export class StripeError extends PaymentError {
  constructor(message: string, code?: string) {
    super(message, code, 400)
    this.name = 'StripeError'
  }
}
