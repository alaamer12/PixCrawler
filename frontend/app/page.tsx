import {createClient} from '@/lib/supabase/server'
import {redirect} from 'next/navigation'
import {Features, Hero, HowItWorks, UseCases} from '@/components/LandingPage'
import type {Metadata} from 'next'

export const metadata: Metadata = {
  title: 'PixCrawler - Build ML Image Datasets in Minutes',
  description: 'Automated image dataset builder for machine learning. Multi-source crawling, AI-powered validation, and instant ML-ready datasets. Perfect for researchers, developers, and enterprises.',
  openGraph: {
    title: 'PixCrawler - Build ML Image Datasets in Minutes',
    description: 'Automated image dataset builder for machine learning. Multi-source crawling, AI-powered validation, and instant ML-ready datasets.',
    type: 'website',
  },
}

export default async function HomePage() {
  const supabase = await createClient()

  const {
    data: {user},
  } = await supabase.auth.getUser()

  // Redirect authenticated users to dashboard
  if (user) {
    redirect('/dashboard')
  }

  return (
    <>
      <Hero/>
      <Features/>
      <HowItWorks/>
      <UseCases/>
    </>
  )
}
