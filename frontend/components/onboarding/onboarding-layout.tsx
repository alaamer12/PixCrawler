'use client'

import { Database } from 'lucide-react'
import { ProgressIndicator } from './progress-indicator'

interface OnboardingLayoutProps {
  children: React.ReactNode
  currentStep: number
  totalSteps: number
  onSkip: () => void
}

export function OnboardingLayout({
  children,
  currentStep,
  totalSteps,
  onSkip,
}: OnboardingLayoutProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <div className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-medium text-foreground">
            <div className="bg-gradient-to-br from-primary to-secondary text-primary-foreground flex size-8 items-center justify-center rounded-lg shadow-lg">
              <Database className="size-5" />
            </div>
            <span className="text-xl font-bold">PixCrawler</span>
          </div>
          
          <button
            onClick={onSkip}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-md hover:bg-accent"
          >
            Skip to Dashboard →
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="border-b border-border bg-background">
        <div className="container mx-auto px-4 py-4">
          <ProgressIndicator
            currentStep={currentStep}
            totalSteps={totalSteps}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-4xl">
          {children}
        </div>
      </div>
    </div>
  )
}