'use client'

import {memo, useState} from 'react'
import {PricingCard} from './PricingCard'
import {PRICING_PLANS, CREDIT_PACKAGES} from '@/lib/payments/plans'
import {Button} from '@/components/ui/button'
import {Tabs, TabsContent, TabsList, TabsTrigger} from '@/components/ui/tabs'
import {Card, CardContent} from '@/components/ui/card'
import {useAuth} from '@/lib/auth/hooks'
import {useRouter} from 'next/navigation'
import {MessageSquare, FileText, Sparkles} from 'lucide-react'

interface PricingGridProps {
  currentPlan?: string
  showCredits?: boolean
  className?: string
}

export const PricingGrid = memo(({
                                   currentPlan,
                                   showCredits = true,
                                   className = ''
                                 }: PricingGridProps) => {
  const [isLoading, setIsLoading] = useState(false)
  const {user} = useAuth()
  const router = useRouter()

  const handleSelectPlan = async (planId: string) => {
    if (!user) {
      router.push('/auth/login?redirect=/pricing')
      return
    }

    // Handle free plan
    if (planId === 'starter') {
      router.push('/dashboard')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('/api/payments/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          planId,
          userId: user.id,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to create checkout session')
      }

      const {url} = await response.json()

      if (url) {
        window.location.href = url
      }
    } catch (error) {
      console.error('Error creating checkout session:', error)
      // You might want to show a toast notification here
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`w-full ${className}`}>
      <Tabs defaultValue="plans" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-8 max-w-md mx-auto">
          <TabsTrigger value="plans" className="flex items-center gap-2">
            <Sparkles className="w-4 h-4"/>
            Subscription Plans
          </TabsTrigger>
          {showCredits && (
            <TabsTrigger value="credits" className="flex items-center gap-2">
              <FileText className="w-4 h-4"/>
              Credit Packages
            </TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="plans" className="space-y-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Choose Your Plan</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Start building amazing image datasets today. Upgrade or downgrade at any time.
            </p>
          </div>

          {/* Subscription Plans */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {PRICING_PLANS.map((plan) => (
              <PricingCard
                key={plan.id}
                plan={plan}
                onSelectPlan={handleSelectPlan}
                isLoading={isLoading}
                currentPlan={currentPlan}
              />
            ))}
          </div>

          {/* Features Comparison */}
          <div className="mt-12">
            <h3 className="text-xl font-bold text-center mb-6">Compare Features</h3>
            <div className="overflow-x-auto">
              <table className="w-full border border-border rounded-lg">
                <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left p-4 font-medium">Feature</th>
                  {PRICING_PLANS.map(plan => (
                    <th key={plan.id} className="text-center p-4 font-medium min-w-[120px]">
                      {plan.name}
                    </th>
                  ))}
                </tr>
                </thead>
                <tbody>
                <tr className="border-b border-border">
                  <td className="p-4 font-medium">Monthly Images</td>
                  <td className="p-4 text-center">1,000</td>
                  <td className="p-4 text-center">10,000</td>
                  <td className="p-4 text-center">50,000</td>
                  <td className="p-4 text-center">Pay per use</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="p-4 font-medium">Datasets</td>
                  <td className="p-4 text-center">3</td>
                  <td className="p-4 text-center">Unlimited</td>
                  <td className="p-4 text-center">Unlimited</td>
                  <td className="p-4 text-center">Unlimited</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="p-4 font-medium">API Access</td>
                  <td className="p-4 text-center">❌</td>
                  <td className="p-4 text-center">✅</td>
                  <td className="p-4 text-center">✅</td>
                  <td className="p-4 text-center">✅</td>
                </tr>
                <tr className="border-b border-border">
                  <td className="p-4 font-medium">Priority Support</td>
                  <td className="p-4 text-center">❌</td>
                  <td className="p-4 text-center">✅</td>
                  <td className="p-4 text-center">✅</td>
                  <td className="p-4 text-center">❌</td>
                </tr>
                <tr>
                  <td className="p-4 font-medium">Custom Integrations</td>
                  <td className="p-4 text-center">❌</td>
                  <td className="p-4 text-center">❌</td>
                  <td className="p-4 text-center">✅</td>
                  <td className="p-4 text-center">❌</td>
                </tr>
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>

        {showCredits && (
          <TabsContent value="credits" className="space-y-8">
            {/* Header */}
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">One-Time Credit Packages</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Purchase credits that never expire. Perfect for occasional use or supplementing your subscription.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {CREDIT_PACKAGES.map((pkg) => (
                <PricingCard
                  key={pkg.id}
                  plan={pkg}
                  onSelectPlan={handleSelectPlan}
                  isLoading={isLoading}
                />
              ))}
            </div>

            {/* Credit Benefits */}
            <Card className="max-w-2xl mx-auto">
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-4 text-center">Why Choose Credits?</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>Never expire</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>No monthly commitment</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>Stackable with subscriptions</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>Bulk discounts available</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>Perfect for testing</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-primary rounded-full"></div>
                      <span>Instant activation</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Enterprise CTA */}
      <div className="mt-12 text-center">
        <Card className="bg-gradient-to-r from-primary/5 to-secondary/5 border-primary/20 max-w-2xl mx-auto">
          <CardContent className="pt-6">
            <h3 className="text-xl font-bold mb-2">Need Something Custom?</h3>
            <p className="text-muted-foreground mb-4">
              Looking for enterprise features, custom integrations, volume discounts, or white-label solutions?
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button variant="outline" size="lg" className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4"/>
                Contact Sales
              </Button>
              <Button variant="outline" size="lg">
                Schedule Demo
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
})

PricingGrid.displayName = 'PricingGrid'
