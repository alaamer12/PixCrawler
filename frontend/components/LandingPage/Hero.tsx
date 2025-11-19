import Link from 'next/link'
import {memo} from 'react'
import {Button} from '@/components/ui/button'
import {HeroVisual} from './HeroVisual'

export const Hero = memo(() => {
  return (
    <section className="relative border-b border-border py-16 md:py-24 lg:py-32">
      <div className="container relative mx-auto px-4 lg:px-8 text-center">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 max-w-4xl mx-auto leading-tight">
          Build ML Datasets in <span
          className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">Minutes</span>
        </h1>
        <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          Automated image dataset creation for machine learning, research, and data science projects. Multi-source
          crawling with AI-powered validation.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button asChild variant="brand" size="lg">
            <Link href="/signup">
              Get Started Free
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/#features">
              View Demo
            </Link>
          </Button>
        </div>

        <HeroVisual/>
      </div>
    </section>
  )
})
Hero.displayName = 'Hero'
