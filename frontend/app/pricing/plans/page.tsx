import { PricingGrid } from '@/components/stripe'

export default function PricingPlansPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">
            All Plans & Credit Packages
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Explore all our subscription plans and one-time credit packages. 
            Find the perfect fit for your needs.
          </p>
        </div>
        
        <PricingGrid showCredits={true} />
      </div>
    </div>
  )
}