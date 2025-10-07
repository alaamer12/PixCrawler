'use client'

import {memo} from 'react'
import Link from 'next/link'
import {Button} from '@/components/ui/button'
import {Book, Mail, MessageCircle, Users} from 'lucide-react'

export const FAQSupport = memo(() => {
  return (
    <section className="py-16 bg-gradient-to-r from-primary/10 via-accent/10 to-secondary/10">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Still need help?
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Can&apos;t find the answer you&apos;re looking for? Our support team is here to help you succeed.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
              <div
                className="inline-flex items-center justify-center w-12 h-12 bg-primary/10 text-primary rounded-lg mb-4">
                <MessageCircle className="w-6 h-6"/>
              </div>
              <h3 className="font-semibold mb-2">Live Chat</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Get instant help from our support team
              </p>
              <Button size="sm" className="w-full">
                Start Chat
              </Button>
            </div>

            <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
              <div
                className="inline-flex items-center justify-center w-12 h-12 bg-secondary/10 text-secondary rounded-lg mb-4">
                <Mail className="w-6 h-6"/>
              </div>
              <h3 className="font-semibold mb-2">Email Support</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Send us a detailed message
              </p>
              <Button size="sm" variant="outline" className="w-full">
                Send Email
              </Button>
            </div>

            <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
              <div
                className="inline-flex items-center justify-center w-12 h-12 bg-warning/10 text-warning rounded-lg mb-4">
                <Book className="w-6 h-6"/>
              </div>
              <h3 className="font-semibold mb-2">Documentation</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Comprehensive guides and tutorials
              </p>
              <Button asChild size="sm" variant="outline" className="w-full">
                <Link href="/docs">
                  View Docs
                </Link>
              </Button>
            </div>

            <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
              <div
                className="inline-flex items-center justify-center w-12 h-12 bg-destructive/10 text-destructive rounded-lg mb-4">
                <Users className="w-6 h-6"/>
              </div>
              <h3 className="font-semibold mb-2">Community</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Connect with other developers
              </p>
              <Button size="sm" variant="outline" className="w-full">
                Join Forum
              </Button>
            </div>
          </div>

          <div className="text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Response times: Live chat (instant) • Email (&lt; 4 hours) • Enterprise (&lt; 1 hour)
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center text-sm">
              <a
                href="mailto:support@pixcrawler.com"
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Mail className="w-4 h-4"/>
                support@pixcrawler.com
              </a>
              <span className="hidden sm:block text-muted-foreground">•</span>
              <span className="text-muted-foreground">
                Available 24/7 for Enterprise customers
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})

FAQSupport.displayName = 'FAQSupport'
