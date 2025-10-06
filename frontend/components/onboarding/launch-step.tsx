'use client'

import {ArrowLeft, Clock, DollarSign, Lightbulb, Rocket} from 'lucide-react'
import type {DatasetConfig} from '@/app/welcome/welcome-flow'

interface LaunchStepProps {
  config: DatasetConfig
  onLaunch: () => void
  onBack: () => void
}

export function LaunchStep({config, onLaunch, onBack}: LaunchStepProps) {
  const totalImages = config.categories.length * config.imagesPerCategory
  const estimatedTime = Math.ceil(totalImages / 60) // Rough estimate: 1 image per second
  const estimatedCost = totalImages > 500 ? '$0.50' : 'Free tier'

  return (
    <div className="space-y-8">
      {/* Summary Card */}
      <div className="bg-card border border-border rounded-xl shadow-lg p-8 text-center space-y-6">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <Rocket className="w-8 h-8 text-primary"/>
          </div>
        </div>

        <div className="space-y-3">
          <h2 className="text-3xl font-bold tracking-tight">
            Ready to Launch!
          </h2>
        </div>

        {/* Configuration Summary */}
        <div className="bg-muted/30 border border-border rounded-lg p-6 text-left max-w-md mx-auto">
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-border/50">
              <span className="text-sm text-muted-foreground">Dataset Name</span>
              <span className="font-medium">{config.name}</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-border/50">
              <span className="text-sm text-muted-foreground">Categories</span>
              <span className="font-medium">{config.categories.join(', ')}</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-border/50">
              <span className="text-sm text-muted-foreground">Images Per Category</span>
              <span className="font-medium">{config.imagesPerCategory} images</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-border/50">
              <span className="text-sm text-muted-foreground">Total Images</span>
              <span className="font-medium">~{totalImages} images</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-border/50">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Clock className="w-3 h-3"/>
                Estimated Time
              </span>
              <span className="font-medium">~{estimatedTime} minutes</span>
            </div>

            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <DollarSign className="w-3 h-3"/>
                Cost
              </span>
              <span className="font-medium text-green-600">{estimatedCost}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-6 py-3 border border-border rounded-lg hover:bg-accent transition-colors"
        >
          <ArrowLeft className="w-4 h-4"/>
          Adjust Settings
        </button>

        <button
          onClick={onLaunch}
          className="flex-1 py-4 px-6 bg-gradient-to-r from-primary to-secondary text-primary-foreground font-semibold rounded-lg hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all shadow-lg hover:shadow-xl"
        >
          Create Full Dataset 🎉
        </button>
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
