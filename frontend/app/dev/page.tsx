'use client'

import {useEffect} from 'react'
import {Button} from '@/components/ui/button'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Badge} from '@/components/ui/badge'
import {Code, Database, Eye, Home, Lock, Palette, Settings, TestTube, Unlock, User, UserPlus, CreditCard, ExternalLink, Copy} from 'lucide-react'
import Link from 'next/link'
import {useSearchParams} from 'next/navigation'

interface PageInfo {
  path: string
  name: string
  description: string
  category: 'Public' | 'Auth' | 'Payment' | 'Dashboard' | 'Onboarding' | 'Demo' | 'Dev'
  requiresAuth: boolean
  oneTime?: boolean
  icon: React.ReactNode
}

const PAGES: PageInfo[] = [
  // Public Pages
  {
    path: '/',
    name: 'Landing Page',
    description: 'Main landing page with hero section',
    category: 'Public',
    requiresAuth: false,
    icon: <Home className="size-4"/>
  },
  {
    path: '/pricing',
    name: 'Pricing',
    description: 'Pricing plans and subscription options',
    category: 'Public',
    requiresAuth: false,
    icon: <Database className="size-4"/>
  },
  {
    path: '/pricing/plans',
    name: 'All Plans',
    description: 'Detailed pricing with credit packages',
    category: 'Public',
    requiresAuth: false,
    icon: <Database className="size-4"/>
  },
  {
    path: '/examples',
    name: 'Examples',
    description: 'Dataset examples and use cases',
    category: 'Public',
    requiresAuth: false,
    icon: <Eye className="size-4"/>
  },

  // Auth Pages
  {
    path: '/login',
    name: 'Login',
    description: 'User authentication login form',
    category: 'Auth',
    requiresAuth: false,
    icon: <Lock className="size-4"/>
  },
  {
    path: '/signup',
    name: 'Sign Up',
    description: 'User registration form',
    category: 'Auth',
    requiresAuth: false,
    icon: <UserPlus className="size-4"/>
  },
  {
    path: '/auth/forgot-password',
    name: 'Forgot Password',
    description: 'Password reset request form',
    category: 'Auth',
    requiresAuth: false,
    icon: <Unlock className="size-4"/>
  },
  {
    path: '/auth/reset-password',
    name: 'Reset Password',
    description: 'Password reset form with token',
    category: 'Auth',
    requiresAuth: false,
    icon: <Unlock className="size-4"/>
  },
  {
    path: '/auth/auth-code-error',
    name: 'Auth Code Error',
    description: 'Authentication error page',
    category: 'Auth',
    requiresAuth: false,
    icon: <Lock className="size-4"/>
  },

  // Payment Pages
  {
    path: '/payment/success',
    name: 'Payment Success',
    description: 'Payment confirmation and success page',
    category: 'Payment',
    requiresAuth: false,
    icon: <CreditCard className="size-4"/>
  },
  {
    path: '/payment/cancelled',
    name: 'Payment Cancelled',
    description: 'Payment cancellation page',
    category: 'Payment',
    requiresAuth: false,
    icon: <CreditCard className="size-4"/>
  },

  // Onboarding Pages
  {
    path: '/welcome',
    name: 'Welcome Flow',
    description: 'One-time onboarding experience',
    category: 'Onboarding',
    requiresAuth: true,
    oneTime: true,
    icon: <User className="size-4"/>
  },

  // Dashboard Pages
  {
    path: '/dashboard',
    name: 'Dashboard Home',
    description: 'Main dashboard overview',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Database className="size-4"/>
  },
  {
    path: '/dashboard/projects',
    name: 'Projects',
    description: 'Project management interface',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Database className="size-4"/>
  },
  {
    path: '/dashboard/projects/new',
    name: 'New Project',
    description: 'Create new project form',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Database className="size-4"/>
  },
  {
    path: '/dashboard/datasets',
    name: 'Datasets List',
    description: 'Dataset management and listing',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Database className="size-4"/>
  },
  {
    path: '/dashboard/datasets/cats_dogs_001',
    name: 'Dataset Dashboard',
    description: 'Complete dataset dashboard with overview, gallery, files',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Database className="size-4"/>
  },
  {
    path: '/dashboard/datasets/new',
    name: 'New Dataset',
    description: 'Create new dataset form',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Database className="size-4"/>
  },
  {
    path: '/dashboard/profile',
    name: 'Profile',
    description: 'User profile and account settings',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <User className="size-4"/>
  },
  {
    path: '/dashboard/billing',
    name: 'Billing',
    description: 'Subscription and billing management',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Database className="size-4"/>
  },
  {
    path: '/dashboard/settings',
    name: 'Settings',
    description: 'Application settings and preferences',
    category: 'Dashboard',
    requiresAuth: true,
    icon: <Settings className="size-4"/>
  },

  // Demo Pages
  {
    path: '/demo',
    name: 'Demo',
    description: 'Product demonstration',
    category: 'Demo',
    requiresAuth: false,
    icon: <TestTube className="size-4"/>
  },
  {
    path: '/demo/buttons',
    name: 'Button Demo',
    description: 'UI component demonstrations',
    category: 'Demo',
    requiresAuth: false,
    icon: <Palette className="size-4"/>
  },

  // Dev Pages
  {
    path: '/dev',
    name: 'Dev Navigator',
    description: 'This development page navigator',
    category: 'Dev',
    requiresAuth: false,
    icon: <Code className="size-4"/>
  }
]

