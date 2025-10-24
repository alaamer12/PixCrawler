'use client'

import {useState} from 'react'
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {
  CreditCard,
  Download,
  Receipt,
  Calendar,
  DollarSign,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  ExternalLink,
  Sparkles
} from 'lucide-react'
import type {User} from '@supabase/supabase-js'
import {useRouter} from 'next/navigation'
import {Bar, BarChart, CartesianGrid, XAxis, Pie, PieChart, Cell} from 'recharts'
import {ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent, type ChartConfig} from '@/components/ui/chart'

interface BillingPageProps {
  user: User
  isDevMode: boolean
}

// Mock data for dev mode
const DEV_MOCK_DATA = {
  currentPlan: {
    name: 'Pro Plan',
    status: 'active',
    price: 29.99,
    billingCycle: 'monthly',
    nextBillingDate: '2025-11-24',
    credits: 1000,
    creditsUsed: 342,
  },
  paymentMethod: {
    type: 'Visa',
    last4: '4242',
    expiryMonth: 12,
    expiryYear: 2026,
  },
  invoices: [
    {
      id: 'inv_001',
      date: '2025-10-24',
      amount: 29.99,
      status: 'paid',
      description: 'Pro Plan - Monthly',
      downloadUrl: '#',
    },
    {
      id: 'inv_002',
      date: '2025-09-24',
      amount: 29.99,
      status: 'paid',
      description: 'Pro Plan - Monthly',
      downloadUrl: '#',
    },
    {
      id: 'inv_003',
      date: '2025-08-24',
      amount: 29.99,
      status: 'paid',
      description: 'Pro Plan - Monthly',
      downloadUrl: '#',
    },
  ],
  usage: {
    datasetsCreated: 12,
    imagesProcessed: 3420,
    storageUsed: '2.4 GB',
  },
}

// Chart data with vibrant colors
const creditsChartData = [
  { day: 'Mon', credits: 650, fill: '#8b5cf6' },
  { day: 'Tue', credits: 720, fill: '#8b5cf6' },
  { day: 'Wed', credits: 580, fill: '#8b5cf6' },
  { day: 'Thu', credits: 800, fill: '#8b5cf6' },
  { day: 'Fri', credits: 680, fill: '#8b5cf6' },
  { day: 'Sat', credits: 750, fill: '#8b5cf6' },
  { day: 'Sun', credits: 660, fill: '#8b5cf6' },
]

const creditsChartConfig = {
  credits: {
    label: 'Credits Used',
    color: '#8b5cf6',
  },
} satisfies ChartConfig

const storageChartData = [
  { category: 'Images', value: 1.5, fill: '#3b82f6' },
  { category: 'Datasets', value: 0.7, fill: '#10b981' },
  { category: 'Other', value: 0.2, fill: '#f59e0b' },
]

const storageChartConfig = {
  value: {
    label: 'Storage (GB)',
  },
  Images: {
    label: 'Images',
    color: '#3b82f6',
  },
  Datasets: {
    label: 'Datasets',
    color: '#10b981',
  },
  Other: {
    label: 'Other',
    color: '#f59e0b',
  },
} satisfies ChartConfig

