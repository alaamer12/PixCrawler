'use client'

import {memo} from 'react'
import Link from 'next/link'
import {Button} from '@/components/ui/button'
import {ArrowRight, MessageCircle} from 'lucide-react'

export const PricingCTA = memo(() => {
  return (
    <section className="py-16 bg-gradient-to-r from-primary/10 via-accent/10 to-secondary/10">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to start building your{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              image datasets?
            </span>
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join thousands of developers, researchers, and companies who trust PixCrawler
            for their machine learning and computer vision projects.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button asChild size="lg" className="min-w-[200px]">
              <Link href="/signup">
                Start Free Trial
                <ArrowRight className="w-4 h-4 ml-2"/>
              </Link>
            </Button>

            <Button asChild variant="outline" size="lg" className="min-w-[200px]">
              <Link href="/contact">
                <MessageCircle className="w-4 h-4 mr-2"/>
                Talk to Sales
              </Link>
            </Button>
          </div>

          <div className="mt-8 text-sm text-muted-foreground">
            <p>No credit card required • 14-day free trial • Cancel anytime</p>
          </div>
        </div>
      </div>
    </section>
  )
})

PricingCTA.displayName = 'PricingCTA'
