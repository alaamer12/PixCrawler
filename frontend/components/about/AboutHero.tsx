import {memo} from 'react'
import {Rocket} from 'lucide-react'

export const AboutHero = memo(() => {
  return (
    <section className="py-16 md:py-24 lg:py-32">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            About <span
            className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">PixCrawler</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            An automated image dataset builder developed by a data engineering team,
            sponsored by <strong className="text-foreground">DEPI (Digital Egypt Pioneers Initiative)</strong>,
            focused on solving real-world machine learning challenges.
          </p>
          <div
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/20 rounded-full text-sm font-medium text-primary">
            <Rocket className="w-4 h-4"/>
            Currently in Development
          </div>
        </div>
      </div>
    </section>
  )
})

AboutHero.displayName = 'AboutHero'
