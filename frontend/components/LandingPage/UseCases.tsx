'use client'

import {memo, useMemo} from 'react'

interface UseCase {
  icon: string
  title: string
  items: string[]
}

const useCases: UseCase[] = [
  {
    icon: '🔬',
    title: 'Research & Academia',
    items: [
      'Custom datasets for CV research',
      'Balanced training sets',
      'Benchmark dataset generation',
      'Academic project support'
    ]
  },
  {
    icon: '🏢',
    title: 'Enterprise & Startups',
    items: [
      'Rapid ML prototyping',
      'Product image datasets',
      'Visual content analysis',
      'Business intelligence'
    ]
  },
  {
    icon: '👨‍💻',
    title: 'Individual Developers',
    items: [
      'Personal ML projects',
      'Learning & education',
      'Portfolio projects',
      'Experimentation'
    ]
  }
]

const UseCaseCard = memo(({icon, title, items}: UseCase) => {
  return (
    <div className="border border-border rounded-lg p-8 hover:shadow-lg transition-shadow">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="font-bold text-xl mb-4">{title}</h3>
      <ul className="text-sm text-muted-foreground space-y-2">
        {items.map((item, j) => (
          <li key={j} className="flex items-start">
            <span className="mr-2">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
})
UseCaseCard.displayName = 'UseCaseCard'

export const UseCases = memo(() => {
  const useCaseCards = useMemo(() =>
      useCases.map((useCase, i) => (
        <UseCaseCard key={i} {...useCase} />
      )),
    []
  )

  return (
    <section id="use-cases" className="border-b border-border py-16 md:py-24">
      <div className="container mx-auto px-4 lg:px-8">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 md:mb-16">
          Built For Everyone
        </h2>

        <div className="grid md:grid-cols-3 gap-6 md:gap-8 max-w-6xl mx-auto">
          {useCaseCards}
        </div>
      </div>
    </section>
  )
})
UseCases.displayName = 'UseCases'
