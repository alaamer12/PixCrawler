'use client'

import Link from 'next/link'
import { memo, useEffect, useState } from 'react'
import { Menu, X } from 'lucide-react'
import { Button, IconButton } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme-toggle'

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
      className={`text-sm transition-all relative group ${
        isActive
          ? 'text-foreground font-medium'
          : 'text-foreground/60 hover:text-foreground'
      }`}
    >
      {label}
      <span
        className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${
          isActive ? 'w-full' : 'w-0 group-hover:w-full'
        }`}
      />
    </Link>
  )
})
NavLink.displayName = 'NavLink'

const NavLinks = memo(() => {
  const [activeSection, setActiveSection] = useState('')

  useEffect(() => {
    const updateActiveSection = () => {
      if (typeof window !== 'undefined') {
        setActiveSection(window.location.pathname)
      }
    }

    updateActiveSection()
    window.addEventListener('popstate', updateActiveSection)
    
    return () => {
      window.removeEventListener('popstate', updateActiveSection)
    }
  }, [])

  return (
    <div className="hidden md:flex gap-8">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.href}
          href={item.href}
          label={item.label}
          isActive={activeSection === item.href}
        />
      ))}
    </div>
  )
})
NavLinks.displayName = 'NavLinks'

const AuthButtons = memo(() => (
  <div className="flex items-center gap-3">
    <ThemeToggle />
    <Button asChild variant="outline">
      <Link href="/login">Sign In</Link>
    </Button>
  </div>
))
AuthButtons.displayName = 'AuthButtons'

export const Navigation = memo(() => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <>
      <nav className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-50">
        <div className="container mx-auto px-4 lg:px-8 h-[70px] flex items-center justify-between">
          <Link href="/" className="text-xl font-bold">
            PixCrawler
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
              <Button asChild variant="outline" className="w-full">
                <Link href="/login">Sign In</Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
})
Navigation.displayName = 'Navigation'