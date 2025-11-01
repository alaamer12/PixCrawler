import {memo} from 'react'
import {Code2, Database, Zap} from 'lucide-react'

interface Feature {
  icon: typeof Database
  title: string
  description: string
}

const FEATURES: Feature[] = [
  {
    icon: Database,
    title: 'Multi-Source Crawling',
    description: 'Collect images from multiple search engines and sources simultaneously for comprehensive datasets.'
  },
  {
    icon: Zap,
    title: 'Automated Validation',
    description: 'AI-powered quality checks, deduplication, and validation ensure clean, production-ready datasets.'
  },
  {
    icon: Code2,
    title: 'ML-Ready Output',
    description: 'Organized folder structures, metadata generation, and multiple export formats for immediate use.'
  }
]

const FeatureCard = memo(({icon: Icon, title, description}: Feature) => (
  <div className="text-center">
    <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
      <Icon className="w-8 h-8 text-primary"/>
    </div>
    <h3 className="text-xl font-semibold mb-3">{title}</h3>
    <p className="text-muted-foreground">{description}</p>
  </div>
))
FeatureCard.displayName = 'FeatureCard'

export const AboutFeatures = memo(() => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-12 text-center">What We Do</h2>

          <div className="grid md:grid-cols-3 gap-8">
            {FEATURES.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
})

AboutFeatures.displayName = 'AboutFeatures'
