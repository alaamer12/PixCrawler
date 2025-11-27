'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  User,
  Bell,
  Settings,
  CreditCard,
  BarChart3,
  Key,
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
import { useAuth } from '@/lib/auth/hooks'
import { AuthUser } from '@supabase/supabase-js'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export interface ProfileSection {
  id: string
  label: string
  icon: React.ElementType
  description?: string
  badge?: string | number
  showArrow?: boolean
  group?: string
  keywords?: string[]
}

const profileSections: ProfileSection[] = [
  // Personal Settings
  {
    id: 'account',
    label: 'Account Profile',
    icon: User,
    description: 'Personal information',
    group: 'Personal',
    keywords: ['name', 'email', 'phone', 'avatar', 'picture', 'bio', 'last name', 'first name'],
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: Bell,
    description: 'Notification preferences',
    badge: 3,
    group: 'Personal',
    keywords: ['email notifications', 'push', 'alerts', 'messages'],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    description: 'Application preferences',
    group: 'Personal',
    keywords: ['theme', 'dark mode', 'language', 'region'],
  },

  // Billing & Usage
  {
    id: 'subscription',
    label: 'Subscription',
    icon: CreditCard,
    description: 'Manage your plan',
    showArrow: true,
    group: 'Billing',
    keywords: ['plan', 'payment', 'credit card', 'invoice', 'billing'],
  },
  {
    id: 'usage',
    label: 'Usage',
    icon: BarChart3,
    description: 'Resource consumption',
    group: 'Billing',
    keywords: ['credits', 'api calls', 'storage', 'limits'],
  },

  // Developer
  {
    id: 'api-keys',
    label: 'API Keys',
    icon: Key,
    description: 'Access tokens',
    badge: 2,
    group: 'Developer',
    keywords: ['token', 'secret', 'authentication', 'oauth'],
  },
]

interface ProfileLayoutProps {
  children: React.ReactNode
  activeSection: string
  onSectionChange: (section: string) => void
}


function UserLogo({ user }: { user: any }) {
  return (
    <div className="flex items-center gap-3">
      <Avatar className="h-9 w-9">
        <AvatarImage src={user?.profile?.avatarUrl || ''} alt={user?.profile?.fullName || ''} />
        <AvatarFallback>
          {user?.profile?.fullName?.charAt(0) || user?.email?.charAt(0) || 'U'}
        </AvatarFallback>
      </Avatar>
      <div className="flex flex-col">
        <p className="text-sm font-medium leading-none">{user?.profile?.fullName || user?.email?.split('@')[0] || 'User'}</p>
        <p className="text-xs text-muted-foreground">{user?.email}</p>
      </div>
    </div>
  )
}

const HighlightText = ({ text, query }: { text: string; query: string }) => {
  if (!query) return <>{text}</>
  const parts = text.split(new RegExp(`(${query})`, 'gi'))
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <span key={i} className="bg-yellow-500/30 text-foreground rounded-sm px-0.5">{part}</span>
        ) : (
          part
        )
      )}
    </>
  )
}

export function ProfileLayout({ children, activeSection, onSectionChange }: ProfileLayoutProps) {
  const router = useRouter()
  const { user, signOut } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const handleLogout = async () => {
    await signOut()
    router.push('/login')
  }

  const filteredSections = profileSections.filter(section =>
    section.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
    section.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    section.keywords?.some(k => k.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <div className="min-h-screen bg-black md:bg-background">

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
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            {/* User Logo */}
            <UserLogo user={user} />

          </div>

          {/* Center Navigation */}
          <nav className="hidden lg:flex items-center gap-6 mx-auto">
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard')}>
              <Home className="h-4 w-4 mr-2" />
              Dashboard
            </Button>
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/projects')}>
              <FolderOpen className="h-4 w-4 mr-2" />
              Projects
            </Button>
            <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/datasets')}>
              <Database className="h-4 w-4 mr-2" />
              Datasets
            </Button>
            <Button variant="ghost" size="sm" onClick={() => router.push('/docs')}>
              <HelpCircle className="h-4 w-4 mr-2" />
              Help
            </Button>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="hidden md:flex items-center">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
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
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-9 w-9 relative">
                  <Bell className="h-4 w-4" />
                  <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80">
                <DropdownMenuLabel>Notifications</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <div className="max-h-[300px] overflow-y-auto">
                  {[
                    {
                      id: 1,
                      title: 'New Feature Available',
                      description: 'Try out our new Image Validation tool',
                      time: '2 hours ago',
                      unread: true,
                    },
                    {
                      id: 2,
                      title: 'Crawl Job Completed',
                      description: 'Job #1234 finished with 500 images',
                      time: '5 hours ago',
                      unread: true,
                    },
                    {
                      id: 3,
                      title: 'Payment Successful',
                      description: 'Your monthly subscription has been renewed',
                      time: '1 day ago',
                      unread: false,
                    },
                  ].map((notification) => (
                    <DropdownMenuItem key={notification.id} className="flex flex-col items-start gap-1 p-3 cursor-pointer">
                      <div className="flex items-center justify-between w-full">
                        <span className="font-medium text-sm">{notification.title}</span>
                        <span className="text-xs text-muted-foreground">{notification.time}</span>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {notification.description}
                      </p>
                    </DropdownMenuItem>
                  ))}
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="w-full text-center block p-2 font-medium text-primary cursor-pointer"
                  onClick={() => router.push('/dashboard/notifications')}
                >
                  View all notifications
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>


          </div>
        </div>
      </header>

      <div className="flex min-h-[calc(100vh-4rem)]">
        {/* Left Sidebar */}
        <aside
          className={cn(
            "w-64 border-r bg-card/50 backdrop-blur-sm transition-all duration-300",
            "lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)]",
            mobileMenuOpen ? "fixed inset-y-16 left-0 z-40 translate-x-0" : "fixed -translate-x-full lg:translate-x-0"
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
                              )} />
                              <div className="text-left min-w-0 flex-1">
                                <div className={cn(
                                  "text-sm truncate",
                                  isActive ? "font-semibold" : "font-medium"
                                )}>
                                  <HighlightText text={section.label} query={searchQuery} />
                                </div>
                                {section.description && (
                                  <div className="text-xs text-muted-foreground mt-0.5 truncate hidden xl:block">
                                    <HighlightText text={section.description} query={searchQuery} />
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
                                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
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
                <LogOut className="h-4 w-4" />
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
        <main className="flex-1">
          <div className="container max-w-6xl mx-auto p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
