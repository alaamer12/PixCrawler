'use client'

import {useAuth} from '@/lib/auth/hooks'
import {Avatar, AvatarFallback, AvatarImage} from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {CreditCard, LogOut, Settings, User} from 'lucide-react'
import Link from 'next/link'

export function UserMenu() {
  const {user, signOut, loading} = useAuth()

  if (loading || !user) {
    return (
      <div className="w-8 h-8 rounded-full bg-muted animate-pulse"/>
    )
  }

  const initials = user.profile?.fullName
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase() || user.email?.charAt(0).toUpperCase() || 'U'

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="flex items-center space-x-2 rounded-full focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2">
          <Avatar className="h-8 w-8">
            <AvatarImage
              src={user.profile?.avatarUrl || user.user_metadata?.avatar_url}
              alt={user.profile?.fullName || user.email || 'User'}
            />
            <AvatarFallback>{initials}</AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">
              {user.profile?.fullName || user.user_metadata?.full_name || 'User'}
            </p>
            <p className="text-xs leading-none text-muted-foreground">
              {user.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator/>
        <DropdownMenuItem asChild>
          <Link href="/dashboard/profile" className="flex items-center">
            <User className="mr-2 h-4 w-4"/>
            <span>Profile</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/dashboard/settings" className="flex items-center">
            <Settings className="mr-2 h-4 w-4"/>
            <span>Settings</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/dashboard/billing" className="flex items-center">
            <CreditCard className="mr-2 h-4 w-4"/>
            <span>Billing</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator/>
        <DropdownMenuItem
          className="text-red-600 focus:text-red-600"
          onClick={signOut}
        >
          <LogOut className="mr-2 h-4 w-4"/>
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
