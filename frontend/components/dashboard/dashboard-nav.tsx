'use client'

import {UserMenu} from '@/components/auth/user-menu'
import {Activity, Database, FolderOpen, Home, Settings} from 'lucide-react'
import Link from 'next/link'
import {usePathname} from 'next/navigation'
import {cn} from '@/lib/utils'

const navigation = [
  {name: 'Dashboard', href: '/dashboard', icon: Home},
  {name: 'Projects', href: '/dashboard/projects', icon: FolderOpen},
  {name: 'Activity', href: '/dashboard/activity', icon: Activity},
  {name: 'Settings', href: '/dashboard/settings', icon: Settings},
]

export function DashboardNav() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link href="/dashboard" className="flex items-center gap-2 font-medium text-foreground">
              <div
                className="bg-gradient-to-br from-primary to-secondary text-primary-foreground flex size-8 items-center justify-center rounded-lg shadow-lg">
                <Database className="size-5"/>
              </div>
              <span className="text-xl font-bold">PixCrawler</span>
            </Link>

            <div className="hidden md:flex items-center space-x-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                    )}
                  >
                    <item.icon className="size-4"/>
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>

          <UserMenu/>
        </div>
      </div>
    </nav>
  )
}
