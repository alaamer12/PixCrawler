'use client'

import Link from 'next/link'
import { memo } from 'react'
import { Github, Linkedin, Twitter } from 'lucide-react'

interface FooterLink {
  label: string
  href: string
}

interface FooterSection {
  title: string
  links: FooterLink[]
}

const FOOTER_SECTIONS: FooterSection[] = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '#features' },
      { label: 'Pricing', href: '#pricing' },
      { label: 'Documentation', href: '#docs' },
      { label: 'API Reference', href: '#api' }
    ]
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '#about' },
      { label: 'Contact', href: '#contact' }
    ]
  },
  {
    title: 'Resources',
    links: [
      { label: 'Examples', href: '#examples' },
      { label: 'FAQ', href: '#faq' }
    ]
  },
  {
    title: 'Legal',
    links: [
      { label: 'Privacy Policy', href: '#privacy' },
      { label: 'Terms of Service', href: '#terms' }
    ]
  }
]

const SOCIAL_LINKS = [
  { icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
  { icon: Linkedin, href: 'https://linkedin.com', label: 'LinkedIn' },
  { icon: Github, href: 'https://github.com', label: 'GitHub' }
] as const

const BrandSection = memo(() => {
  return (
    <div className="col-span-2">
      <Link href="/" className="inline-block">
        <div className="font-bold text-lg mb-3 text-foreground hover:text-primary transition-colors">
          PixCrawler
        </div>
      </Link>
      <p className="text-sm text-foreground/60 leading-relaxed max-w-sm">
        Automated image dataset builder for ML & research. Transform keywords into
        organized, validated datasets.
      </p>
    </div>
  )
})
BrandSection.displayName = 'BrandSection'

const FooterLinks = memo(({ title, links }: FooterSection) => {
  return (
    <div>
      <div className="font-semibold text-m mb-4 text-foreground">{title}</div>
      <ul className="space-y-2.5">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="text-sm text-foreground/60 text-neutral-500 hover:text-foreground transition-colors inline-block"
            >
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
})
FooterLinks.displayName = 'FooterLinks'

const SocialLinks = memo(() => {
  return (
    <div className="flex gap-3">
      {SOCIAL_LINKS.map(({ icon: Icon, href, label }) => (
        <a
          key={label}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={label}
          className="
            group w-9 h-9 border border-border rounded-lg
            flex items-center justify-center
            transition-all duration-200 ease-out
            hover:bg-muted hover:border-foreground/40 hover:scale-110
          "
        >
          <Icon
            size={18}
            className="
              text-foreground/60
              transition-colors duration-200
              group-hover:text-foreground
            "
          />
        </a>
      ))}
    </div>
  )
})
SocialLinks.displayName = 'SocialLinks'

export const Footer = memo(() => {
  return (
    <footer className="py-12 md:py-16 footer-bg border-t border-border">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8 md:gap-12 mb-12">
          <BrandSection />
          {FOOTER_SECTIONS.map((section) => (
            <FooterLinks key={section.title} {...section} />
          ))}
        </div>

        <div className="border-t border-border pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-foreground/60">
            © 2025 PixCrawler. All rights reserved.
          </p>
          <SocialLinks />
        </div>
      </div>
    </footer>
  )
})
Footer.displayName = 'Footer'