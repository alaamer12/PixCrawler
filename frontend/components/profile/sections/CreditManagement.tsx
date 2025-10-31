'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import {
  CreditCard,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  Clock,
  AlertCircle,
  CheckCircle,
  Info,
  Plus,
  Minus,
  ArrowUp,
  ArrowDown,
  History,
  Receipt,
  Wallet,
  Zap,
  Package,
  ShoppingCart,
  Gift,
  Percent,
  Save,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface CreditTransaction {
  id: string
  date: string
  type: 'purchase' | 'usage' | 'refund' | 'bonus'
  description: string
  amount: number
  balance: number
  status: 'completed' | 'pending' | 'failed'
}

interface CreditPackage {
  id: string
  name: string
  credits: number
  price: number
  savings?: number
  popular?: boolean
}

export function CreditManagement() {
  const { toast } = useToast()
  const [activeTab, setActiveTab] = useState<'refills' | 'history' | 'packages'>('refills')
  const [autoRefillEnabled, setAutoRefillEnabled] = useState(true)
  const [refillThreshold, setRefillThreshold] = useState(100)
  const [refillAmount, setRefillAmount] = useState(500)
  const [monthlyLimit, setMonthlyLimit] = useState(2000)
  const [selectedPackage, setSelectedPackage] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const currentBalance = 1250
  const monthlyUsage = 750
  const averageDailyUsage = 25

  const creditPackages: CreditPackage[] = [
    { id: 'starter', name: 'Starter', credits: 100, price: 10 },
    { id: 'basic', name: 'Basic', credits: 500, price: 45, savings: 5 },
    { id: 'pro', name: 'Professional', credits: 1000, price: 85, savings: 15, popular: true },
    { id: 'business', name: 'Business', credits: 2500, price: 200, savings: 50 },
    { id: 'enterprise', name: 'Enterprise', credits: 5000, price: 375, savings: 125 },
    { id: 'custom', name: 'Custom', credits: 10000, price: 700, savings: 300 },
  ]

  const transactions: CreditTransaction[] = [
    {
      id: 'tx_1',
      date: '2024-10-30',
      type: 'usage',
      description: 'Cat Breeds Dataset - 250 images',
      amount: -25,
      balance: 1250,
      status: 'completed',
    },
    {
      id: 'tx_2',
      date: '2024-10-29',
      type: 'purchase',
      description: 'Professional Package - 1000 credits',
      amount: 1000,
      balance: 1275,
      status: 'completed',
    },
    {
      id: 'tx_3',
      date: '2024-10-28',
      type: 'usage',
      description: 'Product Images - 150 images',
      amount: -15,
      balance: 275,
      status: 'completed',
    },
    {
      id: 'tx_4',
      date: '2024-10-27',
      type: 'bonus',
      description: 'Referral Bonus',
      amount: 50,
      balance: 290,
      status: 'completed',
    },
    {
      id: 'tx_5',
      date: '2024-10-26',
      type: 'usage',
      description: 'Nature Dataset - 400 images',
      amount: -40,
      balance: 240,
      status: 'completed',
    },
  ]

  const usageHistory = Array.from({ length: 30 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (29 - i))
    return {
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      credits: Math.floor(Math.random() * 50) + 10,
      cost: Math.floor(Math.random() * 5) + 1,
    }
  })

  const handlePurchaseCredits = async (packageId: string) => {
    setIsProcessing(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsProcessing(false)
    
    const pkg = creditPackages.find(p => p.id === packageId)
    toast({
      title: 'Credits purchased',
      description: `Successfully added ${pkg?.credits} credits to your account.`,
    })
  }

  const handleSaveRefillSettings = async () => {
    setIsProcessing(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsProcessing(false)
    
    toast({
      title: 'Settings saved',
      description: 'Your automatic refill settings have been updated.',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Credit Management</h1>
        <p className="text-muted-foreground">
          Manage your credits and automatic refills
        </p>
      </div>

      {/* Current Balance Card */}
      <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-2xl">Credit Balance</CardTitle>
              <CardDescription>
                Your current credit status
              </CardDescription>
            </div>
            <Wallet className="h-8 w-8 text-primary" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold">{currentBalance.toLocaleString()}</span>
              <span className="text-muted-foreground">credits</span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Monthly Usage</p>
                <p className="text-lg font-medium">{monthlyUsage} credits</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Daily Average</p>
                <p className="text-lg font-medium">{averageDailyUsage} credits</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Est. Days Remaining</p>
                <p className="text-lg font-medium">{Math.floor(currentBalance / averageDailyUsage)} days</p>
              </div>
            </div>

            <div className="flex gap-2">
              <Dialog>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Buy Credits
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-3xl">
                  <DialogHeader>
                    <DialogTitle>Purchase Credits</DialogTitle>
                    <DialogDescription>
                      Choose a credit package that suits your needs
                    </DialogDescription>
                  </DialogHeader>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 py-4">
                    {creditPackages.map((pkg) => (
                      <Card
                        key={pkg.id}
                        className={cn(
                          "relative cursor-pointer transition-all",
                          selectedPackage === pkg.id && "ring-2 ring-primary",
                          pkg.popular && "border-primary"
                        )}
                        onClick={() => setSelectedPackage(pkg.id)}
                      >
                        {pkg.popular && (
                          <Badge className="absolute -top-2 right-2">Popular</Badge>
                        )}
                        <CardHeader className="pb-3">
                          <CardTitle className="text-lg">{pkg.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div>
                              <span className="text-2xl font-bold">{pkg.credits.toLocaleString()}</span>
                              <span className="text-muted-foreground text-sm ml-1">credits</span>
                            </div>
                            <div className="flex items-baseline gap-2">
                              <span className="text-xl font-semibold">${pkg.price}</span>
                              {pkg.savings && (
                                <Badge variant="secondary" className="text-xs">
                                  Save ${pkg.savings}
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              ${(pkg.price / pkg.credits * 100).toFixed(2)} per 100 credits
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <DialogFooter>
                    <Button variant="outline">Cancel</Button>
                    <Button
                      onClick={() => selectedPackage && handlePurchaseCredits(selectedPackage)}
                      disabled={!selectedPackage || isProcessing}
                    >
                      {isProcessing ? (
                        <>
                          <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <ShoppingCart className="h-4 w-4 mr-2" />
                          Purchase
                        </>
                      )}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              
              <Button variant="outline">
                <History className="h-4 w-4 mr-2" />
                View History
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Automatic Refills */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Automatic Credit Refills</CardTitle>
              <CardDescription>
                Never run out of credits with automatic refills
              </CardDescription>
            </div>
            <RefreshCw className={cn(
              "h-5 w-5",
              autoRefillEnabled ? "text-primary animate-spin-slow" : "text-muted-foreground"
            )} />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Auto-Refill</Label>
              <p className="text-sm text-muted-foreground">
                Automatically purchase credits when balance is low
              </p>
            </div>
            <Switch
              checked={autoRefillEnabled}
              onCheckedChange={setAutoRefillEnabled}
            />
          </div>

          {autoRefillEnabled && (
            <>
              <Separator />
              
              <div className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="threshold">Refill when balance falls below</Label>
                    <span className="text-sm font-medium">{refillThreshold} credits</span>
                  </div>
                  <Slider
                    id="threshold"
                    min={50}
                    max={500}
                    step={50}
                    value={[refillThreshold]}
                    onValueChange={(value) => setRefillThreshold(value[0])}
                  />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="amount">Credits to purchase</Label>
                    <span className="text-sm font-medium">{refillAmount} credits</span>
                  </div>
                  <Slider
                    id="amount"
                    min={100}
                    max={2000}
                    step={100}
                    value={[refillAmount]}
                    onValueChange={(value) => setRefillAmount(value[0])}
                  />
                  <p className="text-xs text-muted-foreground">
                    Estimated cost: ${(refillAmount * 0.085).toFixed(2)}
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="limit">Monthly spending limit</Label>
                    <span className="text-sm font-medium">${monthlyLimit}</span>
                  </div>
                  <Slider
                    id="limit"
                    min={100}
                    max={5000}
                    step={100}
                    value={[monthlyLimit]}
                    onValueChange={(value) => setMonthlyLimit(value[0])}
                  />
                </div>

                <div className="p-3 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                  <div className="flex gap-2">
                    <Info className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium text-blue-900 dark:text-blue-100">
                        Auto-refill summary
                      </p>
                      <p className="text-blue-800 dark:text-blue-200">
                        When your balance drops below {refillThreshold} credits, we'll automatically add {refillAmount} credits to your account (up to ${monthlyLimit}/month).
                      </p>
                    </div>
                  </div>
                </div>

                <Button onClick={handleSaveRefillSettings} className="w-full">
                  <Save className="h-4 w-4 mr-2" />
                  Save Refill Settings
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Credit History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Credit History</CardTitle>
              <CardDescription>
                Recent credit transactions and usage
              </CardDescription>
            </div>
            <Select defaultValue="all">
              <SelectTrigger className="w-[150px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Transactions</SelectItem>
                <SelectItem value="purchases">Purchases</SelectItem>
                <SelectItem value="usage">Usage</SelectItem>
                <SelectItem value="refunds">Refunds</SelectItem>
                <SelectItem value="bonuses">Bonuses</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {transactions.map((transaction) => {
              const isCredit = transaction.amount > 0
              const Icon = 
                transaction.type === 'purchase' ? ShoppingCart :
                transaction.type === 'usage' ? Package :
                transaction.type === 'refund' ? RefreshCw :
                Gift
              
              return (
                <div key={transaction.id} className="flex items-center justify-between py-3 border-b last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "p-2 rounded-lg",
                      isCredit ? "bg-green-100 dark:bg-green-900/20" : "bg-gray-100 dark:bg-gray-900/20"
                    )}>
                      <Icon className={cn(
                        "h-4 w-4",
                        isCredit ? "text-green-600 dark:text-green-400" : "text-gray-600 dark:text-gray-400"
                      )} />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{transaction.description}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(transaction.date).toLocaleDateString()} at {new Date(transaction.date).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={cn(
                      "font-medium",
                      isCredit ? "text-green-600 dark:text-green-400" : "text-gray-900 dark:text-gray-100"
                    )}>
                      {isCredit ? '+' : ''}{Math.abs(transaction.amount)} credits
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Balance: {transaction.balance}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="mt-4 pt-4 border-t">
            <Button variant="outline" className="w-full">
              View Full History
              <ArrowDown className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Usage Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Credit Usage Trend</CardTitle>
          <CardDescription>
            Your credit consumption over the last 30 days
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={usageHistory}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="credits"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="Credits Used"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Special Offers */}
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20 border-purple-200 dark:border-purple-800">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Gift className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-purple-900 dark:text-purple-100">
                Limited time offer!
              </p>
              <p className="text-sm text-purple-800 dark:text-purple-200">
                Get 20% bonus credits on purchases over $100. Offer ends in 3 days.
              </p>
              <Button variant="link" className="h-auto p-0 text-purple-700 dark:text-purple-300">
                Claim offer →
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
