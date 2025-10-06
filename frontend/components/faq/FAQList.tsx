'use client'

import { memo, useState, useCallback, useMemo } from 'react'
import { ChevronDown, Search } from 'lucide-react'

interface FAQItem {
  id: string
  question: string
  answer: string
  category: string
  tags: string[]
}

const FAQ_ITEMS: FAQItem[] = [
  // Getting Started
  {
    id: '1',
    question: 'How do I get started with PixCrawler?',
    answer: 'Getting started is easy! Sign up for a free account, verify your email, and you can immediately start creating your first dataset. Our onboarding guide will walk you through the process step by step.',
    category: 'getting-started',
    tags: ['signup', 'onboarding', 'beginner']
  },
  {
    id: '2',
    question: 'Do I need a credit card to start?',
    answer: 'No! Our free plan doesn\'t require a credit card. You can start building datasets immediately with 1,000 images per month. You only need to add payment information when upgrading to a paid plan.',
    category: 'getting-started',
    tags: ['free', 'credit card', 'payment']
  },
  {
    id: '3',
    question: 'What image formats are supported?',
    answer: 'PixCrawler supports all major image formats including JPEG, PNG, WebP, GIF, and SVG. Images are automatically validated and can be converted to your preferred format during download.',
    category: 'getting-started',
    tags: ['formats', 'jpeg', 'png', 'webp']
  },

  // Billing & Plans
  {
    id: '4',
    question: 'Can I change my plan anytime?',
    answer: 'Yes! You can upgrade, downgrade, or cancel your plan at any time. Changes take effect immediately, and we\'ll prorate any billing adjustments. No long-term contracts or cancellation fees.',
    category: 'billing',
    tags: ['plans', 'upgrade', 'cancel', 'prorate']
  },
  {
    id: '5',
    question: 'Do you offer refunds?',
    answer: 'We offer a 14-day money-back guarantee for all paid plans. If you\'re not satisfied with PixCrawler, contact our support team within 14 days of your purchase for a full refund.',
    category: 'billing',
    tags: ['refund', 'money-back', 'guarantee']
  },
  {
    id: '6',
    question: 'What happens if I exceed my plan limits?',
    answer: 'If you exceed your monthly image limit, downloads will be paused until the next billing cycle. You can upgrade your plan instantly to continue, or wait for your limits to reset next month.',
    category: 'billing',
    tags: ['limits', 'overage', 'upgrade']
  },

  // Features & Usage
  {
    id: '7',
    question: 'How does image validation work?',
    answer: 'Our AI-powered validation checks for image quality, relevance, duplicates, and potential copyright issues. You can customize validation settings and review flagged images before finalizing your dataset.',
    category: 'features',
    tags: ['validation', 'quality', 'duplicates', 'AI']
  },
  {
    id: '8',
    question: 'Can I use custom keywords for image search?',
    answer: 'Yes! Pro and Enterprise plans include custom keyword expansion using AI. You can also provide your own keyword lists, use boolean operators, and exclude specific terms.',
    category: 'features',
    tags: ['keywords', 'search', 'AI', 'custom']
  },
  {
    id: '9',
    question: 'What export formats are available?',
    answer: 'We support multiple export formats including JSON, CSV, YAML, and TXT. You can also export metadata, annotations, and organize files in custom directory structures.',
    category: 'features',
    tags: ['export', 'json', 'csv', 'yaml', 'metadata']
  },

  // Security & Privacy
  {
    id: '10',
    question: 'How is my data protected?',
    answer: 'We use enterprise-grade security including AES-256 encryption, secure data centers, and regular security audits. Your datasets are private by default and never shared without your permission.',
    category: 'security',
    tags: ['encryption', 'privacy', 'security', 'data protection']
  },
  {
    id: '11',
    question: 'Do you comply with GDPR and other privacy laws?',
    answer: 'Yes, we\'re fully compliant with GDPR, CCPA, and other major privacy regulations. We provide data processing agreements for enterprise customers and respect all user privacy rights.',
    category: 'security',
    tags: ['GDPR', 'CCPA', 'compliance', 'privacy']
  },

  // Technical
  {
    id: '12',
    question: 'Is there an API available?',
    answer: 'Yes! Pro and Enterprise plans include full API access. You can programmatically create datasets, monitor progress, and integrate PixCrawler into your existing workflows.',
    category: 'technical',
    tags: ['API', 'integration', 'programmatic', 'workflow']
  },
  {
    id: '13',
    question: 'What if I encounter technical issues?',
    answer: 'Our support team is here to help! Free users get community support, Pro users get priority email support, and Enterprise customers get dedicated support with SLA guarantees.',
    category: 'technical',
    tags: ['support', 'issues', 'troubleshooting', 'help']
  }
]

interface FAQItemProps {
  item: FAQItem
  isOpen: boolean
  onToggle: () => void
}

const FAQItemComponent = memo(({ item, isOpen, onToggle }: FAQItemProps) => {
  return (
    <div className="border border-border rounded-lg bg-card">
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-muted/50 transition-colors duration-200"
        aria-expanded={isOpen}
      >
        <span className="font-medium pr-4">{item.question}</span>
        <ChevronDown className={`w-5 h-5 transition-transform duration-200 flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div className="px-6 pb-4 animate-fade-in">
          <p className="text-muted-foreground leading-relaxed">{item.answer}</p>
          <div className="flex flex-wrap gap-1 mt-3">
            {item.tags.map((tag) => (
              <span 
                key={tag}
                className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded-md"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
})

FAQItemComponent.displayName = 'FAQItemComponent'

interface FAQListProps {
  selectedCategory: string
}

export const FAQList = memo(({ selectedCategory }: FAQListProps) => {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')

  const toggleItem = useCallback((id: string) => {
    setOpenItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }, [])

  const filteredItems = useMemo(() => {
    let items = FAQ_ITEMS

    // Filter by category
    if (selectedCategory !== 'all') {
      items = items.filter(item => item.category === selectedCategory)
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      items = items.filter(item => 
        item.question.toLowerCase().includes(query) ||
        item.answer.toLowerCase().includes(query) ||
        item.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    return items
  }, [selectedCategory, searchQuery])

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Search Bar */}
          <div className="relative mb-8">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search questions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
            />
          </div>

          {/* FAQ Items */}
          <div className="space-y-4">
            {filteredItems.map((item) => (
              <FAQItemComponent
                key={item.id}
                item={item}
                isOpen={openItems.has(item.id)}
                onToggle={() => toggleItem(item.id)}
              />
            ))}
          </div>

          {filteredItems.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                {searchQuery 
                  ? `No questions found matching "${searchQuery}"`
                  : 'No questions found for this category.'
                }
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
})

FAQList.displayName = 'FAQList'