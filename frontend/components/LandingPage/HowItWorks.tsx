'use client'

import {Fragment, memo} from 'react'
import {CheckCircle2, Download, Search, Sparkles} from 'lucide-react'

interface Step {
  num: number
  title: string
  desc: string
  icon: typeof Search
  features: string[]
  color: string
}

const steps: Step[] = [
  {
    num: 1,
    title: 'Define Your Vision',
    desc: 'Describe what you need - from simple keywords to complex JSON schemas. Our intelligent parser understands your requirements.',
    icon: Search,
    features: ['Natural language input', 'JSON schema support', 'Advanced filters'],
    color: 'from-blue-500/20 to-cyan-500/20'
  },
  {
    num: 2,
    title: 'AI-Powered Processing',
    desc: 'Watch as our distributed system crawls multiple sources, validates quality, and organizes your dataset in real-time.',
    icon: Sparkles,
    features: ['Multi-engine crawling', 'Quality validation', 'Smart deduplication'],
    color: 'from-purple-500/20 to-pink-500/20'
  },
  {
    num: 3,
    title: 'Ready to Use',
    desc: 'Download your curated, validated, and optimized dataset. Instantly ready for training, analysis, or production.',
    icon: Download,
    features: ['Optimized formats', 'Metadata included', 'Production-ready'],
    color: 'from-green-500/20 to-emerald-500/20'
  }
]

const StepCard = memo(({num, title, desc, icon: Icon, features, color}: Step) => {
  return (
    <div className="group relative flex-1">
      {/* Animated gradient background */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${color} rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-xl`}/>

      {/* Card content */}
      <div
        className="relative bg-background/95 backdrop-blur-sm border border-border rounded-2xl p-6 md:p-8 h-full transition-all duration-300 hover:shadow-2xl hover:scale-[1.02] hover:border-foreground/20">

        {/* Icon */}
        <div
          className="w-14 h-14 rounded-xl bg-gradient-to-br from-foreground/10 to-foreground/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
          <Icon className="w-7 h-7" strokeWidth={1.5}/>
        </div>

        {/* Title */}
        <h3 className="font-bold text-xl md:text-2xl mb-3">
          {title}
        </h3>

        {/* Description */}
        <p className="text-sm md:text-base text-muted-foreground leading-relaxed mb-4">
          {desc}
        </p>

        {/* Features list */}
        <ul className="space-y-2 mt-auto">
          {features.map((feature) => (
            <li key={feature} className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0"/>
              <span>{feature}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
})
StepCard.displayName = 'StepCard'

const FlowArrow = memo(() => {
  return (
    <div className="hidden lg:flex items-center justify-center px-4 animate-pulse">
      {/* <ArrowRight className="w-8 h-8 text-muted-foreground/50" strokeWidth={2} /> */}
    </div>
  )
})
FlowArrow.displayName = 'FlowArrow'

export const HowItWorks = memo(() => {
  return (
    <section id="how-it-works" className="relative border-b border-border py-20 md:py-32 overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-muted/30 to-background"/>
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5 rounded-full blur-3xl"/>

      <div className="container relative mx-auto px-4 lg:px-8">
        {/* Section header */}
        <div className="text-center mb-16 md:mb-20">
          <div
            className="inline-block px-4 py-1.5 bg-foreground/5 border border-foreground/10 rounded-full text-sm font-medium mb-4">
            Simple Process
          </div>
          <h2
            className="text-4xl md:text-5xl lg:text-6xl font-bold mb-4 bg-gradient-to-r from-foreground via-foreground/90 to-foreground/80 bg-clip-text text-transparent">
            From Idea to Dataset
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto">
            Three simple steps to build production-ready image datasets
          </p>
        </div>

        {/* Steps grid */}
        <div
          className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr_auto_1fr] gap-8 lg:gap-0 max-w-7xl mx-auto items-start">
          {steps.map((step, i) => (
            <Fragment key={step.num}>
              <StepCard {...step} />
              {i < steps.length - 1 && <FlowArrow/>}
            </Fragment>
          ))}
        </div>

        {/* Call to action hint */}
        <div className="text-center mt-16 md:mt-20">
          <p className="text-muted-foreground text-sm md:text-base">
            Ready to start building?
            <span className="ml-2 text-foreground font-medium hover:underline cursor-pointer">
							Get started now →
						</span>
          </p>
        </div>
      </div>
    </section>
  )
})
HowItWorks.displayName = 'HowItWorks'