export function BillingPage({user, isDevMode}: BillingPageProps) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)

  // Use mock data in dev mode, otherwise fetch real data
  const billingData = isDevMode ? DEV_MOCK_DATA : null // TODO: Fetch real data from API

  const creditsPercentage = billingData
    ? ((billingData.currentPlan.credits - billingData.currentPlan.creditsUsed) / billingData.currentPlan.credits) * 100
    : 0

  const handleUpgradePlan = () => {
    router.push(isDevMode ? '/pricing?dev_bypass=true' : '/pricing')
  }

  const handleManageSubscription = () => {
    // TODO: Redirect to Stripe customer portal
    console.log('Manage subscription')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-primary/5 to-background py-12 px-8">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Billing & Usage
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage your subscription, payment methods, and view invoices
            </p>
          </div>
          {isDevMode && (
            <Badge variant="outline" className="bg-yellow-500/10 border-yellow-500/30 text-yellow-600">
              Dev Mode
            </Badge>
          )}
        </div>

        {/* Current Plan Card */}
        <Card className="relative overflow-hidden border-primary/20 shadow-lg">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-purple-500/5 to-primary/5" />
          <CardHeader className="relative">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <Sparkles className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-2xl">{billingData?.currentPlan.name}</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    ${billingData?.currentPlan.price}/month • Billed {billingData?.currentPlan.billingCycle}
                  </p>
                </div>
              </div>
              <Badge className="bg-green-500/10 text-green-600 border-green-500/20">
                <CheckCircle className="w-3 h-3 mr-1" />
                {billingData?.currentPlan.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="relative space-y-6">
            {/* Credits Usage */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Credits Remaining</span>
                <span className="font-semibold">
                  {billingData?.currentPlan.credits - billingData?.currentPlan.creditsUsed} / {billingData?.currentPlan.credits}
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-purple-500 transition-all duration-500"
                  style={{width: `${creditsPercentage}%`}}
                />
              </div>
            </div>

            {/* Next Billing Date */}
            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Next billing date</span>
              </div>
              <span className="font-semibold">{billingData?.currentPlan.nextBillingDate}</span>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button 
                onClick={handleUpgradePlan} 
                variant="default" 
                className="flex-1"
                leftIcon={<TrendingUp className="w-4 h-4" />}
              >
                Upgrade Plan
              </Button>
              <Button 
                onClick={handleManageSubscription} 
                variant="outline" 
                className="flex-1"
                leftIcon={<ExternalLink className="w-4 h-4" />}
              >
                Manage Subscription
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Credits Chart */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Credits Usage Over Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer config={creditsChartConfig} className="h-[300px] w-full">
                <BarChart data={creditsChartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis
                    dataKey="day"
                    tickLine={false}
                    tickMargin={10}
                    axisLine={false}
                    tick={{ fill: '#6b7280' }}
                  />
                  <ChartTooltip
                    content={<ChartTooltipContent />}
                    cursor={{ fill: '#8b5cf6', opacity: 0.1 }}
                  />
                  <Bar
                    dataKey="credits"
                    radius={[8, 8, 0, 0]}
                    fill="#8b5cf6"
                    activeBar={{ fill: '#7c3aed', stroke: '#6d28d9', strokeWidth: 2 }}
                  />
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>

          {/* Usage Stats Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Usage This Month
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-border/50">
                  <span className="text-sm text-muted-foreground">Datasets Created</span>
                  <span className="font-semibold">{billingData?.usage.datasetsCreated}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border/50">
                  <span className="text-sm text-muted-foreground">Images Processed</span>
                  <span className="font-semibold">{billingData?.usage.imagesProcessed.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-muted-foreground">Storage Used</span>
                  <span className="font-semibold">{billingData?.usage.storageUsed}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Payment Method Card */}
          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                Payment Method
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1 space-y-4">
                <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded flex items-center justify-center text-white text-xs font-bold">
                      {billingData?.paymentMethod.type}
                    </div>
                    <div>
                      <p className="font-medium">•••• {billingData?.paymentMethod.last4}</p>
                      <p className="text-xs text-muted-foreground">
                        Expires {billingData?.paymentMethod.expiryMonth}/{billingData?.paymentMethod.expiryYear}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline">Default</Badge>
                </div>
              </div>
              <Button variant="outline" className="w-full mt-4">
                Update Payment Method
              </Button>
            </CardContent>
          </Card>

          {/* Storage Distribution Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5" />
                Storage Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer config={storageChartConfig} className="h-[300px] w-full">
                <PieChart>
                  <ChartTooltip
                    content={<ChartTooltipContent nameKey="category" />}
                  />
                  <Pie
                    data={storageChartData}
                    dataKey="value"
                    nameKey="category"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={3}
                    activeIndex={0}
                    activeShape={{
                      outerRadius: 90,
                      stroke: '#fff',
                      strokeWidth: 3,
                      filter: 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))',
                    }}
                  >
                    {storageChartData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.fill}
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <ChartLegend content={<ChartLegendContent nameKey="category" />} />
                </PieChart>
              </ChartContainer>
            </CardContent>
          </Card>
        </div>

        {/* Invoices Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Receipt className="w-5 h-5" />
              Billing History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {billingData?.invoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className="flex items-center justify-between p-4 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-primary/10 rounded">
                      <Receipt className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{invoice.description}</p>
                      <p className="text-xs text-muted-foreground">{invoice.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-semibold">${invoice.amount.toFixed(2)}</p>
                      <Badge
                        variant="outline"
                        className="text-xs bg-green-500/10 text-green-600 border-green-500/20"
                      >
                        {invoice.status}
                      </Badge>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Help Section */}
        <Card className="border-blue-500/20 bg-blue-500/5">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <AlertCircle className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Need help with billing?</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Our support team is here to assist you with any billing questions or concerns.
                </p>
                <Button variant="outline" size="sm" onClick={() => router.push('/contact')}>
                  Contact Support
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
