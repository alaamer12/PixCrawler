'use client'

import React, {useState} from 'react'
import {useRouter} from 'next/navigation'
import {cn} from '@/lib/utils'
import {Button} from '@/components/ui/button'
import {ScrollArea} from '@/components/ui/scroll-area'
import {Avatar, AvatarFallback, AvatarImage} from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  User,
  Bell,
  Settings,
  CreditCard,
  BarChart3,
  RefreshCw,
  Calendar,
  History,
  Cloud,
  Key,
  Sparkles,
  Rocket,
  Share2,
  Gift,
  LogOut,
  ChevronRight,
  Menu,
  X,
  Home,
  Search,
  HelpCircle,
  FolderOpen,
  Database,
} from 'lucide-react'
import {useAuth} from '@/lib/auth/hooks'

export interface ProfileSection {
  id: string
  label: string
  icon: React.ElementType
  description?: string
  badge?: string | number
  showArrow?: boolean
  group?: string
}

const profileSections: ProfileSection[] = [
  // Personal Settings
  {
    id: 'account',
    label: 'Account Profile',
    icon: User,
    description: 'Personal information',
    group: 'Personal',
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: Bell,
    description: 'Notification preferences',
    badge: 3,
    group: 'Personal',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    description: 'Application preferences',
    group: 'Personal',
  },

  // Billing & Usage
  {
    id: 'subscription',
    label: 'Subscription',
    icon: CreditCard,
    description: 'Manage your plan',
    showArrow: true,
    group: 'Billing',
  },
  {
    id: 'usage',
    label: 'Usage',
    icon: BarChart3,
    description: 'Resource consumption',
    group: 'Billing',
  },

  // Developer
  {
    id: 'api-keys',
    label: 'API Keys',
    icon: Key,
    description: 'Access tokens',
    badge: 2,
    group: 'Developer',
  },

  // Commented out for future use
  // {
  //   id: 'auto-refills',
  //   label: 'Automatic Credit Refills',
  //   icon: RefreshCw,
  //   description: 'Set up automatic credit purchases',
  //   group: 'Billing',
  // },
  // {
  //   id: 'manage-plan',
  //   label: 'Manage Plan',
  //   icon: Calendar,
  //   description: 'Change or upgrade your plan',
  //   showArrow: true,
  //   group: 'Billing',
  // },
  // {
  //   id: 'credit-history',
  //   label: 'Credit History',
  //   icon: History,
  //   description: 'View transaction history',
  //   group: 'Billing',
  // },
  // {
  //   id: 'referrals',
  //   label: 'Referrals',
  //   icon: Gift,
  //   description: 'Invite friends and earn rewards',
  //   badge: '$50',
  //   group: 'Rewards',
  // },
]

interface ProfileLayoutProps {
  children: React.ReactNode
  activeSection: string
  onSectionChange: (section: string) => void
}

