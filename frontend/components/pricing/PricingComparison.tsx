'use client'

import {memo} from 'react'
import {Check, X} from 'lucide-react'

interface ComparisonFeature {
  name: string
  starter: boolean | string
  pro: boolean | string
  enterprise: boolean | string
}

const COMPARISON_FEATURES: ComparisonFeature[] = [
  {
    name: 'Monthly Images',
    starter: '1,000',
    pro: '50,000',
    enterprise: 'Unlimited'
  },
  {
    name: 'Concurrent Downloads',
    starter: '2',
    pro: '10',
    enterprise: 'Unlimited'
  },
  {
    name: 'Image Validation',
    starter: 'Basic',
    pro: 'Advanced',
    enterprise: 'Premium'
  },
  {
    name: 'Export Formats',
    starter: 'JSON, CSV',
    pro: 'All formats',
    enterprise: 'Custom formats'
  },
  {
    name: 'Data Retention',
    starter: '7 days',
    pro: '30 days',
    enterprise: 'Unlimited'
  },
  {
    name: 'API Access',
    starter: false,
    pro: true,
    enterprise: true
  },
  {
    name: 'Custom Keywords',
    starter: false,
    pro: true,
    enterprise: true
  },
  {
    name: 'Duplicate Detection',
    starter: false,
    pro: true,
    enterprise: true
  },
  {
    name: 'Priority Support',
    starter: false,
    pro: true,
    enterprise: true
  },
  {
    name: 'SLA Guarantee',
    starter: false,
    pro: false,
    enterprise: true
  },
  {
    name: 'On-premise Deployment',
    starter: false,
    pro: false,
    enterprise: true
  },
  {
    name: 'Custom Integrations',
    starter: false,
    pro: false,
    enterprise: true
  }
]

interface FeatureValueProps {
  value: boolean | string
}

const FeatureValue = memo(({value}: FeatureValueProps) => {
  if (typeof value === 'boolean') {
    return value ? (
      <Check className="w-5 h-5 text-success mx-auto"/>
    ) : (
      <X className="w-5 h-5 text-muted-foreground mx-auto"/>
    )
  }

  return (
    <span className="text-sm font-medium text-center block">{value}</span>
  )
})

FeatureValue.displayName = 'FeatureValue'

export const PricingComparison = memo(() => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Compare Plans
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Detailed comparison of all features across our pricing tiers to help you choose the right plan.
          </p>
        </div>

        <div className="max-w-5xl mx-auto">
          <div className="overflow-x-auto">
            <table className="w-full border border-border rounded-lg">
              <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left p-4 font-semibold">Features</th>
                <th className="text-center p-4 font-semibold">Starter</th>
                <th className="text-center p-4 font-semibold">Pro</th>
                <th className="text-center p-4 font-semibold">Enterprise</th>
              </tr>
              </thead>
              <tbody>
              {COMPARISON_FEATURES.map((feature, index) => (
                <tr key={`feature-${index}`}
                    className={`border-b border-border ${index % 2 === 0 ? 'bg-background' : 'bg-muted/20'}`}>
                  <td className="p-4 font-medium">{feature.name}</td>
                  <td className="p-4 text-center">
                    <FeatureValue value={feature.starter}/>
                  </td>
                  <td className="p-4 text-center">
                    <FeatureValue value={feature.pro}/>
                  </td>
                  <td className="p-4 text-center">
                    <FeatureValue value={feature.enterprise}/>
                  </td>
                </tr>
              ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  )
})

PricingComparison.displayName = 'PricingComparison'
