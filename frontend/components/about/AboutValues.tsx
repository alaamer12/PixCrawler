'use client'

import {memo} from 'react'
import {Globe, Heart, Leaf, Lightbulb, Shield, Target, Users, Zap} from 'lucide-react'

interface Value {
  title: string
  description: string
  icon: React.ReactNode
}

const VALUES: Value[] = [
  {
    title: 'Developer-First',
    description: 'Every decision we make is guided by what will best serve our developer community. We build tools we ourselves would want to use.',
    icon: <Heart className="w-6 h-6"/>
  },
  {
    title: 'Privacy & Security',
    description: 'Your data is yours. We implement industry-leading security practices and never compromise on user privacy.',
    icon: <Shield className="w-6 h-6"/>
  },
  {
    title: 'Performance',
    description: 'Speed and reliability are non-negotiable. We optimize every aspect of our platform for maximum efficiency.',
    icon: <Zap className="w-6 h-6"/>
  },
  {
    title: 'Inclusivity',
    description: 'AI should be accessible to everyone, regardless of background, experience level, or resources. We break down barriers.',
    icon: <Users className="w-6 h-6"/>
  },
  {
    title: 'Global Impact',
    description: 'We believe AI can solve humanity\'s biggest challenges. Our tools empower researchers and developers worldwide.',
    icon: <Globe className="w-6 h-6"/>
  },
  {
    title: 'Innovation',
    description: 'We constantly push boundaries, exploring new technologies and methodologies to stay ahead of the curve.',
    icon: <Lightbulb className="w-6 h-6"/>
  },
  {
    title: 'Transparency',
    description: 'Open communication, clear pricing, and honest feedback. We believe trust is built through transparency.',
    icon: <Target className="w-6 h-6"/>
  },
  {
    title: 'Sustainability',
    description: 'We\'re committed to building a sustainable future, optimizing our infrastructure for minimal environmental impact.',
    icon: <Leaf className="w-6 h-6"/>
  }
]

export const AboutValues = memo(() => {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Our Values
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            These principles guide everything we do, from product decisions to how we treat our community.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
          {VALUES.map((value, index) => (
            <div key={index} className="text-center group">
              <div
                className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 text-primary rounded-lg mb-4 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                {value.icon}
              </div>
              <h3 className="text-lg font-semibold mb-3">{value.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{value.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
})

AboutValues.displayName = 'AboutValues'
