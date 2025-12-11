'use client'

import {ArrowLeft, Clock, DollarSign, Lightbulb, Rocket, Sparkles, Loader2} from 'lucide-react'
import {Button} from '@/components/ui/button'
import type {DatasetConfig} from '@/app/welcome/welcome-flow'

interface LaunchStepProps {
  config: DatasetConfig
  onLaunch: () => void
  onBack: () => void
  isLaunching?: boolean
}

export function LaunchStep({config, onLaunch, onBack, isLaunching = false}: LaunchStepProps) {
  const totalImages = config.categories.length * config.imagesPerCategory
  const estimatedTime = Math.ceil(totalImages / 60) // Rough estimate: 1 image per second
  const estimatedCost = totalImages > 500 ? '$0.50' : 'Free tier'

  return (
    <div className="space-y-8">
      {/* Summary Card */}
      <div
        className="relative bg-card border border-border rounded-xl shadow-2xl p-8 text-center space-y-6 overflow-hidden group">
        {/* Animated shine border */}
        <div
          className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 animate-shimmer"/>
        <div
          className="absolute inset-0 rounded-xl border-2 border-transparent bg-gradient-to-r from-primary/20 via-purple-500/20 to-primary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          style={{
            WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            WebkitMaskComposite: 'xor',
            maskComposite: 'exclude',
            padding: '2px'
          }}/>

        {/* Glow effect */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/10 rounded-full blur-3xl"/>
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl"/>

        <div className="relative flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 bg-primary/30 blur-xl rounded-full animate-pulse"/>
            <div
              className="relative w-20 h-20 bg-gradient-to-br from-primary/20 via-purple-500/20 to-primary/20 rounded-full flex items-center justify-center border-2 border-primary/30 shadow-lg shadow-primary/20">
              <Rocket className="w-10 h-10 text-primary animate-pulse"/>
            </div>
          </div>
        </div>

        <div className="relative space-y-3">
          <h2
            className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground via-primary to-foreground bg-clip-text text-transparent">
            Ready to Launch!
          </h2>
          <p className="text-sm text-muted-foreground">Your AI-powered dataset is configured and ready</p>
        </div>

        {/* Configuration Summary */}
        <div
          className="relative bg-gradient-to-br from-muted/50 to-muted/30 border border-border/50 rounded-xl p-6 text-left max-w-md mx-auto backdrop-blur-sm shadow-inner">
          <div className="space-y-3">
            <div
              className="flex justify-between items-center py-3 border-b border-border/30 hover:bg-primary/5 transition-colors rounded px-2 -mx-2">
              <span className="text-sm text-muted-foreground font-medium">Dataset Name</span>
              <span className="font-semibold text-foreground">{config.name}</span>
            </div>

            <div
              className="flex justify-between items-center py-3 border-b border-border/30 hover:bg-primary/5 transition-colors rounded px-2 -mx-2">
              <span className="text-sm text-muted-foreground font-medium">Categories</span>
              <span className="font-semibold text-foreground">{config.categories.join(', ')}</span>
            </div>

            <div
              className="flex justify-between items-center py-3 border-b border-border/30 hover:bg-primary/5 transition-colors rounded px-2 -mx-2">
              <span className="text-sm text-muted-foreground font-medium">Images Per Category</span>
              <span className="font-semibold text-primary">{config.imagesPerCategory} images</span>
            </div>

            <div
              className="flex justify-between items-center py-3 border-b border-border/30 hover:bg-primary/5 transition-colors rounded px-2 -mx-2">
              <span className="text-sm text-muted-foreground font-medium">Total Images</span>
              <span
                className="font-bold text-lg bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">~{totalImages} images</span>
            </div>

            <div
              className="flex justify-between items-center py-3 border-b border-border/30 hover:bg-primary/5 transition-colors rounded px-2 -mx-2">
              <span className="text-sm text-muted-foreground flex items-center gap-1.5 font-medium">
                <Clock className="w-4 h-4 text-primary"/>
                Estimated Time
              </span>
              <span className="font-semibold text-foreground">~{estimatedTime} min</span>
            </div>

            <div
              className="flex justify-between items-center py-3 hover:bg-emerald-500/5 transition-colors rounded px-2 -mx-2">
              <span className="text-sm text-muted-foreground flex items-center gap-1.5 font-medium">
                <DollarSign className="w-4 h-4 text-emerald-600"/>
                Cost
              </span>
              <span className="font-bold text-emerald-600 flex items-center gap-1">
                {estimatedCost}
                {estimatedCost === 'Free tier' && <span
                  className="text-xs px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">✓</span>}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          onClick={onBack}
          variant="outline"
          size="lg"
          disabled={isLaunching}
          leftIcon={<ArrowLeft className="w-4 h-4"/>}
        >
          Adjust Settings
        </Button>

        <Button
          onClick={onLaunch}
          variant="brand"
          size="lg"
          className="flex-1"
          disabled={isLaunching}
          rightIcon={isLaunching ? <Loader2 className="w-4 h-4 animate-spin"/> : <Sparkles className="w-4 h-4"/>}
        >
          {isLaunching ? 'Creating Dataset...' : 'Create Full Dataset'}
        </Button>
      </div>

      {/* Help Card */}
      <div className="bg-card border border-border rounded-xl shadow-lg p-6">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
            <Lightbulb className="w-5 h-5 text-blue-600"/>
          </div>

          <div className="space-y-3">
            <h3 className="font-semibold">What happens next?</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Images will download and process in real-time</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>You can monitor progress live on the dashboard</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Get notified when your dataset is complete</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>Download your organized dataset instantly</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
