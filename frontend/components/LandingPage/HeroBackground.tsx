'use client'

import {memo} from 'react'

export const HeroBackground = memo(() => {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-muted/20 to-background"/>

      {/* Animated gradient orbs - enhanced for light theme */}
      <div
        className="absolute top-0 left-1/4 w-96 h-96 rounded-full blur-3xl animate-float-slow"
        style={{
          background: 'linear-gradient(135deg, hsl(var(--primary)), hsl(var(--secondary) ))',
          animationDuration: '20s'
        }}
      />

      <div
        className="absolute top-1/3 right-1/4 w-80 h-80 rounded-full blur-3xl animate-float-slow"
        style={{
          background: 'linear-gradient(135deg, hsl(var(--secondary)), hsl(var(--primary)))',
          animationDuration: '25s',
          animationDelay: '2s'
        }}
      />

      <div
        className="absolute bottom-1/4 left-1/3 w-72 h-72 rounded-full blur-3xl animate-float-slow"
        style={{
          background: 'linear-gradient(135deg, hsl(var(--primary) / 0.2), hsl(var(--secondary) / 0.15))',
          animationDuration: '22s',
          animationDelay: '4s'
        }}
      />

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.06] dark:opacity-[0.04]"/>

      {/* Radial gradient overlay */}
      <div className="absolute inset-0 bg-radial-gradient from-transparent via-transparent to-background/80"/>

      {/* Noise texture */}
      <div className="absolute inset-0 bg-noise opacity-[0.025] dark:opacity-[0.015]"/>
    </div>
  )
})
HeroBackground.displayName = 'HeroBackground'
