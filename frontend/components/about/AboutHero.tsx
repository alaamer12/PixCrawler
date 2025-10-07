'use client'

import {memo} from 'react'
import {Button} from '@/components/ui/button'
import {ArrowRight, Target, Users, Zap} from 'lucide-react'

export const AboutHero = memo(() => {
  return (
    <section className="py-16 md:py-24 lg:py-32">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Empowering the future of{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              AI development
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            PixCrawler was born from a simple belief: building high-quality image datasets
            shouldn't be the hardest part of your machine learning journey. We're here to
            make AI development accessible, efficient, and scalable for everyone.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg">
              Start Building Today
              <ArrowRight className="w-4 h-4 ml-2"/>
            </Button>
            <Button variant="outline" size="lg">
              Meet Our Team
            </Button>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-3xl mx-auto">
            <div className="text-center">
              <div
                className="inline-flex items-center justify-center w-12 h-12 bg-primary/10 text-primary rounded-lg mb-4">
                <Target className="w-6 h-6"/>
              </div>
              <h3 className="font-semibold mb-2">Mission-Driven</h3>
              <p className="text-sm text-muted-foreground">
                Democratizing AI development through accessible tools
              </p>
            </div>
            <div className="text-center">
              <div
                className="inline-flex items-center justify-center w-12 h-12 bg-secondary/10 text-secondary rounded-lg mb-4">
                <Users className="w-6 h-6"/>
              </div>
              <h3 className="font-semibold mb-2">Community-First</h3>
              <p className="text-sm text-muted-foreground">
                Built by developers, for developers worldwide
              </p>
            </div>
            <div className="text-center">
              <div
                className="inline-flex items-center justify-center w-12 h-12 bg-warning/10 text-warning rounded-lg mb-4">
                <Zap className="w-6 h-6"/>
              </div>
              <h3 className="font-semibold mb-2">Innovation-Led</h3>
              <p className="text-sm text-muted-foreground">
                Cutting-edge technology for tomorrow's solutions
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
})

AboutHero.displayName = 'AboutHero'
