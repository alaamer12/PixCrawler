import { z } from 'zod'

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
  lemonSqueezyVariantId?: string
  credits?: number
  maxDatasets?: number
  maxImagesPerDataset?: number
  storage?: {
    retentionDays?: number // Days before deletion/archival (e.g. for Free tier)
    hotStorageDays?: number // Days in hot storage before moving to cold (e.g. for Hobby tier)
  }
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
  lemonSqueezyCustomerId: string
  lemonSqueezySubscriptionId: string
  lemonSqueezyVariantId: string
  planId: string
  status: 'active' | 'cancelled' | 'expired' | 'on_trial' | 'paused' | 'past_due' | 'unpaid'
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
  lemonSqueezyOrderId: string
  amount: number
  currency: string
  status: 'paid' | 'pending' | 'failed' | 'refunded'
  planId: string
  metadata?: Record<string, string>
  createdAt: Date
  updatedAt: Date
}

// Webhook Event Types
export interface LemonSqueezyWebhookEvent {
  meta: {
    event_name: string
    custom_data?: Record<string, any>
  }
  data: any
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

export class LemonSqueezyError extends PaymentError {
  constructor(message: string, code?: string) {
    super(message, code, 400)
    this.name = 'LemonSqueezyError'
  }
}
