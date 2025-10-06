'use client'

import { memo } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight, Lightbulb, Code, Rocket } from 'lucide-react'

export const ExamplesCTA = memo(() => {
  return (
    <section className="py-16 bg-gradient-to-r from-primary/10 via-accent/10 to-secondary/10">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex justify-center mb-6">
            <div className="p-3 bg-primary/10 rounded-full">
              <Lightbulb className="w-8 h-8 text-primary" />
            </div>
          </div>
          
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to build your own{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              dataset?
            </span>
          </h2>
          
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Start with one of our examples or create something completely new. 
            PixCrawler makes it easy to build high-quality image datasets for any use case.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <Button asChild size="lg" className="min-w-[200px]">
              <Link href="/signup">
                <Rocket className="w-4 h-4 mr-2" />
                Start Building Now
              </Link>
            </Button>
            
            <Button asChild variant="outline" size="lg" className="min-w-[200px]">
              <Link href="/docs">
                <Code className="w-4 h-4 mr-2" />
                View Documentation
              </Link>
            </Button>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary mb-1">50+</div>
              <div className="text-sm text-muted-foreground">Ready-to-use examples</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-secondary mb-1">10M+</div>
              <div className="text-sm text-muted-foreground">Images processed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-warning mb-1">99.9%</div>
              <div className="text-sm text-muted-foreground">Uptime guarantee</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})

ExamplesCTA.displayName = 'ExamplesCTA'