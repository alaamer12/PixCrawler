import {PricingCards, PricingComparison, PricingCTA, PricingFAQ, PricingHero} from '@/components/pricing'

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <PricingHero/>
      <PricingCards/>
      <PricingComparison/>
      <PricingFAQ/>
      <PricingCTA/>
    </div>
  )
}
