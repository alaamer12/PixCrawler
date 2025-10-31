'use client'

import {ProgressIndicator} from './progress-indicator'
import React from "react";

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
    <div className="min-h-screen relative overflow-hidden">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(99,102,241,0.1),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.08),transparent_50%)]" />

      {/* Content Container */}
      <div className="relative min-h-screen flex flex-col">

        {/* Two Column Layout */}
        <div className="flex-1 flex">
          {/* Left Sidebar - Progress Indicator */}
          <div className="w-[10%] min-w-[120px] ml-6 p-6 flex items-center justify-center">
            <ProgressIndicator
              currentStep={currentStep}
              totalSteps={totalSteps}
            />
          </div>

          {/* Right Content Area */}
          <div className="flex-1 overflow-y-auto">
            <div className="min-h-full flex items-center justify-center p-4 sm:p-6 md:p-10">
              <div className="w-full max-w-5xl">
                {children}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
