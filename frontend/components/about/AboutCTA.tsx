'use client'

import { memo } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight, Mail, MessageCircle } from 'lucide-react'

export const AboutCTA = memo(() => {
  return (
    <section className="py-16 bg-gradient-to-r from-primary/10 via-accent/10 to-secondary/10">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Join us in shaping the{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              future of AI
            </span>
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Whether you're a developer, researcher, or just curious about AI, we'd love to hear from you. 
            Let's build something amazing together.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <Button asChild size="lg" className="min-w-[200px]">
              <Link href="/signup">
                Start Building Today
                <ArrowRight className="w-4 h-4 ml-2" />
              </Link>
            </Button>
            
            <Button asChild variant="outline" size="lg" className="min-w-[200px]">
              <Link href="/contact">
                <MessageCircle className="w-4 h-4 mr-2" />
                Get in Touch
              </Link>
            </Button>
          </div>

          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Have questions? We're here to help.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center text-sm">
              <a 
                href="mailto:hello@pixcrawler.com" 
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Mail className="w-4 h-4" />
                hello@pixcrawler.com
              </a>
              <span className="hidden sm:block text-muted-foreground">•</span>
              <Link 
                href="/docs" 
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Documentation
              </Link>
              <span className="hidden sm:block text-muted-foreground">•</span>
              <Link 
                href="/examples" 
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Examples
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})

AboutCTA.displayName = 'AboutCTA'