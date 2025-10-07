'use client'

import {memo, useCallback, useState} from 'react'
import {ChevronDown} from 'lucide-react'

interface FAQItem {
  question: string
  answer: string
}

const FAQ_ITEMS: FAQItem[] = [
  {
    question: 'How does the free plan work?',
    answer: 'The free plan gives you 1,000 images per month with basic features. Perfect for testing PixCrawler and small projects. No credit card required.'
  },
  {
    question: 'Can I change plans anytime?',
    answer: 'Yes! You can upgrade, downgrade, or cancel your plan at any time. Changes take effect immediately, and we\'ll prorate any billing adjustments.'
  },
  {
    question: 'What happens if I exceed my image limit?',
    answer: 'If you exceed your monthly limit, downloads will be paused until the next billing cycle or you can upgrade your plan instantly to continue.'
  },
  {
    question: 'Do you offer refunds?',
    answer: 'We offer a 14-day money-back guarantee for all paid plans. If you\'re not satisfied, contact us for a full refund.'
  },
  {
    question: 'What payment methods do you accept?',
    answer: 'We accept all major credit cards (Visa, MasterCard, American Express) and PayPal. Enterprise customers can also pay via bank transfer.'
  },
  {
    question: 'Is there a setup fee?',
    answer: 'No setup fees, ever. You only pay for your chosen plan, and you can start with our free tier immediately.'
  },
  {
    question: 'Can I use PixCrawler for commercial projects?',
    answer: 'Yes! All our plans, including the free tier, allow commercial use. Just make sure to respect image copyrights and licensing.'
  },
  {
    question: 'What kind of support do you provide?',
    answer: 'Free users get community support, Pro users get priority email support, and Enterprise customers get dedicated support with SLA guarantees.'
  }
]

interface FAQItemProps {
  item: FAQItem
  isOpen: boolean
  onToggle: () => void
}

const FAQItemComponent = memo(({item, isOpen, onToggle}: FAQItemProps) => {
  return (
    <div className="border border-border rounded-lg">
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-muted/50 transition-colors duration-200"
        aria-expanded={isOpen}
      >
        <span className="font-medium">{item.question}</span>
        <ChevronDown className={`w-5 h-5 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}/>
      </button>
      {isOpen && (
        <div className="px-6 pb-4 animate-fade-in">
          <p className="text-muted-foreground">{item.answer}</p>
        </div>
      )}
    </div>
  )
})

FAQItemComponent.displayName = 'FAQItemComponent'

export const PricingFAQ = memo(() => {
  const [openItems, setOpenItems] = useState<Set<number>>(new Set())

  const toggleItem = useCallback((index: number) => {
    setOpenItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(index)) {
        newSet.delete(index)
      } else {
        newSet.add(index)
      }
      return newSet
    })
  }, [])

  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-muted-foreground">
              Everything you need to know about PixCrawler pricing and plans.
            </p>
          </div>

          <div className="space-y-4">
            {FAQ_ITEMS.map((item, index) => (
              <FAQItemComponent
                key={index}
                item={item}
                isOpen={openItems.has(index)}
                onToggle={() => toggleItem(index)}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  )
})

PricingFAQ.displayName = 'PricingFAQ'
