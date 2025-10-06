'use client'

import Link from 'next/link'
import {memo, useEffect, useState} from 'react'
import {Menu, X} from 'lucide-react'
import {ThemeToggle} from '@/components/theme-toggle'
import {usePathname} from 'next/navigation'

const NavLinks = memo(() => {
  const pathname = usePathname()
  const [activeHash, setActiveHash] = useState('')

  useEffect(() => {
    const handleHashChange = () => {
      setActiveHash(window.location.hash)
    }

    handleHashChange()
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const isActive = (hash: string) => activeHash === hash

  return (
    <div className="hidden md:flex gap-8">
      <a
        href="#features"
        className={`text-sm transition-all relative group ${
          isActive('#features')
            ? 'text-primary font-medium'
            : 'text-foreground hover:text-primary'
        }`}
      >
        Features
        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${
          isActive('#features') ? 'w-full' : 'w-0 group-hover:w-full'
        }`}/>
      </a>
      <a
        href="#pricing"
        className={`text-sm transition-all relative group ${
          isActive('#pricing')
            ? 'text-primary font-medium'
            : 'text-foreground hover:text-primary'
        }`}
      >
        Pricing
        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${
          isActive('#pricing') ? 'w-full' : 'w-0 group-hover:w-full'
        }`}/>
      </a>
      <a
        href="#docs"
        className={`text-sm transition-all relative group ${
          isActive('#docs')
            ? 'text-primary font-medium'
            : 'text-foreground hover:text-primary'
        }`}
      >
        Docs
        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${
          isActive('#docs') ? 'w-full' : 'w-0 group-hover:w-full'
        }`}/>
      </a>
      <a
        href="#blog"
        className={`text-sm transition-all relative group ${
          isActive('#blog')
            ? 'text-primary font-medium'
            : 'text-foreground hover:text-primary'
        }`}
      >
        Blog
        <span className={`absolute -bottom-1 left-0 h-0.5 bg-primary transition-all ${
          isActive('#blog') ? 'w-full' : 'w-0 group-hover:w-full'
        }`}/>
      </a>
    </div>
  )
})
NavLinks.displayName = 'NavLinks'

const AuthButtons = memo(() => (
  <div className="flex items-center gap-3">
    <ThemeToggle/>
    <Link
      href="/login"
      className="px-12 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors right-0"
    >
      Sign In
    </Link>
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
          <NavLinks/>
          <div className="flex items-center gap-3">
            <AuthButtons/>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden w-9 h-9 border border-border rounded flex items-center justify-center hover:bg-muted transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5"/> : <Menu className="h-5 w-5"/>}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 top-[70px] bg-background/95 backdrop-blur z-40 border-b border-border">
          <div className="container mx-auto px-4 py-6 flex flex-col gap-4">
            <a
              href="#features"
              className="text-base hover:text-primary hover:bg-muted transition-all py-2 px-3 rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Features
            </a>
            <a
              href="#pricing"
              className="text-base hover:text-primary hover:bg-muted transition-all py-2 px-3 rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Pricing
            </a>
            <a
              href="#docs"
              className="text-base hover:text-primary hover:bg-muted transition-all py-2 px-3 rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Docs
            </a>
            <a
              href="#blog"
              className="text-base hover:text-primary hover:bg-muted transition-all py-2 px-3 rounded-lg"
              onClick={() => setMobileMenuOpen(false)}
            >
              Blog
            </a>
            <div className="border-t border-border pt-4 mt-2">
              <Link
                href="/login"
                className="px-5 py-3 text-center border border-border rounded-lg hover:bg-muted transition-colors block"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  )
})
Navigation.displayName = 'Navigation'