const CATEGORY_COLORS = {
  'Public': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  'Auth': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  'Payment': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300',
  'Dashboard': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  'Onboarding': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
  'Demo': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  'Dev': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
}

export default function DevPage() {
  const searchParams = useSearchParams()
  const requestedPage = searchParams.get('page')

  // If a specific page is requested, redirect to it with dev bypass
  useEffect(() => {
    if (requestedPage) {
      let targetPath = requestedPage

      // Handle special cases
      if (requestedPage === 'home') {
        targetPath = ''
      } else {
        // Decode the path
        targetPath = decodeURIComponent(requestedPage)
      }

      const targetUrl = `/${targetPath}?dev_bypass=true`
      window.location.href = targetUrl
    }
  }, [requestedPage])

  const getDevUrl = (page: PageInfo) => {
    // Handle root path
    if (page.path === '/') {
      return `/dev?page=home`
    }
    // Remove leading slash and encode the path
    const pageName = encodeURIComponent(page.path.substring(1))
    return `/dev?page=${pageName}`
  }

  const groupedPages = PAGES.reduce((acc, page) => {
    if (!acc[page.category]) {
      acc[page.category] = []
    }
    acc[page.category].push(page)
    return acc
  }, {} as Record<string, PageInfo[]>)

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Code className="size-8 text-primary"/>
        <div>
          <h1 className="text-3xl font-bold">Development Page Navigator</h1>
          <p className="text-muted-foreground">
            Access all pages in development mode, bypass auth and one-time restrictions
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(groupedPages).map(([category, pages]) => (
          <Card key={category}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Badge className={CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS]} variant="secondary">
                  {category}
                </Badge>
              </div>
              <div className="text-2xl font-bold mt-2">{pages.length}</div>
              <p className="text-sm text-muted-foreground">pages</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Access */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="size-5"/>
            Quick Access
          </CardTitle>
          <CardDescription>
            Jump to the most commonly used pages during development
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button asChild variant="outline" className="h-auto p-4 flex-col gap-2">
              <Link href="/dashboard/datasets/cats_dogs_001">
                <Database className="size-5"/>
                <span className="text-sm">Dataset Dashboard</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto p-4 flex-col gap-2">
              <Link href="/pricing">
                <CreditCard className="size-5"/>
                <span className="text-sm">Pricing</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto p-4 flex-col gap-2">
              <Link href="/welcome">
                <User className="size-5"/>
                <span className="text-sm">Welcome Flow</span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="h-auto p-4 flex-col gap-2">
              <Link href="/dashboard">
                <Home className="size-5"/>
                <span className="text-sm">Dashboard</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="size-5"/>
            How to Use
          </CardTitle>
          <CardDescription>
            Click any page below to view it in development mode with auth bypass
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <strong>Direct Access:</strong> Click any page below to view it immediately, bypassing auth and one-time
            restrictions.
          </div>
          <div>
            <strong>URL Format:</strong> <code className="bg-muted px-1 rounded">localhost:3000/dev?page=welcome</code>
          </div>
          <div>
            <strong>New Features:</strong>
            <ul className="list-disc list-inside ml-4 mt-1 space-y-1">
              <li><strong>Copy URL:</strong> Click the copy icon to copy the direct page URL</li>
              <li><strong>Open in New Tab:</strong> Click the external link icon to open in a new tab</li>
              <li><strong>Quick Access:</strong> Use the buttons above for commonly used pages</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Page Categories */}
      {Object.entries(groupedPages).map(([category, pages]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Badge className={CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS]}>
                {category}
              </Badge>
              <span>{category} Pages</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-1 lg:grid-cols-2">
              {pages.map((page) => (
                <div
                  key={page.path}
                  className="border rounded-lg hover:bg-accent/50 transition-colors overflow-hidden"
                >
                  <div className="flex items-center gap-3 p-3">
                    <div className="flex-shrink-0">
                      {page.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium truncate">{page.name}</h3>
                        {page.requiresAuth && (
                          <Lock className="size-3 text-muted-foreground"/>
                        )}
                        {page.oneTime && (
                          <Badge variant="outline" className="text-xs">
                            One-time
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {page.description}
                      </p>
                    </div>
                  </div>
                  
                  {/* Action buttons in a separate row */}
                  <div className="flex items-center justify-end gap-1 px-3 pb-3 pt-0">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        navigator.clipboard.writeText(`${window.location.origin}${page.path}`)
                      }}
                      title="Copy URL"
                      className="h-8 w-8 p-0"
                    >
                      <Copy className="size-4"/>
                    </Button>
                    <Button asChild size="sm" variant="ghost" className="h-8 w-8 p-0">
                      <Link
                        href={getDevUrl(page)}
                        title="View Page"
                      >
                        <Eye className="size-4"/>
                      </Link>
                    </Button>
                    <Button asChild size="sm" variant="outline" className="h-8 w-8 p-0">
                      <Link
                        href={page.path}
                        target="_blank"
                        title="Open in New Tab"
                      >
                        <ExternalLink className="size-4"/>
                      </Link>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}


    </div>
  )
}
