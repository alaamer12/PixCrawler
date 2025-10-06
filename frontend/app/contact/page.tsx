import {Metadata} from 'next'
import {ContactHero} from '@/components/contact/ContactHero'
import {ContactForm} from '@/components/contact/ContactForm'

export const metadata: Metadata = {
  title: 'Contact Us - PixCrawler',
  description: 'Get in touch with PixCrawler. Contact our support team for technical help, billing questions, or enterprise solutions.',
  keywords: ['contact', 'support', 'help', 'customer service', 'enterprise sales'],
}

export default function ContactPage() {
  return (
    <main className="min-h-screen">
      <ContactHero/>
      <ContactForm/>
    </main>
  )
}