export function ProfileLayout({children, activeSection, onSectionChange}: ProfileLayoutProps) {
  const router = useRouter()
  const {user, signOut} = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const handleLogout = async () => {
    await signOut()
    router.push('/login')
  }

  const filteredSections = profileSections.filter(section =>
    section.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
    section.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navbar */}
      <header
        className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center px-4">
          {/* Logo and Brand */}
          <div className="flex items-center gap-6">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 hover:bg-accent rounded-lg transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5"/> : <Menu className="h-5 w-5"/>}
            </button>

            <a href="/dashboard" className="flex items-center gap-2 font-semibold">
              <div
                className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center">
                <span className="text-primary-foreground text-sm font-bold">P</span>
              </div>
              <span className="hidden sm:inline-block">PixCrawler</span>
            </a>
          </div>

          {/* Center Navigation */}
          <nav className="hidden lg:flex items-center gap-6 mx-auto">
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
              <Home className="h-4 w-4 mr-2"/>
              Dashboard
            </Button>
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/projects')}>
              <FolderOpen className="h-4 w-4 mr-2"/>
              Projects
            </Button>
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/datasets')}>
              <Database className="h-4 w-4 mr-2"/>
              Datasets
            </Button>
            <Button variant="ghost" size="sm" onClick={() => router.push('/docs')}>
              <HelpCircle className="h-4 w-4 mr-2"/>
              Help
            </Button>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="hidden md:flex items-center">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"/>
                <input
                  type="text"
                  placeholder="Search..."
                  className="h-9 w-[300px] rounded-md border bg-background pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            {/* Notifications */}
            <Button variant="ghost" size="icon" className="h-9 w-9 relative">
              <Bell className="h-4 w-4"/>
              <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive"/>
            </Button>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                  <Avatar className="h-9 w-9">
                    <AvatarImage src={user?.profile?.avatarUrl || ''} alt={user?.profile?.fullName || ''}/>
                    <AvatarFallback>
                      {user?.profile?.fullName?.charAt(0) || user?.email?.charAt(0) || 'U'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user?.profile?.fullName || 'User'}</p>
                    <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator/>
                <DropdownMenuItem onClick={() => onSectionChange('account')}>
                  <User className="mr-2 h-4 w-4"/>
                  <span>Profile</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onSectionChange('subscription')}>
                  <CreditCard className="mr-2 h-4 w-4"/>
                  <span>Billing</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onSectionChange('settings')}>
                  <Settings className="mr-2 h-4 w-4"/>
                  <span>Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator/>
                <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                  <LogOut className="mr-2 h-4 w-4"/>
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-4rem)]">
        {/* Left Sidebar */}
        <aside
          className={cn(
            "w-64 border-r bg-card/50 backdrop-blur-sm transition-all duration-300",
            "lg:relative lg:translate-x-0",
            mobileMenuOpen ? "fixed inset-y-16 left-0 z-40 translate-x-0" : "fixed -translate-x-full"
          )}
        >
          <div className="h-full flex flex-col">
            {/* Scrollable Menu Items */}
            <ScrollArea className="flex-1 py-6">
              <div className="px-3 space-y-6">
                {/* Group sections by category */}
                {['Personal', 'Billing', 'Developer'].map((groupName) => {
                  const groupSections = filteredSections.filter(s => s.group === groupName)
                  if (groupSections.length === 0) return null

                  return (
                    <div key={groupName} className="space-y-1">
                      {/* Group Label */}
                      <div className="px-3 mb-2">
                        <h3 className="text-xs font-semibold text-muted-foreground/70 uppercase tracking-wider">
                          {groupName}
                        </h3>
                      </div>

                      {/* Group Items */}
                      {groupSections.map((section) => {
                        const Icon = section.icon
                        const isActive = activeSection === section.id

                        return (
                          <button
                            key={section.id}
                            onClick={() => {
                              onSectionChange(section.id)
                              setMobileMenuOpen(false)
                            }}
                            className={cn(
                              "w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-200",
                              "hover:bg-accent/20 hover:text-accent-foreground",
                              "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                              isActive
                                ? "bg-primary/10 text-primary shadow-sm"
                                : "text-foreground/80"
                            )}
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <Icon className={cn(
                                "h-4 w-4 flex-shrink-0",
                                isActive ? "text-primary" : "text-muted-foreground"
                              )}/>
                              <div className="text-left min-w-0 flex-1">
                                <div className={cn(
                                  "text-sm truncate",
                                  isActive ? "font-semibold" : "font-medium"
                                )}>
                                  {section.label}
                                </div>
                                {section.description && (
                                  <div className="text-xs text-muted-foreground mt-0.5 truncate hidden xl:block">
                                    {section.description}
                                  </div>
                                )}
                              </div>
                            </div>

                            <div className="flex items-center gap-2 flex-shrink-0">
                              {section.badge && (
                                <span className={cn(
                                  "px-1.5 py-0.5 text-xs rounded-full font-semibold min-w-[20px] text-center",
                                  typeof section.badge === 'string' && section.badge.startsWith('$')
                                    ? "bg-green-500/10 text-green-600 dark:text-green-400"
                                    : typeof section.badge === 'string'
                                      ? "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                                      : "bg-red-500/10 text-red-600 dark:text-red-400"
                                )}>
                                  {section.badge}
                                </span>
                              )}
                              {section.showArrow && (
                                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground"/>
                              )}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  )
                })}
              </div>
            </ScrollArea>

            {/* Logout Button - Fixed at Bottom */}
            <div className="border-t p-3 bg-card/50 backdrop-blur-sm">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-destructive hover:bg-destructive/10 transition-all duration-200 font-medium"
              >
                <LogOut className="h-4 w-4"/>
                <span>Log out</span>
              </button>
            </div>
          </div>
        </aside>

        {/* Mobile Overlay */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-30 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto">
          <div className="container max-w-6xl mx-auto p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
