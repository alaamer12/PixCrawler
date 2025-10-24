import {memo} from 'react'

interface TechCategory {
  title: string
  technologies: string[]
}

const TECH_STACK: TechCategory[] = [
  {
    title: 'Frontend',
    technologies: [
      'Next.js 15 with App Router',
      'TypeScript for type safety',
      'Tailwind CSS for styling',
      'Supabase for authentication'
    ]
  },
  {
    title: 'Backend',
    technologies: [
      'FastAPI with Python 3.10+',
      'PostgreSQL via Supabase',
      'Celery for task queuing',
      'Redis for caching'
    ]
  }
]

const TechCard = memo(({title, technologies}: TechCategory) => (
  <div className="border border-border rounded-lg p-6">
    <h3 className="text-lg font-semibold mb-3">{title}</h3>
    <ul className="space-y-2 text-muted-foreground">
      {technologies.map((tech) => (
        <li key={tech}>• {tech}</li>
      ))}
    </ul>
  </div>
))
TechCard.displayName = 'TechCard'

export const AboutTechStack = memo(() => {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-8 text-center">Built With Modern Tech</h2>
          <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
            PixCrawler uses cutting-edge technologies to deliver fast, reliable, and scalable dataset building.
          </p>
          
          <div className="grid md:grid-cols-2 gap-6">
            {TECH_STACK.map((category) => (
              <TechCard key={category.title} {...category} />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
})

AboutTechStack.displayName = 'AboutTechStack'
