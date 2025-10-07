'use client'

import {Check} from 'lucide-react'
import {cn} from '@/lib/utils'

interface ProgressIndicatorProps {
  currentStep: number
  totalSteps: number
}

const stepLabels = ['Configure', 'Test', 'Launch']

export function ProgressIndicator({currentStep, totalSteps}: ProgressIndicatorProps) {
  return (
    <div className="flex items-center justify-center">
      <div className="flex items-center gap-8">
        {Array.from({length: totalSteps}, (_, index) => {
          const stepNumber = index + 1
          const isActive = stepNumber === currentStep
          const isCompleted = stepNumber < currentStep
          const isLast = stepNumber === totalSteps

          return (
            <div key={stepNumber} className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    'flex size-10 items-center justify-center rounded-full border-2 font-semibold transition-colors',
                    isCompleted && 'bg-primary border-primary text-primary-foreground',
                    isActive && 'border-primary text-primary bg-primary/10',
                    !isActive && !isCompleted && 'border-muted-foreground/30 text-muted-foreground'
                  )}
                >
                  {isCompleted ? (
                    <Check className="size-5"/>
                  ) : (
                    <span className="text-sm">{stepNumber}</span>
                  )}
                </div>
                <div className="hidden md:block">
                  <div
                    className={cn(
                      'text-sm font-medium transition-colors',
                      isActive && 'text-foreground',
                      isCompleted && 'text-muted-foreground',
                      !isActive && !isCompleted && 'text-muted-foreground/60'
                    )}
                  >
                    {stepLabels[index]}
                  </div>
                </div>
              </div>

              {!isLast && (
                <div
                  className={cn(
                    'h-0.5 w-16 transition-colors',
                    isCompleted ? 'bg-primary' : 'bg-muted-foreground/20'
                  )}
                />
              )}
            </div>
          )
        })}
      </div>

      {/* Mobile step indicator */}
      <div className="md:hidden text-sm text-muted-foreground">
        Step {currentStep} of {totalSteps}
      </div>
    </div>
  )
}
