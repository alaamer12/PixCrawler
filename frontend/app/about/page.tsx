import {Metadata} from 'next'
import dynamic from 'next/dynamic'
import {AboutHero} from '@/components/about/AboutHero'

// Dynamically import heavy components
const AboutStory = dynamic(() => import('@/components/about/AboutStory').then(mod => ({default: mod.AboutStory})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading story...</div>
  </div>
})

const AboutValues = dynamic(() => import('@/components/about/AboutValues').then(mod => ({default: mod.AboutValues})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading values...</div>
  </div>
})

const AboutTeam = dynamic(() => import('@/components/about/AboutTeam').then(mod => ({default: mod.AboutTeam})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading team...</div>
  </div>
})

const AboutCTA = dynamic(() => import('@/components/about/AboutCTA').then(mod => ({default: mod.AboutCTA})), {
  loading: () => <div className="py-16 flex justify-center">
    <div className="animate-pulse">Loading...</div>
  </div>
})

export const metadata: Metadata = {
  title: 'About Us - PixCrawler',
  description: 'Learn about PixCrawler\'s mission to democratize AI development. Meet our team of engineers, researchers, and designers building the future of image datasets.',
  keywords: ['about', 'team', 'mission', 'AI development', 'computer vision', 'machine learning'],
}

export default function AboutPage() {
  return (
    <main className="min-h-screen">
      <AboutHero/>
      <AboutStory/>
      <AboutValues/>
      <AboutTeam/>
      <AboutCTA/>
    </main>
  )
}
