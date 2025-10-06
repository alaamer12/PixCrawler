'use client'

import { memo } from 'react'
import { Button } from '@/components/ui/button'
import { Code, Database, Zap } from 'lucide-react'

export const ExamplesHero = memo(() => {
  return (
    <section className="py-16 md:py-24 lg:py-32">
      <div className="container mx-auto px-4 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Real-world{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              examples
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Discover how developers, researchers, and companies use PixCrawler to build 
            powerful image datasets for machine learning and computer vision projects.
          </p>
          
          <div className="flex flex-wrap justify-center gap-6 mb-12">
            <div className="flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3">
              <Database className="w-5 h-5 text-primary" />
              <span className="text-sm font-medium">50+ Use Cases</span>
            </div>
            <div className="flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3">
              <Code className="w-5 h-5 text-secondary" />
              <span className="text-sm font-medium">Code Examples</span>
            </div>
            <div className="flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3">
              <Zap className="w-5 h-5 text-warning" />
              <span className="text-sm font-medium">Ready to Use</span>
            </div>
          </div>

          <Button size="lg" className="mr-4">
            Try PixCrawler Free
          </Button>
          <Button variant="outline" size="lg">
            View Documentation
          </Button>
        </div>
      </div>
    </section>
  )
})

ExamplesHero.displayName = 'ExamplesHero'