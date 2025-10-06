'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { ExamplesHero } from '@/components/examples/ExamplesHero'
import { ExampleCategories } from '@/components/examples/ExampleCategories'

// Dynamically import heavy components
const ExampleGrid = dynamic(() => import('@/components/examples/ExampleGrid').then(mod => ({ default: mod.ExampleGrid })), {
    loading: () => <div className="py-16 flex justify-center"><div className="animate-pulse">Loading examples...</div></div>
})

const ExamplesStats = dynamic(() => import('@/components/examples/ExamplesStats').then(mod => ({ default: mod.ExamplesStats })), {
    loading: () => <div className="py-16 flex justify-center"><div className="animate-pulse">Loading stats...</div></div>
})

const ExamplesCTA = dynamic(() => import('@/components/examples/ExamplesCTA').then(mod => ({ default: mod.ExamplesCTA })), {
    loading: () => <div className="py-16 flex justify-center"><div className="animate-pulse">Loading...</div></div>
})

export default function ExamplesPage() {
    const [selectedCategory, setSelectedCategory] = useState('all')

    return (
        <main className="min-h-screen">
            <ExamplesHero />
            <ExampleCategories
                selectedCategory={selectedCategory}
                onCategoryChange={setSelectedCategory}
            />
            <ExampleGrid selectedCategory={selectedCategory} />
            <ExamplesStats />
            <ExamplesCTA />
        </main>
    )
}