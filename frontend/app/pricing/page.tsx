import { 
  PricingHero, 
  PricingCards, 
  PricingComparison, 
  PricingFAQ, 
  PricingCTA 
} from '@/components/pricing'

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <PricingHero />
      <PricingCards />
      <PricingComparison />
      <PricingFAQ />
      <PricingCTA />
    </div>
  )
}