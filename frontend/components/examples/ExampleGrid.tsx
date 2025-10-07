'use client'

import {memo, useMemo} from 'react'
import {Button} from '@/components/ui/button'
import {NextImage} from '@/components/Image'
import {Clock, Download, Eye, Star} from 'lucide-react'

// Types
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
  downloadUrl?: string
  featured?: boolean
}

type DifficultyLevel = 'Beginner' | 'Intermediate' | 'Advanced'

// Constants
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
    downloadUrl: '#',
    featured: true
  }
]

const DIFFICULTY_STYLES: Record<DifficultyLevel, string> = {
  Beginner: 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950',
  Intermediate: 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950',
  Advanced: 'text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-950'
}

// Utility Functions
const getDifficultyStyle = (difficulty: DifficultyLevel): string => {
  return DIFFICULTY_STYLES[difficulty]
}

const filterExamplesByCategory = (examples: Example[], category: string): Example[] => {
  if (category === 'all') return examples
  return examples.filter(example => example.category === category)
}

const separateFeaturedExamples = (examples: Example[]) => {
  const featured = examples.filter(example => example.featured)
  const regular = examples.filter(example => !example.featured)
  return {featured, regular}
}


interface CardImageProps {
  src: string
  alt: string
}

const CardImage = memo(({src, alt}: CardImageProps) => (
  <div className="relative overflow-hidden">
    <NextImage
      src={src}
      alt={alt}
      width={400}
      height={250}
      className="w-full h-52 object-cover group-hover:scale-110 transition-transform duration-500"
    />
    <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-black/10 to-transparent"/>
  </div>
))
CardImage.displayName = 'CardImage'

interface CardHeaderProps {
  title: string
  difficulty: DifficultyLevel
  description: string
}

const CardHeader = memo(({title, difficulty, description}: CardHeaderProps) => {
  const difficultyStyle = getDifficultyStyle(difficulty)

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-xl font-bold group-hover:text-primary transition-colors leading-tight">
          {title}
        </h3>
        <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap ${difficultyStyle}`}>
                    {difficulty}
                </span>
      </div>

      <p className="text-muted-foreground text-sm leading-relaxed line-clamp-2">
        {description}
      </p>
    </div>
  )
})
CardHeader.displayName = 'CardHeader'

interface CardStatsProps {
  imageCount: string
  timeToComplete: string
}

const CardStats = memo(({imageCount, timeToComplete}: CardStatsProps) => (
  <div className="flex items-center gap-5 text-xs text-muted-foreground py-3 border-y border-border/50">
    <div className="flex items-center gap-1.5">
      <Download className="w-4 h-4"/>
      <span className="font-medium">{imageCount}</span>
    </div>
    <div className="flex items-center gap-1.5">
      <Clock className="w-4 h-4"/>
      <span className="font-medium">{timeToComplete}</span>
    </div>
  </div>
))
CardStats.displayName = 'CardStats'

interface CardTagsProps {
  tags: string[]
}

const CardTags = memo(({tags}: CardTagsProps) => (
  <div className="flex flex-wrap gap-1.5">
    {tags.slice(0, 3).map((tag) => (
      <span
        key={tag}
        className="px-2.5 py-1 bg-muted/60 hover:bg-muted text-muted-foreground text-xs rounded-md transition-colors"
      >
                {tag}
            </span>
    ))}
  </div>
))
CardTags.displayName = 'CardTags'

interface CardActionsProps {
  demoUrl?: string
  downloadUrl?: string
}

const CardActions = memo(({demoUrl, downloadUrl}: CardActionsProps) => (
  <div className="flex items-center gap-2">
    {demoUrl && (
      <Button
        size="sm"
        variant="ghost"
        className="flex-1 hover:bg-primary/10 hover:text-primary border-2 py-6 rounded-xl"
      >
        <Eye className="w-4 h-4 mr-1.5"/>
      </Button>
    )}
    {downloadUrl && (
      <Button
        size="sm"
        className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm border-2 py-6 rounded-xl"
      >
        <Download className="w-4 h-4 mr-1.5"/>
      </Button>
    )}
  </div>
))
CardActions.displayName = 'CardActions'

// Main Card Component
interface ExampleCardProps {
  example: Example
}

const ExampleCard = memo(({example}: ExampleCardProps) => {
  return (
    <div
      className="bg-card border border-border/50 rounded-xl overflow-hidden hover:shadow-xl hover:border-primary/20 transition-all duration-300 group relative">

      <CardImage src={example.thumbnail} alt={example.title}/>

      <div className="p-6 space-y-4">
        <CardHeader
          title={example.title}
          difficulty={example.difficulty}
          description={example.description}
        />

        <CardStats
          imageCount={example.imageCount}
          timeToComplete={example.timeToComplete}
        />

        <CardTags tags={example.tags}/>

        <CardActions
          demoUrl={example.demoUrl}
          downloadUrl={example.downloadUrl}
        />
      </div>
    </div>
  )
})
ExampleCard.displayName = 'ExampleCard'

// Section Components
interface SectionHeaderProps {
  title: string
  icon?: React.ReactNode
}

const SectionHeader = memo(({title, icon}: SectionHeaderProps) => (
  <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
    {icon}
    {title}
  </h2>
))
SectionHeader.displayName = 'SectionHeader'

interface ExampleGridSectionProps {
  examples: Example[]
}

const ExampleGridSection = memo(({examples}: ExampleGridSectionProps) => (
  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
    {examples.map((example) => (
      <ExampleCard key={example.id} example={example}/>
    ))}
  </div>
))
ExampleGridSection.displayName = 'ExampleGridSection'

const EmptyState = memo(() => (
  <div className="text-center py-12">
    <p className="text-muted-foreground">No examples found for this category.</p>
  </div>
))
EmptyState.displayName = 'EmptyState'

// Main Export Component
interface ExampleGridProps {
  selectedCategory: string
}

export const ExampleGrid = memo(({selectedCategory}: ExampleGridProps) => {
  const filteredExamples = useMemo(
    () => filterExamplesByCategory(EXAMPLES, selectedCategory),
    [selectedCategory]
  )

  const {featured, regular} = useMemo(
    () => separateFeaturedExamples(filteredExamples),
    [filteredExamples]
  )

  const hasExamples = filteredExamples.length > 0

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        {featured.length > 0 && (
          <div className="mb-12">
            <SectionHeader
              title="Featured Examples"
              icon={<Star className="w-5 h-5 text-primary fill-current"/>}
            />
            <ExampleGridSection examples={featured}/>
          </div>
        )}

        {regular.length > 0 && (
          <div>
            <SectionHeader
              title={selectedCategory === 'all' ? 'All Examples' : 'More Examples'}
            />
            <ExampleGridSection examples={regular}/>
          </div>
        )}

        {!hasExamples && <EmptyState/>}
      </div>
    </section>
  )
})

ExampleGrid.displayName = 'ExampleGrid'
