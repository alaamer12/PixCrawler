'use client'

import {memo} from 'react'
import {Check} from 'lucide-react'

export const PricingHero = memo(() => {
  return (
    <section className="py-16 md:py-24 lg:py-32">
      <div className="container mx-auto px-4 lg:px-8 text-center">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Simple, transparent{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              pricing
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Choose the perfect plan for your image dataset needs. Start free and scale as you grow.
          </p>

          <div className="flex flex-wrap justify-center gap-4 mb-12">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Check className="w-4 h-4 text-success"/>
              No setup fees
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Check className="w-4 h-4 text-success"/>
              Cancel anytime
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Check className="w-4 h-4 text-success"/>
              14-day free trial
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})

PricingHero.displayName = 'PricingHero'
