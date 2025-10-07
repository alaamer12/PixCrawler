'use client'

import {memo} from 'react'
import {Button} from '@/components/ui/button'
import {HelpCircle, MessageCircle, Search} from 'lucide-react'

export const FAQHero = memo(() => {
  return (
    <section className="py-16 md:py-24 lg:py-32">
      <div className="container mx-auto px-4 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto">
          <div
            className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 text-primary rounded-full mb-6">
            <HelpCircle className="w-8 h-8"/>
          </div>

          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Frequently Asked{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Questions
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Find answers to common questions about PixCrawler, from getting started
            to advanced features and billing. Can't find what you're looking for?
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg">
              <MessageCircle className="w-4 h-4 mr-2"/>
              Contact Support
            </Button>
            <Button variant="outline" size="lg">
              <Search className="w-4 h-4 mr-2"/>
              Search Docs
            </Button>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto text-sm">
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 bg-success rounded-full"/>
              <span>24/7 Support Available</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 bg-primary rounded-full"/>
              <span>Comprehensive Documentation</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 bg-secondary rounded-full"/>
              <span>Community Forum</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})

FAQHero.displayName = 'FAQHero'
