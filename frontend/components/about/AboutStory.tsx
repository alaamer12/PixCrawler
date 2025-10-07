'use client'

import {memo} from 'react'
import {Calendar, Globe, Lightbulb, Rocket} from 'lucide-react'

interface Milestone {
  year: string
  title: string
  description: string
  icon: React.ReactNode
}

const MILESTONES: Milestone[] = [
  {
    year: '2023',
    title: 'The Spark',
    description: 'Founded by AI researchers frustrated with the time spent collecting training data instead of building models.',
    icon: <Lightbulb className="w-5 h-5"/>
  },
  {
    year: '2024',
    title: 'First Launch',
    description: 'Released PixCrawler beta to a small group of developers and researchers, processing our first million images.',
    icon: <Rocket className="w-5 h-5"/>
  },
  {
    year: '2024',
    title: 'Global Reach',
    description: 'Expanded to serve developers worldwide, with users in over 50 countries building diverse datasets.',
    icon: <Globe className="w-5 h-5"/>
  },
  {
    year: '2025',
    title: 'The Future',
    description: 'Continuing to innovate with AI-powered dataset curation and advanced quality validation systems.',
    icon: <Calendar className="w-5 h-5"/>
  }
]

export const AboutStory = memo(() => {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Our Story
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              From a late-night frustration to a platform trusted by thousands of developers worldwide.
            </p>
          </div>

          <div className="space-y-8">
            {MILESTONES.map((milestone, index) => (
              <div key={milestone.year} className="flex gap-6 group">
                <div className="flex flex-col items-center">
                  <div
                    className="flex items-center justify-center w-12 h-12 bg-primary/10 text-primary rounded-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    {milestone.icon}
                  </div>
                  {index < MILESTONES.length - 1 && (
                    <div className="w-px h-16 bg-border mt-4"/>
                  )}
                </div>
                <div className="flex-1 pb-8">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-primary bg-primary/10 px-2 py-1 rounded-full">
                      {milestone.year}
                    </span>
                    <h3 className="text-xl font-semibold">{milestone.title}</h3>
                  </div>
                  <p className="text-muted-foreground">{milestone.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
})

AboutStory.displayName = 'AboutStory'
