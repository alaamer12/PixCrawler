'use client'

import Link from 'next/link'
import { memo, useState } from 'react'
import { Menu, X, User, Settings, LogOut, LayoutDashboard } from 'lucide-react'
import { Button, IconButton } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme-toggle'
import { Logo } from '@/components/shared/Logo'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth/hooks'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

const NAV_ITEMS = [
  { href: '/', label: 'Home' },
  { href: '/about', label: 'About' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/examples', label: 'Examples' },
] as const

interface NavLinkProps {
  href: string
  label: string
  isActive: boolean
  onClick?: () => void
  isMobile?: boolean
}

const NavLink = memo(({ href, label, isActive, onClick, isMobile = false }: NavLinkProps) => {
  if (isMobile) {
    return (
      <Link
        href={href}
        className="text-base text-foreground/60 hover:text-foreground hover:bg-muted transition-all py-2 px-3 rounded-lg"
        onClick={onClick}
      >
        {label}
      </Link>
    )
  }

  return (
    <Link
      href={href}
      className={`text-sm transition-all relative group ${isActive
        ? 'text-foreground font-medium'
        : 'text-foreground/60 hover:text-foreground'
        }`}
    >
      {label}
      <span
        className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${isActive ? 'w-full' : 'w-0 group-hover:w-full'
          }`}
      />
    </Link>
  )
})
NavLink.displayName = 'NavLink'

const NavLinks = memo(() => {
  const pathname = usePathname() || '/'

  return (
    <div className="hidden md:flex gap-8">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.href}
          href={item.href}
          label={item.label}
          isActive={pathname === item.href}
        />
      ))}
    </div>
  )
})
NavLinks.displayName = 'NavLinks'

const AuthButtons = memo(() => {
  const { user, signOut } = useAuth()
  const router = useRouter()

  const handleSignOut = async () => {
    await signOut()
    router.push('/')
  }

  return (
    <div className="flex items-center gap-3">
      <ThemeToggle />
      {user ? (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-8 w-8 rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarImage src={user.profile?.avatarUrl} alt={user.profile?.fullName || 'User'} />
                <AvatarFallback>{user.profile?.fullName?.charAt(0) || user.email?.charAt(0) || 'U'}</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{user.profile?.fullName || 'User'}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user.email}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/dashboard" className="cursor-pointer">
                <LayoutDashboard className="mr-2 h-4 w-4" />
                <span>Dashboard</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/dashboard/profile" className="cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/dashboard/settings" className="cursor-pointer">
                <Settings className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut} className="cursor-pointer text-destructive focus:text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ) : (
        <Button asChild variant="outline">
          <Link href="/login">Sign In</Link>
        </Button>
      )}
    </div>
  )
})
AuthButtons.displayName = 'AuthButtons'

export const Navigation = memo(() => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <>
      <nav className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-50">
        <div className="container mx-auto px-4 lg:px-8 h-[70px] flex items-center justify-between">
          <Link href="/" aria-label="PixCrawler Home">
            <Logo showIcon showText size="md" />
          </Link>
          <NavLinks />
          <div className="flex items-center gap-3">
            <AuthButtons />
            <IconButton
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden"
              variant="outline"
              size="icon-sm"
              icon={mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            />
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 top-[70px] bg-background/95 backdrop-blur z-40 border-b border-border">
          <div className="container mx-auto px-4 py-6 flex flex-col gap-4">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.href}
                href={item.href}
                label={item.label}
                isActive={false}
                onClick={() => setMobileMenuOpen(false)}
                isMobile
              />
            ))}
            <div className="border-t border-border pt-4 mt-2">
              <AuthButtons />
            </div>
          </div>
        </div>
      )}
    </>
  )
})
Navigation.displayName = 'Navigation'
