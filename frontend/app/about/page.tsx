import {Metadata} from 'next'
import {AboutCTA, AboutFeatures, AboutHero, AboutMission, AboutTechStack} from '@/components/about'

export const metadata: Metadata = {
  title: 'About PixCrawler - DEPI Data Engineering Team',
  description: 'PixCrawler is an automated image dataset builder developed by a data engineering team sponsored by DEPI (Digital Egypt Pioneers Initiative), focused on solving real-world ML challenges.',
  keywords: ['about', 'DEPI', 'data engineering', 'image dataset', 'machine learning', 'Egypt', 'real-world challenges', 'Digital Egypt Pioneers Initiative'],
  openGraph: {
    title: 'About PixCrawler - DEPI Data Engineering Team',
    description: 'Automated image dataset builder developed by DEPI-sponsored data engineering team, solving real-world ML challenges.',
    type: 'website',
  },
  alternates: {
    canonical: 'https://pixcrawler.io/about',
  },
}

export default function AboutPage() {
  return (
    <main className="min-h-screen">
      <AboutHero/>
      <AboutMission/>
      <AboutFeatures/>
      <AboutTechStack/>
      <AboutCTA/>
    </main>
  )
}
