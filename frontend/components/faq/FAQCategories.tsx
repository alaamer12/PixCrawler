'use client'

import {memo} from 'react'
import {Code, CreditCard, Filter, Rocket, Settings, Shield} from 'lucide-react'

interface FAQCategory {
  id: string
  name: string
  icon: React.ReactNode
  count: number
  description: string
}

const FAQ_CATEGORIES: FAQCategory[] = [
  {
    id: 'all',
    name: 'All Questions',
    icon: <Filter className="w-5 h-5"/>,
    count: 32,
    description: 'Browse all frequently asked questions'
  },
  {
    id: 'getting-started',
    name: 'Getting Started',
    icon: <Rocket className="w-5 h-5"/>,
    count: 8,
    description: 'Account setup, first steps, and basic usage'
  },
  {
    id: 'billing',
    name: 'Billing & Plans',
    icon: <CreditCard className="w-5 h-5"/>,
    count: 6,
    description: 'Pricing, payments, upgrades, and refunds'
  },
  {
    id: 'features',
    name: 'Features & Usage',
    icon: <Settings className="w-5 h-5"/>,
    count: 10,
    description: 'Platform features, limits, and best practices'
  },
  {
    id: 'security',
    name: 'Security & Privacy',
    icon: <Shield className="w-5 h-5"/>,
    count: 4,
    description: 'Data protection, privacy, and compliance'
  },
  {
    id: 'technical',
    name: 'Technical',
    icon: <Code className="w-5 h-5"/>,
    count: 4,
    description: 'API, integrations, and troubleshooting'
  }
]

interface FAQCategoriesProps {
  selectedCategory: string
  onCategoryChange: (category: string) => void
}

export const FAQCategories = memo(({selectedCategory, onCategoryChange}: FAQCategoriesProps) => {
  return (
    <section className="py-12 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">
            Browse by Category
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Find answers quickly by browsing questions organized by topic.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl mx-auto">
          {FAQ_CATEGORIES.map((category) => (
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

FAQCategories.displayName = 'FAQCategories'
