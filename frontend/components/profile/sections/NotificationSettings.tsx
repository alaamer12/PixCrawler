'use client'

import React, {useState} from 'react'
import {Button} from '@/components/ui/button'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Label} from '@/components/ui/label'
import {Switch} from '@/components/ui/switch'
import {Separator} from '@/components/ui/separator'
import {Badge} from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {useToast} from '@/components/ui/use-toast'
import {
  Bell,
  Mail,
  Smartphone,
  Globe,
  Shield,
  Zap,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  Clock,
  Calendar,
  TrendingUp,
  Package,
  CreditCard,
  Users,
  FileText,
  Download,
  Upload,
  Rocket,
  Bug,
  Heart,
  Star,
  Save,
} from 'lucide-react'

interface NotificationChannel {
  id: string
  name: string
  icon: React.ElementType
  enabled: boolean
  verified: boolean
  description: string
}

interface NotificationCategory {
  id: string
  name: string
  description: string
  icon: React.ElementType
  email: boolean
  push: boolean
  sms: boolean
  inApp: boolean
}

export function NotificationSettings() {
  const {toast} = useToast()
  const [isSaving, setIsSaving] = useState(false)
  const [emailFrequency, setEmailFrequency] = useState('instant')
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(true)
  const [quietHoursStart, setQuietHoursStart] = useState('22:00')
  const [quietHoursEnd, setQuietHoursEnd] = useState('08:00')

  const [channels, setChannels] = useState<NotificationChannel[]>([
    {
      id: 'email',
      name: 'Email',
      icon: Mail,
      enabled: true,
      verified: true,
      description: 'john.doe@example.com',
    },
    {
      id: 'sms',
      name: 'SMS',
      icon: Smartphone,
      enabled: false,
      verified: false,
      description: '+1 (555) 123-4567',
    },
  ])

  const [categories, setCategories] = useState<NotificationCategory[]>([
    {
      id: 'crawl-jobs',
      name: 'Crawl Jobs',
      description: 'Updates about your image crawling tasks',
      icon: Download,
      email: true,
      push: true,
      sms: false,
      inApp: true,
    },
    {
      id: 'billing',
      name: 'Billing & Payments',
      description: 'Invoices, payment confirmations, and subscription changes',
      icon: CreditCard,
      email: true,
      push: false,
      sms: true,
      inApp: true,
    },
    {
      id: 'security',
      name: 'Security Alerts',
      description: 'Login attempts, password changes, and security updates',
      icon: Shield,
      email: true,
      push: true,
      sms: true,
      inApp: true,
    },
    {
      id: 'product',
      name: 'Product Updates',
      description: 'New features, improvements, and announcements',
      icon: Rocket,
      email: true,
      push: false,
      sms: false,
      inApp: true,
    },
    {
      id: 'datasets',
      name: 'Dataset Activity',
      description: 'Downloads, shares, and dataset status changes',
      icon: Package,
      email: true,
      push: true,
      sms: false,
      inApp: true,
    },
  ])

  const handleChannelToggle = (channelId: string) => {
    setChannels(prev =>
      prev.map(channel =>
        channel.id === channelId
          ? {...channel, enabled: !channel.enabled}
          : channel
      )
    )
  }

  const handleCategoryToggle = (categoryId: string, channelType: keyof NotificationCategory) => {
    if (channelType === 'id' || channelType === 'name' || channelType === 'description' || channelType === 'icon') return

    setCategories(prev =>
      prev.map(category =>
        category.id === categoryId
          ? {...category, [channelType]: !category[channelType]}
          : category
      )
    )
  }

  const handleSave = async () => {
    setIsSaving(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsSaving(false)

    toast({
      title: 'Notification preferences saved',
      description: 'Your notification settings have been updated successfully.',
    })
  }

  const handleTestNotification = (channelId: string) => {
    toast({
      title: 'Test notification sent',
      description: `A test notification has been sent to your ${channelId} channel.`,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Notification Settings</h1>
          <p className="text-muted-foreground">
            Configure how and when you receive notifications
          </p>
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? (
            <>
              <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent"/>
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2"/>
              Save Changes
            </>
          )}
        </Button>
      </div>

      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Channels</CardTitle>
          <CardDescription>
            Choose how you want to receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {channels.map((channel) => {
            const Icon = channel.icon
            return (
              <div
                key={channel.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className={`p-2 rounded-lg ${channel.enabled ? 'bg-primary/10' : 'bg-muted'}`}>
                    <Icon className={`h-5 w-5 ${channel.enabled ? 'text-primary' : 'text-muted-foreground'}`}/>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{channel.name}</p>
                      {channel.verified ? (
                        <Badge variant="secondary" className="text-xs">
                          <CheckCircle className="h-3 w-3 mr-1"/>
                          Verified
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs">
                          <AlertCircle className="h-3 w-3 mr-1"/>
                          Not Verified
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{channel.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {channel.enabled && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleTestNotification(channel.id)}
                    >
                      Test
                    </Button>
                  )}
                  <Switch
                    checked={channel.enabled}
                    onCheckedChange={() => handleChannelToggle(channel.id)}
                    disabled={!channel.verified}
                  />
                </div>
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* Notification Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Notification Categories</CardTitle>
          <CardDescription>
            Customize notifications for different types of activities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Table Header */}
            <div className="grid grid-cols-5 gap-4 pb-4 border-b">
              <div className="col-span-2">
                <p className="text-sm font-medium">Category</p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium">Email</p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium">Push</p>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium">In-App</p>
              </div>
            </div>

            {/* Categories */}
            {categories.map((category) => {
              const Icon = category.icon
              return (
                <div key={category.id} className="grid grid-cols-5 gap-4 items-center">
                  <div className="col-span-2 flex items-start gap-3">
                    <Icon className="h-5 w-5 text-muted-foreground mt-0.5"/>
                    <div>
                      <p className="font-medium text-sm">{category.name}</p>
                      <p className="text-xs text-muted-foreground">{category.description}</p>
                    </div>
                  </div>
                  <div className="text-center">
                    <Switch
                      checked={category.email}
                      onCheckedChange={() => handleCategoryToggle(category.id, 'email')}
                    />
                  </div>
                  <div className="text-center">
                    <Switch
                      checked={category.push}
                      onCheckedChange={() => handleCategoryToggle(category.id, 'push')}
                    />
                  </div>
                  <div className="text-center">
                    <Switch
                      checked={category.inApp}
                      onCheckedChange={() => handleCategoryToggle(category.id, 'inApp')}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>


      {/* Recent Notifications */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Notifications</CardTitle>
          <CardDescription>
            View your recent notification history
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                icon: CheckCircle,
                title: 'Crawl job completed',
                description: 'Your "Cat Breeds" dataset is ready',
                time: '2 hours ago',
                type: 'success',
              },
              {
                icon: CreditCard,
                title: 'Payment received',
                description: 'Your subscription has been renewed',
                time: '1 day ago',
                type: 'info',
              },
              {
                icon: AlertCircle,
                title: 'Storage limit warning',
                description: 'You have used 80% of your storage',
                time: '3 days ago',
                type: 'warning',
              },
              {
                icon: Rocket,
                title: 'New feature available',
                description: 'Try our new AI-powered keyword expansion',
                time: '1 week ago',
                type: 'info',
              },
            ].map((notification, index) => {
              const Icon = notification.icon
              return (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent/20 cursor-pointer transition-colors"
                  onClick={() => window.location.href = '/notifications'}
                >
                  <div className={cn(
                    "p-2 rounded-lg",
                    notification.type === 'success' && "bg-green-100 dark:bg-green-900/20",
                    notification.type === 'warning' && "bg-yellow-100 dark:bg-yellow-900/20",
                    notification.type === 'info' && "bg-blue-100 dark:bg-blue-900/20"
                  )}>
                    <Icon className={cn(
                      "h-4 w-4",
                      notification.type === 'success' && "text-green-600 dark:text-green-400",
                      notification.type === 'warning' && "text-yellow-600 dark:text-yellow-400",
                      notification.type === 'info' && "text-blue-600 dark:text-blue-400"
                    )}/>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-sm">{notification.title}</p>
                    <p className="text-sm text-muted-foreground">{notification.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      <Clock className="h-3 w-3 inline mr-1"/>
                      {notification.time}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
