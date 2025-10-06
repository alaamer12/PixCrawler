'use client'

import { memo, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { 
  ExternalLink, 
  Github, 
  Download, 
  Eye, 
  Clock,
  Tag,
  Star
} from 'lucide-react'

interface Example {
  id: string
  title: string
  description: string
  category: string
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced'
  imageCount: string
  timeToComplete: string
  tags: string[]
  thumbnail: string
  demoUrl?: string
  githubUrl?: string
  downloadUrl?: string
  featured?: boolean
}

const EXAMPLES: Example[] = [
  {
    id: '1',
    title: 'Dog Breed Classification',
    description: 'Build a comprehensive dataset of dog breeds for training classification models. Includes 120+ breeds with high-quality images.',
    category: 'computer-vision',
    difficulty: 'Beginner',
    imageCount: '15,000+',
    timeToComplete: '30 min',
    tags: ['Classification', 'Animals', 'CNN'],
    thumbnail: '/api/placeholder/400/250',
    demoUrl: '#',
    githubUrl: '#',
    downloadUrl: '#',
    featured: true
  },
  {
    id: '2',
    title: 'Fashion Product Catalog',
    description: 'Create a complete e-commerce fashion dataset with clothing items, accessories, and style variations for recommendation systems.',
    category: 'ecommerce',
    difficulty: 'Intermediate',
    imageCount: '25,000+',
    timeToComplete: '45 min',
    tags: ['E-commerce', 'Fashion', 'Recommendation'],
    thumbnail: '/api/placeholder/400/250',
    demoUrl: '#',
    githubUrl: '#',
    downloadUrl: '#'
  },
  {
    id: '3',
    title: 'Autonomous Vehicle Training',
    description: 'Street scenes, traffic signs, and vehicle detection dataset for autonomous driving research and development.',
    category: 'automotive',
    difficulty: 'Advanced',
    imageCount: '50,000+',
    timeToComplete: '2 hours',
    tags: ['Autonomous', 'Detection', 'Safety'],
    thumbnail: '/api/placeholder/400/250',
    demoUrl: '#',
    githubUrl: '#',
    downloadUrl: '#',
    featured: true
  },
  {
    id: '4',
    title: 'Architectural Styles Dataset',
    description: 'Comprehensive collection of architectural styles from around the world for style classification and analysis.',
    category: 'architecture',
    difficulty: 'Intermediate',
    imageCount: '8,000+',
    timeToComplete: '25 min',
    tags: ['Architecture', 'Styles', 'Culture'],
    thumbnail: '/api/placeholder/400/250',
    demoUrl: '#',
    downloadUrl: '#'
  },
  {
    id: '5',
    title: 'Wildlife Conservation',
    description: 'Endangered species monitoring dataset for conservation efforts and wildlife population tracking.',
    category: 'nature',
    difficulty: 'Intermediate',
    imageCount: '12,000+',
    timeToComplete: '40 min',
    tags: ['Wildlife', 'Conservation', 'Monitoring'],
    thumbnail: '/api/placeholder/400/250',
    demoUrl: '#',
    githubUrl: '#',
    downloadUrl: '#'
  },
  {
    id: '6',
    title: 'Medical Imaging Dataset',
    description: 'Curated medical images for diagnostic AI training, including X-rays, MRIs, and CT scans.',
    category: 'computer-vision',
    difficulty: 'Advanced',
    imageCount: '30,000+',
    timeToComplete: '1.5 hours',
    tags: ['Medical', 'Diagnostics', 'Healthcare'],
    thumbnail: '/api/placeholder/400/250',
    demoUrl: '#',
    githubUrl: '#',
    downloadUrl: '#',
    featured: true
  }
]

interface ExampleCardProps {
  example: Example
}

const ExampleCard = memo(({ example }: ExampleCardProps) => {
  const difficultyColor = {
    'Beginner': 'text-success bg-success/10',
    'Intermediate': 'text-warning bg-warning/10',
    'Advanced': 'text-destructive bg-destructive/10'
  }[example.difficulty]

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden hover:shadow-lg transition-all duration-200 group">
      {example.featured && (
        <div className="absolute top-4 left-4 z-10">
          <div className="bg-gradient-to-r from-primary to-secondary text-primary-foreground px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
            <Star className="w-3 h-3 fill-current" />
            Featured
          </div>
        </div>
      )}
      
      <div className="relative">
        <img 
          src={example.thumbnail} 
          alt={example.title}
          className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-200"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
      </div>
      
      <div className="p-6">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold group-hover:text-primary transition-colors">
            {example.title}
          </h3>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${difficultyColor}`}>
            {example.difficulty}
          </span>
        </div>
        
        <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
          {example.description}
        </p>
        
        <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
          <div className="flex items-center gap-1">
            <Download className="w-3 h-3" />
            {example.imageCount}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {example.timeToComplete}
          </div>
        </div>
        
        <div className="flex flex-wrap gap-1 mb-4">
          {example.tags.slice(0, 3).map((tag) => (
            <span 
              key={tag}
              className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded-md"
            >
              {tag}
            </span>
          ))}
        </div>
        
        <div className="flex items-center gap-2">
          {example.demoUrl && (
            <Button size="sm" variant="outline" className="flex-1">
              <Eye className="w-3 h-3 mr-1" />
              Demo
            </Button>
          )}
          {example.githubUrl && (
            <Button size="sm" variant="outline">
              <Github className="w-3 h-3" />
            </Button>
          )}
          {example.downloadUrl && (
            <Button size="sm" variant="default">
              <Download className="w-3 h-3 mr-1" />
              Use
            </Button>
          )}
        </div>
      </div>
    </div>
  )
})

ExampleCard.displayName = 'ExampleCard'

interface ExampleGridProps {
  selectedCategory: string
}

export const ExampleGrid = memo(({ selectedCategory }: ExampleGridProps) => {
  const filteredExamples = useMemo(() => {
    if (selectedCategory === 'all') return EXAMPLES
    return EXAMPLES.filter(example => example.category === selectedCategory)
  }, [selectedCategory])

  const featuredExamples = useMemo(() => 
    filteredExamples.filter(example => example.featured), 
    [filteredExamples]
  )

  const regularExamples = useMemo(() => 
    filteredExamples.filter(example => !example.featured), 
    [filteredExamples]
  )

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        {featuredExamples.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Star className="w-5 h-5 text-primary fill-current" />
              Featured Examples
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredExamples.map((example) => (
                <ExampleCard key={example.id} example={example} />
              ))}
            </div>
          </div>
        )}

        {regularExamples.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">
              {selectedCategory === 'all' ? 'All Examples' : 'More Examples'}
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {regularExamples.map((example) => (
                <ExampleCard key={example.id} example={example} />
              ))}
            </div>
          </div>
        )}

        {filteredExamples.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No examples found for this category.</p>
          </div>
        )}
      </div>
    </section>
  )
})

ExampleGrid.displayName = 'ExampleGrid'