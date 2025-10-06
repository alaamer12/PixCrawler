'use client'

import {memo, useMemo} from 'react'

interface Feature {
  icon: string
  title: string
  desc: string
}

const features: Feature[] = [
  {
    icon: '🤖',
    title: 'Intelligent Crawling',
    desc: 'Multiple discovery methods for comprehensive image collection from various sources'
  },
  {
    icon: '✓',
    title: 'Smart Validation',
    desc: 'Automated quality checks and integrity verification for every image'
  },
  {
    icon: '📁',
    title: 'Auto Organization',
    desc: 'Structured folder hierarchies and metadata generation automatically'
  },
  {
    icon: '🎯',
    title: 'AI Keywords',
    desc: 'Intelligent search term expansion and generation powered by AI'
  }
]

const FeatureCard = memo(({icon, title, desc}: Feature) => {
  return (
    <div className="border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="font-bold text-lg mb-3">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
    </div>
  )
})
FeatureCard.displayName = 'FeatureCard'

export const Features = memo(() => {
  const featureCards = useMemo(() =>
      features.map((feature, i) => (
        <FeatureCard key={i} {...feature} />
      )),
    []
  )

  return (
    <section id="features" className="border-b border-border py-16 md:py-24">
      <div className="container mx-auto px-4 lg:px-8">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 md:mb-16">
          Powerful Features
        </h2>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8 max-w-6xl mx-auto">
          {featureCards}
        </div>
      </div>
    </section>
  )
})
Features.displayName = 'Features'
