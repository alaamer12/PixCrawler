'use client'

import { memo } from 'react'
import { Mail, MessageCircle, Phone } from 'lucide-react'

export const ContactHero = memo(() => {
  return (
    <section className="py-16 md:py-24 lg:py-32">
      <div className="container mx-auto px-4 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Get in{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              touch
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Have questions about PixCrawler? Need help with your datasets? Want to discuss enterprise solutions? 
            We&apos;d love to hear from you.
          </p>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="flex items-center justify-center gap-3 bg-card border border-border rounded-lg px-4 py-3">
              <Mail className="w-5 h-5 text-primary" />
              <span className="text-sm font-medium">Email Support</span>
            </div>
            <div className="flex items-center justify-center gap-3 bg-card border border-border rounded-lg px-4 py-3">
              <MessageCircle className="w-5 h-5 text-secondary" />
              <span className="text-sm font-medium">Live Chat</span>
            </div>
            <div className="flex items-center justify-center gap-3 bg-card border border-border rounded-lg px-4 py-3">
              <Phone className="w-5 h-5 text-warning" />
              <span className="text-sm font-medium">Phone Support</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})

ContactHero.displayName = 'ContactHero'