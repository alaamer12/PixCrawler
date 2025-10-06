'use client'

import {memo, useMemo} from 'react'
import {Button} from '@/components/ui/button'
import {Check, Crown, Star, Zap} from 'lucide-react'

interface PricingPlan {
  name: string
  price: string
  period: string
  description: string
  features: string[]
  popular?: boolean
  enterprise?: boolean
  icon: React.ReactNode
  buttonText: string
  buttonVariant: 'outline' | 'default' | 'brand'
  includesPrevious?: boolean
}

const PRICING_PLANS: PricingPlan[] = [
  {
    name: 'Starter',
    price: 'Free',
    period: 'forever',
    description: 'Perfect for trying out PixCrawler and small projects',
    icon: <Star className="w-5 h-5"/>,
    features: [
      '1,000 images per month',
      '2 concurrent downloads',
      'Basic image validation',
      'JSON/CSV export',
      'Community support',
      '7-day data retention'
    ],
    buttonText: 'Get Started Free',
    buttonVariant: 'outline'
  },
  {
    name: 'Pro',
    price: '$29',
    period: 'per month',
    description: 'Ideal for professionals and growing teams',
    icon: <Zap className="w-5 h-5"/>,
    popular: true,
    includesPrevious: true,
    features: [
      '50,000 images per month',
      '10 concurrent downloads',
      'Advanced image validation',
      'All export formats (JSON, CSV, YAML, TXT)',
      'Priority support',
      '30-day data retention',
      'Custom keywords expansion',
      'Duplicate detection',
      'API access'
    ],
    buttonText: 'Start Free Trial',
    buttonVariant: 'default'
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'contact us',
    description: 'For large organizations with custom requirements',
    icon: <Crown className="w-5 h-5"/>,
    enterprise: true,
    includesPrevious: true,
    features: [
      'Unlimited images',
      'Unlimited concurrent downloads',
      'Premium image validation',
      'Custom export formats',
      'Dedicated support',
      'Unlimited data retention',
      'Advanced AI keyword expansion',
      'Custom integrations',
      'SLA guarantee',
      'On-premise deployment',
      'Custom branding'
    ],
    buttonText: 'Contact Sales',
    buttonVariant: 'brand'
  }
]

interface PricingCardProps {
  plan: PricingPlan
}

const PricingCard = memo(({plan}: PricingCardProps) => {
  const cardClassName = useMemo(() =>
    `relative rounded-2xl border h-full flex flex-col ${plan.popular
      ? 'border-primary shadow-lg scale-105 bg-card'
      : 'border-border bg-card hover:border-primary/50 transition-colors duration-200'
    }`, [plan.popular])

  const features = useMemo(() =>
    plan.features.map((feature, index) => (
      <li key={`${plan.name}-feature-${index}`} className="flex items-start gap-3">
        <Check className="w-4 h-4 text-success mt-0.5 flex-shrink-0"/>
        <span className="text-sm">{feature}</span>
      </li>
    )), [plan.features, plan.name])

  return (
    <div className={cardClassName}>
      {plan.popular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <div
            className="bg-gradient-to-r from-primary to-secondary text-primary-foreground px-4 py-1 rounded-full text-sm font-medium flex items-center gap-1">
            <Star className="w-3 h-3 fill-current"/>
            Most Popular
            <Star className="w-3 h-3 fill-current"/>
          </div>
        </div>
      )}

      <div className="p-8 flex-1 flex flex-col">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            {plan.icon}
            <h3 className="text-xl font-semibold">{plan.name}</h3>
          </div>

          <div className="mb-2">
            <span className="text-4xl font-bold">{plan.price}</span>
            {plan.price !== 'Free' && plan.price !== 'Custom' && (
              <span className="text-muted-foreground ml-1">/{plan.period}</span>
            )}
            {plan.price === 'Free' && (
              <span className="text-muted-foreground ml-1">{plan.period}</span>
            )}
          </div>

          <p className="text-muted-foreground text-sm">{plan.description}</p>
        </div>

        {plan.includesPrevious && (
          <div className="mb-6 p-3 bg-muted/30 rounded-lg border border-muted">
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Star className="w-4 h-4 fill-current text-primary"/>
              <span className="font-medium">Everything in previous plan, plus:</span>
              <Star className="w-4 h-4 fill-current text-primary"/>
            </div>
          </div>
        )}

        <ul className="space-y-3 flex-1 mb-8">
          {features}
        </ul>

        <div className="mt-auto">
          <Button
            variant={plan.buttonVariant}
            className="w-full"
            size="lg"
          >
            {plan.buttonText}
          </Button>
        </div>
      </div>
    </div>
  )
})

PricingCard.displayName = 'PricingCard'

export const PricingCards = memo(() => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {PRICING_PLANS.map((plan) => (
            <PricingCard key={plan.name} plan={plan}/>
          ))}
        </div>
      </div>
    </section>
  )
})

PricingCards.displayName = 'PricingCards'
