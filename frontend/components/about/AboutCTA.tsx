import {memo} from 'react'
import Link from 'next/link'
import {Button} from '@/components/ui/button'

export const AboutCTA = memo(() => {
  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Build Your Dataset?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Start creating production-ready image datasets in minutes.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">
                Get Started Free
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link href="/contact">
                Contact Us
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
})

AboutCTA.displayName = 'AboutCTA'
