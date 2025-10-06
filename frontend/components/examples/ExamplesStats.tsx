'use client'

import { memo } from 'react'
import { TrendingUp, Users, Database, Clock } from 'lucide-react'

interface Stat {
  icon: React.ReactNode
  value: string
  label: string
  description: string
}

const STATS: Stat[] = [
  {
    icon: <Database className="w-6 h-6" />,
    value: '50+',
    label: 'Example Datasets',
    description: 'Curated examples across multiple industries'
  },
  {
    icon: <Users className="w-6 h-6" />,
    value: '10,000+',
    label: 'Active Users',
    description: 'Developers and researchers worldwide'
  },
  {
    icon: <TrendingUp className="w-6 h-6" />,
    value: '99.9%',
    label: 'Success Rate',
    description: 'Reliable image collection and processing'
  },
  {
    icon: <Clock className="w-6 h-6" />,
    value: '< 30min',
    label: 'Average Setup',
    description: 'From idea to working dataset'
  }
]

export const ExamplesStats = memo(() => {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">
            Trusted by Developers Worldwide
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Join thousands of developers, researchers, and companies who rely on PixCrawler 
            for their machine learning and computer vision projects.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
          {STATS.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-primary/10 text-primary rounded-lg mb-4">
                {stat.icon}
              </div>
              <div className="text-3xl font-bold mb-2">{stat.value}</div>
              <div className="font-semibold mb-1">{stat.label}</div>
              <div className="text-sm text-muted-foreground">{stat.description}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
})

ExamplesStats.displayName = 'ExamplesStats'