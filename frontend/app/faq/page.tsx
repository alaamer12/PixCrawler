'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { FAQHero } from '@/components/faq/FAQHero'
import { FAQCategories } from '@/components/faq/FAQCategories'

// Dynamically import heavy components
const FAQList = dynamic(() => import('@/components/faq/FAQList').then(mod => ({ default: mod.FAQList })), {
  loading: () => <div className="py-16 flex justify-center"><div className="animate-pulse">Loading questions...</div></div>
})

const FAQSupport = dynamic(() => import('@/components/faq/FAQSupport').then(mod => ({ default: mod.FAQSupport })), {
  loading: () => <div className="py-16 flex justify-center"><div className="animate-pulse">Loading support...</div></div>
})

export default function FAQPage() {
  const [selectedCategory, setSelectedCategory] = useState('all')

  return (
    <main className="min-h-screen">
      <FAQHero />
      <FAQCategories 
        selectedCategory={selectedCategory}
        onCategoryChange={setSelectedCategory}
      />
      <FAQList selectedCategory={selectedCategory} />
      <FAQSupport />
    </main>
  )
}