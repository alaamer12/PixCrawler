import {Metadata} from 'next'
import dynamic from 'next/dynamic'
import {PricingHero} from '@/components/pricing/PricingHero'

// Dynamically import heavy components to improve initial load
const PricingCards = dynamic(() => import('@/components/pricing/PricingCards').then(mod => ({default: mod.PricingCards})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading pricing...</div>
  </div>
})

const PricingComparison = dynamic(() => import('@/components/pricing/PricingComparison').then(mod => ({default: mod.PricingComparison})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading comparison...</div>
  </div>
})

const PricingFAQ = dynamic(() => import('@/components/pricing/PricingFAQ').then(mod => ({default: mod.PricingFAQ})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading FAQ...</div>
  </div>
})

const PricingCTA = dynamic(() => import('@/components/pricing/PricingCTA').then(mod => ({default: mod.PricingCTA})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading...</div>
  </div>
})

export const metadata: Metadata = {
  title: 'Pricing - PixCrawler',
  description: 'Simple, transparent pricing for PixCrawler. Start free and scale as you grow. Perfect for developers, researchers, and enterprises.',
  keywords: ['pricing', 'plans', 'image datasets', 'machine learning', 'computer vision', 'API'],
}

export default function PricingPage() {
  return (
    <main className="min-h-screen">
      <PricingHero/>
      <PricingCards/>
      <PricingComparison/>
      <PricingFAQ/>
      <PricingCTA/>
    </main>
  )
}
