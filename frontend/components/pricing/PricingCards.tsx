'use client'

import { memo, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Check, Crown, Star, Zap, Loader2, Rocket } from 'lucide-react'
import { useAuth } from '@/lib/auth/hooks'
import { useRouter } from 'next/navigation'
import { PRICING_PLANS as PLANS_DATA } from '@/lib/payments/plans'
import type { PricingPlan as PlanType } from '@/lib/payments/types'

interface PricingPlan extends Omit<PlanType, 'price' | 'interval'> {
  displayPrice: string
  displayPeriod: string
  icon: React.ReactNode
  buttonText: string
  buttonVariant: 'outline' | 'default' | 'brand'
  includesPrevious?: boolean
  enterprise?: boolean
}

// Map imported plans to UI format
const PRICING_PLANS: PricingPlan[] = PLANS_DATA.filter(p => p.interval !== null || p.id === 'free').map((plan) => {
  const isEnterprise = plan.id === 'enterprise'
  const isPro = plan.id === 'pro'
  const isHobby = plan.id === 'hobby'
  const isFree = plan.id === 'free'

  return {
    ...plan,
    displayPrice: isFree ? 'Free' : isEnterprise ? 'Custom' : `$${plan.price}`,
    displayPeriod: isFree ? 'forever' : isEnterprise ? 'contact us' : plan.interval || 'month',
    icon: isFree ? <Star className="w-5 h-5" /> :
      isHobby ? <Rocket className="w-5 h-5" /> :
        isPro ? <Zap className="w-5 h-5" /> :
          <Crown className="w-5 h-5" />,
    buttonText: isFree ? 'Get Started Free' :
      isEnterprise ? 'Contact Sales' :
        'Start Free Trial',
    buttonVariant: isFree ? 'outline' as const :
      isEnterprise ? 'brand' as const :
        'default' as const,
    includesPrevious: !isFree,
    enterprise: isEnterprise
  }
})

interface PricingCardProps {
  plan: PricingPlan
  currentPlan?: string
  onSelectPlan: (planId: string) => Promise<void>
  isLoading?: boolean
}

const PricingCard = memo(({ plan, currentPlan, onSelectPlan, isLoading = false }: PricingCardProps) => {
  const [isProcessing, setIsProcessing] = useState(false)
  const isCurrentPlan = currentPlan === plan.id

  const handleSelectPlan = async () => {
    if (isCurrentPlan || isProcessing || isLoading) return

    setIsProcessing(true)
    try {
      await onSelectPlan(plan.id)
    } catch (error) {
      console.error('Error selecting plan:', error)
    } finally {
      setIsProcessing(false)
    }
  }
  const cardClassName = useMemo(() =>
    `relative rounded-2xl border h-full flex flex-col ${plan.popular
      ? 'border-primary shadow-lg scale-105 bg-card'
      : 'border-border bg-card hover:border-primary/50 transition-colors duration-200'
    }`, [plan.popular])

  const features = useMemo(() =>
    plan.features.map((feature, index) => (
      <li key={`${plan.name}-feature-${index}`} className="flex items-start gap-3">
        <Check className="w-4 h-4 text-success mt-0.5 flex-shrink-0" />
        <span className="text-sm">{feature}</span>
      </li>
    )), [plan.features, plan.name])

  return (
    <div className={cardClassName}>
      {plan.popular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <div
            className="bg-gradient-to-r from-primary to-secondary text-primary-foreground px-4 py-1 rounded-full text-sm font-medium flex items-center gap-1">
            <Star className="w-3 h-3 fill-current" />
            Most Popular
            <Star className="w-3 h-3 fill-current" />
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
            <span className="text-4xl font-bold">{plan.displayPrice}</span>
            {plan.displayPrice !== 'Free' && plan.displayPrice !== 'Custom' && (
              <span className="text-muted-foreground ml-1">/{plan.displayPeriod}</span>
            )}
            {plan.displayPrice === 'Free' && (
              <span className="text-muted-foreground ml-1">{plan.displayPeriod}</span>
            )}
          </div>

          <p className="text-muted-foreground text-sm">{plan.description}</p>
        </div>

        {plan.includesPrevious && (
          <div className="mb-6 p-3 bg-muted/30 rounded-lg border border-muted">
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Star className="w-4 h-4 fill-current text-primary" />
              <span className="font-medium">Everything in previous plan, plus:</span>
              <Star className="w-4 h-4 fill-current text-primary" />
            </div>
          </div>
        )}

        <ul className="space-y-3 flex-1 mb-8">
          {features}
        </ul>

        <div className="mt-auto">
          <Button
            variant={isCurrentPlan ? 'outline' : plan.buttonVariant}
            className="w-full"
            size="lg"
            onClick={handleSelectPlan}
            disabled={isCurrentPlan || isProcessing || isLoading}
          >
            {(isProcessing || isLoading) && (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            )}
            {isCurrentPlan ? 'Current Plan' : plan.buttonText}
          </Button>
        </div>
      </div>
    </div>
  )
})

PricingCard.displayName = 'PricingCard'

interface PricingCardsProps {
  currentPlan?: string
}

export const PricingCards = memo(({ currentPlan }: PricingCardsProps) => {
  const [isLoading, setIsLoading] = useState(false)
  const { user } = useAuth()
  const router = useRouter()

  const handleSelectPlan = async (planId: string) => {
    if (!user) {
      router.push('/auth/login?redirect=/pricing')
      return
    }

    // Handle free plan
    if (planId === 'free') {
      router.push('/dashboard')
      return
    }

    // Handle enterprise plan
    if (planId === 'enterprise') {
      // You can implement a contact form or redirect to sales
      window.open('mailto:sales@pixcrawler.com?subject=Enterprise Plan Inquiry', '_blank')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          planId,
          userId: user.id,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create checkout session')
      }

      const { url } = await response.json()

      if (url) {
        window.location.href = url
      }
    } catch (error) {
      console.error('Error creating checkout session:', error)
      // You might want to show a toast notification here
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {PRICING_PLANS.map((plan) => (
            <PricingCard
              key={plan.name}
              plan={plan}
              currentPlan={currentPlan}
              onSelectPlan={handleSelectPlan}
              isLoading={isLoading}
            />
          ))}
        </div>
      </div>
    </section>
  )
})

PricingCards.displayName = 'PricingCards'
