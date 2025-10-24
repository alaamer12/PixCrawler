import {memo} from 'react'

export const ContactHero = memo(() => {
  return (
    <section className="py-16 md:py-24 lg:py-32">
      <div className="container mx-auto px-4 lg:px-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Get in{' '}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              touch
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto">
            Have questions about PixCrawler? Need help with your datasets? Want to discuss enterprise solutions?
            We&apos;d love to hear from you.
          </p>
        </div>
      </div>
    </section>
  )
})

ContactHero.displayName = 'ContactHero'
