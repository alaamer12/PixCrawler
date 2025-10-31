'use client'

import React, {useState} from 'react'
import {Button} from '@/components/ui/button'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Badge} from '@/components/ui/badge'
import {Progress} from '@/components/ui/progress'
import {Input} from '@/components/ui/input'
import {Label} from '@/components/ui/label'
import {Switch} from '@/components/ui/switch'
import {Separator} from '@/components/ui/separator'
import {useToast} from '@/components/ui/use-toast'
import {
  Sparkles,
  Rocket,
  Share2,
  Gift,
  Users,
  Copy,
  ExternalLink,
  CheckCircle,
  Clock,
  TrendingUp,
  DollarSign,
  Star,
  Trophy,
  Target,
  Zap,
  Package,
  Globe,
  Lock,
  Unlock,
  ChevronRight,
  Info,
  Download,
  Upload,
  Calendar,
  Activity,
  BarChart3,
} from 'lucide-react'

// Referrals Section
export function Referrals() {
  const {toast} = useToast()
  const [referralCode] = useState('PIXCRAWL2024')

  const stats = {
    totalReferrals: 5,
    pendingRewards: 50,
    earnedRewards: 150,
    conversionRate: 40,
  }

  const referrals = [
    {email: 'alice@example.com', status: 'active', reward: 50, date: '2024-10-15'},
    {email: 'bob@example.com', status: 'pending', reward: 0, date: '2024-10-28'},
    {email: 'charlie@example.com', status: 'active', reward: 50, date: '2024-10-10'},
  ]

  const handleCopyCode = () => {
    navigator.clipboard.writeText(referralCode)
    toast({
      title: 'Referral code copied',
      description: 'Share this code with your friends!',
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Referrals</h1>
        <p className="text-muted-foreground">Invite friends and earn rewards</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Total Referrals</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.totalReferrals}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Pending Rewards</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">${stats.pendingRewards}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Earned Rewards</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">${stats.earnedRewards}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Conversion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.conversionRate}%</p>
          </CardContent>
        </Card>
      </div>

      {/* Referral Code */}
      <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
        <CardHeader>
          <CardTitle>Your Referral Code</CardTitle>
          <CardDescription>Share this code with friends to earn rewards</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <div className="flex-1 p-4 bg-background rounded-lg border font-mono text-lg text-center">
              {referralCode}
            </div>
            <Button onClick={handleCopyCode}>
              <Copy className="h-4 w-4 mr-2"/>
              Copy Code
            </Button>
          </div>
          <div className="mt-4 p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
            <p className="text-sm text-green-800 dark:text-green-200">
              <Gift className="h-4 w-4 inline mr-2"/>
              You and your friend each get <strong>$50 in credits</strong> when they sign up and make their first
              purchase!
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Referral List */}
      <Card>
        <CardHeader>
          <CardTitle>Your Referrals</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {referrals.map((referral, index) => (
              <div key={index} className="flex items-center justify-between py-3 border-b last:border-0">
                <div className="space-y-1">
                  <p className="font-medium">{referral.email}</p>
                  <p className="text-sm text-muted-foreground">Referred on {referral.date}</p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={referral.status === 'active' ? 'secondary' : 'outline'}>
                    {referral.status}
                  </Badge>
                  {referral.reward > 0 && (
                    <span className="text-green-600 dark:text-green-400 font-medium">
                      +${referral.reward}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
