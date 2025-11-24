'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/components/ui/use-toast'
import {
  CreditCard,
  Calendar,
  CheckCircle,
  XCircle,
  AlertCircle,
  Info,
  TrendingUp,
  Zap,
  Crown,
  Shield,
  Rocket,
  Star,
  ArrowRight,
  Download,
  ChevronRight,
  Clock,
  Users,
  Package,
  Database,
  Cpu,
  Activity,
  BarChart3,
  FileText,
  Receipt,
  RefreshCw,
  Pause,
  Play,
  CreditCard as CardIcon,
} from 'lucide-react'

interface PlanFeature {
  name: string
  included: boolean
  value?: string
}

interface BillingHistory {
  id: string
  date: string
  description: string
  amount: number
  status: 'paid' | 'pending' | 'failed'
  invoice?: string
}

export function Subscription() {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [autoRenew, setAutoRenew] = useState(true)

  const currentPlan = {
    name: 'Professional',
    price: 49,
    interval: 'month',
    status: 'active',
    startDate: '2024-01-15',
    nextBillingDate: '2024-11-15',
    cancelAtPeriodEnd: false,
  }

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      price: 19,
      interval: 'month',
      description: 'Perfect for individuals and small projects',
      features: [
        { name: '1,000 images/month', included: true },
        { name: '5 concurrent crawl jobs', included: true },
        { name: 'Basic validation', included: true },
        { name: 'Standard support', included: true },
        { name: 'API access', included: false },
        { name: 'Custom models', included: false },
        { name: 'Priority processing', included: false },
        { name: 'Advanced analytics', included: false },
      ],
      recommended: false,
    },
    {
      id: 'professional',
      name: 'Professional',
      price: 49,
      interval: 'month',
      description: 'For professionals and growing teams',
      features: [
        { name: '10,000 images/month', included: true },
        { name: '20 concurrent crawl jobs', included: true },
        { name: 'Advanced validation', included: true },
        { name: 'Priority support', included: true },
        { name: 'API access', included: true },
        { name: 'Custom models', included: true },
        { name: 'Priority processing', included: true },
        { name: 'Advanced analytics', included: false },
      ],
      recommended: true,
      current: true,
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: 199,
      interval: 'month',
      description: 'For large teams and organizations',
      features: [
        { name: 'Unlimited images', included: true },
        { name: 'Unlimited crawl jobs', included: true },
        { name: 'AI-powered validation', included: true },
        { name: 'Dedicated support', included: true },
        { name: 'API access', included: true },
        { name: 'Custom models', included: true },
        { name: 'Priority processing', included: true },
        { name: 'Advanced analytics', included: true },
      ],
      recommended: false,
    },
  ]

  const billingHistory: BillingHistory[] = [
    {
      id: 'inv_001',
      date: '2024-10-15',
      description: 'Professional Plan - Monthly',
      amount: 49,
      status: 'paid',
      invoice: 'INV-2024-10-001',
    },
    {
      id: 'inv_002',
      date: '2024-09-15',
      description: 'Professional Plan - Monthly',
      amount: 49,
      status: 'paid',
      invoice: 'INV-2024-09-001',
    },
    {
      id: 'inv_003',
      date: '2024-08-15',
      description: 'Professional Plan - Monthly',
      amount: 49,
      status: 'paid',
      invoice: 'INV-2024-08-001',
    },
    {
      id: 'inv_004',
      date: '2024-07-15',
      description: 'Starter Plan - Monthly',
      amount: 19,
      status: 'paid',
      invoice: 'INV-2024-07-001',
    },
  ]

  const handleUpgrade = async (planId: string) => {
    setIsLoading(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsLoading(false)

    toast({
      title: 'Plan upgraded successfully',
      description: 'Your subscription has been updated.',
    })
  }

  const handleCancelSubscription = async () => {
    setIsLoading(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsLoading(false)

    toast({
      title: 'Subscription cancelled',
      description: 'Your subscription will remain active until the end of the billing period.',
    })
  }

  const handleReactivate = async () => {
    setIsLoading(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsLoading(false)

    toast({
      title: 'Subscription reactivated',
      description: 'Your subscription will continue to renew automatically.',
    })
  }

  const handleDownloadInvoice = (invoiceId: string) => {
    toast({
      title: 'Invoice downloaded',
      description: `Invoice ${invoiceId} has been downloaded.`,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Subscription</h1>
        <p className="text-muted-foreground">
          Manage your subscription plan and billing
        </p>
      </div>

      {/* Current Plan Overview */}
      <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Crown className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle className="text-2xl">{currentPlan.name} Plan</CardTitle>
                <CardDescription>
                  ${currentPlan.price}/{currentPlan.interval}
                </CardDescription>
              </div>
            </div>
            <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              <CheckCircle className="h-3 w-3 mr-1" />
              Active
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Started</p>
              <p className="font-medium">{new Date(currentPlan.startDate).toLocaleDateString()}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Next billing date</p>
              <p className="font-medium">{new Date(currentPlan.nextBillingDate).toLocaleDateString()}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Auto-renewal</p>
              <p className="font-medium">{autoRenew ? 'Enabled' : 'Disabled'}</p>
            </div>
          </div>

          <Separator />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="w-full">
              <CreditCard className="h-4 w-4 mr-2" />
              Update Payment Method
            </Button>
            <Button variant="outline" className="w-full">
              <Receipt className="h-4 w-4 mr-2" />
              View Invoices
            </Button>
            {currentPlan.cancelAtPeriodEnd ? (
              <Button variant="outline" className="w-full" onClick={handleReactivate}>
                <Play className="h-4 w-4 mr-2" />
                Reactivate Subscription
              </Button>
            ) : (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" className="w-full text-destructive hover:text-destructive hover:bg-destructive/10">
                    <Pause className="h-4 w-4 mr-2" />
                    Cancel Subscription
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Cancel Subscription?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Your subscription will remain active
                      until {new Date(currentPlan.nextBillingDate).toLocaleDateString()}.
                      You can reactivate anytime before then.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleCancelSubscription}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      Cancel Subscription
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Available Plans */}
      <Card>
        <CardHeader>
          <CardTitle>Explore Other Plans</CardTitle>
          <CardDescription>
            View all available plans and find the one that best fits your needs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            className="w-full"
            onClick={() => window.location.href = '/pricing'}
          >
            View All Plans
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </CardContent>
      </Card>

      {/* Payment Method */}
      <Card>
        <CardHeader>
          <CardTitle>Payment Method</CardTitle>
          <CardDescription>
            Manage your payment information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <CardIcon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">•••• •••• •••• 4242</p>
                <p className="text-sm text-muted-foreground">Expires 12/2025</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary">Default</Badge>
              <Button variant="outline" size="sm">
                Update
              </Button>
            </div>
          </div>

          <Button variant="outline" className="w-full">
            <CreditCard className="h-4 w-4 mr-2" />
            Add Payment Method
          </Button>
        </CardContent>
      </Card>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
          <CardDescription>
            View your past transactions and invoices
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {billingHistory.map((item) => (
              <div key={item.id} className="flex items-center justify-between py-3 border-b last:border-0">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "p-2 rounded-lg",
                    item.status === 'paid' && "bg-green-100 dark:bg-green-900/20",
                    item.status === 'pending' && "bg-yellow-100 dark:bg-yellow-900/20",
                    item.status === 'failed' && "bg-red-100 dark:bg-red-900/20"
                  )}>
                    <FileText className={cn(
                      "h-4 w-4",
                      item.status === 'paid' && "text-green-600 dark:text-green-400",
                      item.status === 'pending' && "text-yellow-600 dark:text-yellow-400",
                      item.status === 'failed' && "text-red-600 dark:text-red-400"
                    )} />
                  </div>
                  <div>
                    <p className="font-medium">{item.description}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(item.date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="font-medium">${item.amount}</p>
                    <Badge
                      variant={
                        item.status === 'paid' ? 'secondary' :
                          item.status === 'pending' ? 'outline' :
                            'destructive'
                      }
                      className="text-xs"
                    >
                      {item.status}
                    </Badge>
                  </div>
                  {item.invoice && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownloadInvoice(item.invoice!)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t">
            <Button variant="outline" className="w-full">
              View All Transactions
              <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Usage Alert */}
      <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Need more resources?
              </p>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                You're using 75% of your monthly image quota. Consider upgrading to the Enterprise plan for unlimited
                images.
              </p>
              <Button variant="link" className="h-auto p-0 text-blue-700 dark:text-blue-300">
                View usage details →
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
