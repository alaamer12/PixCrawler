import { PricingPlan } from './types'

// PixCrawler Pricing Plans
export const PRICING_PLANS: PricingPlan[] = [
  {
    id: 'free',
    name: 'Free',
    description: 'Perfect for testing and small experiments',
    price: 0,
    currency: 'usd',
    interval: null,
    features: [
      '1 dataset',
      'Max 1,500 images',
      '7-day data retention',
      'Standard quality',
      'Community support'
    ],
    credits: 1500,
    maxDatasets: 1,
    maxImagesPerDataset: 1500,
    storage: {
      retentionDays: 7
    }
  },
  {
    id: 'hobby',
    name: 'Hobby',
    description: 'For serious hobbyists and creators',
    price: 70,
    currency: 'usd',
    interval: 'month',
    features: [
      '10 datasets',
      'Max 50,000 images per dataset',
      '30-day hot storage',
      'Cold storage afterwards',
      'Priority support',
      'API access'
    ],
    popular: true,
    lemonSqueezyVariantId: process.env.LEMONSQUEEZY_HOBBY_VARIANT_ID,
    credits: 500000,
    maxDatasets: 10,
    maxImagesPerDataset: 50000,
    storage: {
      hotStorageDays: 30
    }
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'For professionals and businesses',
    price: 180,
    currency: 'usd',
    interval: 'month',
    features: [
      '30 datasets',
      'Max 2,000,000 images per dataset',
      'Extended hot storage',
      'Dedicated support',
      'Commercial usage rights',
      'Early access to features'
    ],
    lemonSqueezyVariantId: process.env.LEMONSQUEEZY_PRO_VARIANT_ID,
    credits: 60000000,
    maxDatasets: 30,
    maxImagesPerDataset: 2000000,
    storage: {
      hotStorageDays: -1 // Indefinite
    }
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
    lemonSqueezyVariantId: process.env.LEMONSQUEEZY_PAYG_VARIANT_ID,
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
    lemonSqueezyVariantId: process.env.LEMONSQUEEZY_CREDITS_1000_VARIANT_ID,
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
    lemonSqueezyVariantId: process.env.LEMONSQUEEZY_CREDITS_5000_VARIANT_ID,
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
    lemonSqueezyVariantId: process.env.LEMONSQUEEZY_CREDITS_10000_VARIANT_ID,
    credits: 10000,
  }
]

// Helper functions
export const getPlanById = (planId: string): PricingPlan | undefined => {
  return [...PRICING_PLANS, ...CREDIT_PACKAGES].find(plan => plan.id === planId)
}

export const getPlanByLemonSqueezyVariant = (lemonSqueezyVariantId: string): PricingPlan | undefined => {
  return [...PRICING_PLANS, ...CREDIT_PACKAGES].find(plan => plan.lemonSqueezyVariantId === lemonSqueezyVariantId)
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
