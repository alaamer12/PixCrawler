import { PricingPlan } from './types'

// PixCrawler Pricing Plans
export const PRICING_PLANS: PricingPlan[] = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'Perfect for individuals and small projects',
    price: 0,
    currency: 'usd',
    interval: null,
    features: [
      '1,000 images per month',
      '3 datasets',
      'Basic image sources',
      'Standard quality',
      'Email support',
      'Basic analytics'
    ],
    credits: 1000,
    maxDatasets: 3,
    maxImagesPerDataset: 500,
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'Ideal for growing businesses and researchers',
    price: 29,
    currency: 'usd',
    interval: 'month',
    features: [
      '10,000 images per month',
      'Unlimited datasets',
      'All image sources',
      'High quality images',
      'Priority support',
      'Advanced analytics',
      'API access',
      'Custom labeling'
    ],
    popular: true,
    stripePriceId: process.env.STRIPE_PRO_PRICE_ID,
    credits: 10000,
    maxDatasets: -1, // Unlimited
    maxImagesPerDataset: 2000,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For large organizations with custom needs',
    price: 99,
    currency: 'usd',
    interval: 'month',
    features: [
      '50,000 images per month',
      'Unlimited datasets',
      'All premium sources',
      'Ultra-high quality',
      'Dedicated support',
      'Custom integrations',
      'Advanced API',
      'White-label options',
      'SLA guarantee',
      'Custom training'
    ],
    stripePriceId: process.env.STRIPE_ENTERPRISE_PRICE_ID,
    credits: 50000,
    maxDatasets: -1, // Unlimited
    maxImagesPerDataset: 10000,
  },
  {
    id: 'pay-as-you-go',
    name: 'Pay as You Go',
    description: 'Flexible pricing for variable usage',
    price: 0.01, // $0.01 per image
    currency: 'usd',
    interval: null,
    features: [
      '$0.01 per image',
      'No monthly commitment',
      'All image sources',
      'High quality images',
      'Standard support',
      'Basic analytics',
      'API access'
    ],
    stripePriceId: process.env.STRIPE_PAYG_PRICE_ID,
    credits: 0, // Credits purchased as needed
    maxDatasets: -1,
    maxImagesPerDataset: 5000,
  }
]

// One-time credit packages
export const CREDIT_PACKAGES: PricingPlan[] = [
  {
    id: 'credits-1000',
    name: '1,000 Credits',
    description: 'Perfect for small projects',
    price: 9,
    currency: 'usd',
    features: [
      '1,000 image credits',
      'Never expires',
      'All image sources',
      'High quality images'
    ],
    stripePriceId: process.env.STRIPE_CREDITS_1000_PRICE_ID,
    credits: 1000,
  },
  {
    id: 'credits-5000',
    name: '5,000 Credits',
    description: 'Great value for medium projects',
    price: 39,
    currency: 'usd',
    features: [
      '5,000 image credits',
      'Never expires',
      'All image sources',
      'High quality images',
      '20% savings'
    ],
    popular: true,
    stripePriceId: process.env.STRIPE_CREDITS_5000_PRICE_ID,
    credits: 5000,
  },
  {
    id: 'credits-10000',
    name: '10,000 Credits',
    description: 'Best value for large projects',
    price: 69,
    currency: 'usd',
    features: [
      '10,000 image credits',
      'Never expires',
      'All image sources',
      'High quality images',
      '30% savings'
    ],
    stripePriceId: process.env.STRIPE_CREDITS_10000_PRICE_ID,
    credits: 10000,
  }
]

// Helper functions
export const getPlanById = (planId: string): PricingPlan | undefined => {
  return [...PRICING_PLANS, ...CREDIT_PACKAGES].find(plan => plan.id === planId)
}

export const getPlanByStripePrice = (stripePriceId: string): PricingPlan | undefined => {
  return [...PRICING_PLANS, ...CREDIT_PACKAGES].find(plan => plan.stripePriceId === stripePriceId)
}

export const isSubscriptionPlan = (planId: string): boolean => {
  const plan = getPlanById(planId)
  return plan?.interval !== null && plan?.interval !== undefined
}

export const isCreditPackage = (planId: string): boolean => {
  return CREDIT_PACKAGES.some(pkg => pkg.id === planId)
}

export const formatPrice = (price: number, currency: string = 'usd'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
  }).format(price)
}