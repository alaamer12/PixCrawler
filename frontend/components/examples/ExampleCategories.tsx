'use client'

import {memo} from 'react'
import {Brain, Building, Camera, Car, Filter, Leaf, Palette, Shield, ShoppingBag} from 'lucide-react'

interface Category {
  id: string
  name: string
  icon: React.ReactNode
  count: number
  description: string
}

const CATEGORIES: Category[] = [
  {
    id: 'all',
    name: 'All Examples',
    icon: <Filter className="w-5 h-5"/>,
    count: 50,
    description: 'Browse all available examples'
  },
  {
    id: 'computer-vision',
    name: 'Computer Vision',
    icon: <Brain className="w-5 h-5"/>,
    count: 12,
    description: 'Object detection, classification, and recognition'
  },
  {
    id: 'photography',
    name: 'Photography',
    icon: <Camera className="w-5 h-5"/>,
    count: 8,
    description: 'Photo enhancement, style transfer, and editing'
  },
  {
    id: 'ecommerce',
    name: 'E-commerce',
    icon: <ShoppingBag className="w-5 h-5"/>,
    count: 10,
    description: 'Product catalogs, recommendation systems'
  },
  {
    id: 'automotive',
    name: 'Automotive',
    icon: <Car className="w-5 h-5"/>,
    count: 6,
    description: 'Autonomous driving, vehicle recognition'
  },
  {
    id: 'nature',
    name: 'Nature & Environment',
    icon: <Leaf className="w-5 h-5"/>,
    count: 7,
    description: 'Wildlife, plants, environmental monitoring'
  },
  {
    id: 'architecture',
    name: 'Architecture',
    icon: <Building className="w-5 h-5"/>,
    count: 5,
    description: 'Building styles, urban planning, design'
  },
  {
    id: 'art',
    name: 'Art & Design',
    icon: <Palette className="w-5 h-5"/>,
    count: 4,
    description: 'Artistic styles, creative projects'
  },
  {
    id: 'security',
    name: 'Security',
    icon: <Shield className="w-5 h-5"/>,
    count: 3,
    description: 'Surveillance, anomaly detection'
  }
]

interface ExampleCategoriesProps {
  selectedCategory: string
  onCategoryChange: (category: string) => void
}

export const ExampleCategories = memo(({selectedCategory, onCategoryChange}: ExampleCategoriesProps) => {
  return (
    <section className="py-12 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">
            Browse by Category
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Explore examples organized by industry and use case to find inspiration for your next project.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-6xl mx-auto">
          {CATEGORIES.map((category) => (
            <button
              key={category.id}
              onClick={() => onCategoryChange(category.id)}
              className={`p-4 rounded-lg border text-left transition-all duration-200 hover:shadow-md ${
                selectedCategory === category.id
                  ? 'border-primary bg-primary/5 shadow-md'
                  : 'border-border bg-card hover:border-primary/50'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${
                  selectedCategory === category.id
                    ? 'bg-primary/10 text-primary'
                    : 'bg-muted text-muted-foreground'
                }`}>
                  {category.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-sm">{category.name}</h3>
                    <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded-full">
                      {category.count}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{category.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
})

ExampleCategories.displayName = 'ExampleCategories'
