'use client'

import {memo, useMemo} from 'react'
import {Github, Linkedin, Twitter} from 'lucide-react'

interface FooterSection {
  title: string
  links: string[]
}

const footerSections: FooterSection[] = [
  {
    title: 'Product',
    links: ['Features', 'Pricing', 'Documentation', 'API Reference']
  },
  {
    title: 'Company',
    links: ['About', 'Blog', 'Careers', 'Contact']
  },
  {
    title: 'Resources',
    links: ['User Guide', 'Examples', 'FAQ', 'Support']
  },
  {
    title: 'Legal',
    links: ['Privacy Policy', 'Terms of Service', 'Security']
  }
]

const socialIcons = [
  {icon: Twitter, href: 'https://twitter.com'},
  {icon: Linkedin, href: 'https://linkedin.com'},
  {icon: Github, href: 'https://github.com'}
]

const BrandSection = memo(() => {
  return (
    <div className="col-span-2">
      <div className="font-bold text-lg mb-3">PixCrawler</div>
      <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
        Automated image dataset builder for ML & research. Transform keywords into
        organized, validated datasets.
      </p>
    </div>
  )
})
BrandSection.displayName = 'BrandSection'

const FooterLinks = memo(({title, links}: FooterSection) => {
  return (
    <div>
      <div className="font-semibold text-sm mb-3">{title}</div>
      <ul className="space-y-2">
        {links.map((link, j) => (
          <li key={j}>
            <a
              href="#"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {link}
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
})
FooterLinks.displayName = 'FooterLinks'

const SocialLinks = memo(() => {
  return (
    <div className="flex gap-4">
      {socialIcons.map(({icon: Icon, href}, i) => (
        <a
          key={i}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="
						group w-9 h-9 border border-border rounded-lg
						flex items-center justify-center
						transition-all duration-200 ease-out
						hover:bg-muted hover:border-foreground hover:scale-110 hover:shadow-md
					"
        >
          <Icon
            size={18}
            className="
							text-muted-foreground
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
  const footerLinkSections = useMemo(
    () => footerSections.map((section, i) => <FooterLinks key={i} {...section} />),
    []
  )

  return (
    <footer className="py-2 footer-bg md:py-4">
      <div className="container mx-auto px-4 pt-4 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 md:gap-12 mb-12">
          <BrandSection/>
          {footerLinkSections}
        </div>

        <div className="border-t border-border pt-2 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            © 2025 PixCrawler. All rights reserved.
          </p>
          <SocialLinks/>
        </div>
      </div>
    </footer>
  )
})
Footer.displayName = 'Footer'
