'use client'

import { memo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Check, Loader2, Star, Zap } from 'lucide-react'
import { PricingPlan } from '@/lib/payments/types'
import { formatPrice } from '@/lib/payments/plans'

interface PricingCardProps {
  plan: PricingPlan
  onSelectPlan: (planId: string) => Promise<void>
  isLoading?: boolean
  currentPlan?: string
  className?: string
}

export const PricingCard = memo(({
  plan,
  onSelectPlan,
  isLoading = false,
  currentPlan,
  className = ''
}: PricingCardProps) => {
  const [isProcessing, setIsProcessing] = useState(false)
  const isCurrentPlan = currentPlan === plan.id
  const isFree = plan.price === 0

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

  const getButtonText = () => {
    if (isCurrentPlan) return 'Current Plan'
    if (isFree) return 'Get Started Free'
    if (plan.interval) return `Subscribe to ${plan.name}`
    return `Purchase ${plan.name}`
  }

  const getButtonVariant = () => {
    if (isCurrentPlan) return 'outline'
    if (plan.popular) return 'default'
    return 'outline'
  }

  return (
    <div className={`relative bg-card border border-border rounded-xl p-6 transition-all duration-300 hover:shadow-lg hover:border-primary/20 ${plan.popular ? 'ring-2 ring-primary ring-opacity-50 scale-105' : ''} ${className}`}>
      {/* Popular Badge */}
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="bg-primary text-primary-foreground px-3 py-1 flex items-center gap-1">
            <Star className="w-3 h-3 fill-current" />
            Most Popular
          </Badge>
        </div>
      )}

      {/* Header */}
      <div className="text-center mb-6">
        <div className="flex items-center justify-center gap-2 mb-2">
          <h3 className="text-xl font-bold">{plan.name}</h3>
          {plan.id === 'enterprise' && <Zap className="w-5 h-5 text-yellow-500" />}
        </div>
        <p className="text-muted-foreground text-sm mb-4 min-h-[2.5rem] flex items-center justify-center">
          {plan.description}
        </p>
        
        {/* Price */}
        <div className="mb-4">
          {isFree ? (
            <div className="text-3xl font-bold text-green-600">Free</div>
          ) : (
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-3xl font-bold">{formatPrice(plan.price, plan.currency)}</span>
              {plan.interval && (
                <span className="text-muted-foreground">/{plan.interval}</span>
              )}
              {plan.id === 'pay-as-you-go' && (
                <span className="text-sm text-muted-foreground">per image</span>
              )}
            </div>
          )}
        </div>

        {/* Credits Info */}
        {plan.credits !== undefined && plan.credits > 0 && (
          <div className="text-sm text-muted-foreground mb-4 bg-muted/30 rounded-lg py-2 px-3">
            <strong>{plan.credits.toLocaleString()}</strong> credits
            {plan.interval && ' per month'}
            {!plan.interval && ' (never expires)'}
          </div>
        )}
      </div>

      {/* Features */}
      <div className="space-y-3 mb-6 min-h-[200px]">
        {plan.features.map((feature, index) => (
          <div key={index} className="flex items-start gap-3">
            <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
            <span className="text-sm leading-relaxed">{feature}</span>
          </div>
        ))}
      </div>

      {/* Action Button */}
      <Button
        onClick={handleSelectPlan}
        disabled={isCurrentPlan || isProcessing || isLoading}
        variant={getButtonVariant()}
        className={`w-full transition-all duration-200 ${
          plan.popular && !isCurrentPlan 
            ? 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg' 
            : ''
        }`}
        size="lg"
      >
        {(isProcessing || isLoading) && (
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        )}
        {getButtonText()}
      </Button>

      {/* Current Plan Indicator */}
      {isCurrentPlan && (
        <div className="text-center mt-3">
          <Badge variant="secondary" className="text-xs">
            ✓ Active Plan
          </Badge>
        </div>
      )}

      {/* Value Indicator for Credit Packages */}
      {!plan.interval && plan.credits && plan.credits >= 5000 && (
        <div className="text-center mt-2">
          <Badge variant="outline" className="text-xs text-green-600 border-green-200">
            {plan.credits === 5000 ? '20% savings' : '30% savings'}
          </Badge>
        </div>
      )}
    </div>
  )
})

PricingCard.displayName = 'PricingCard'