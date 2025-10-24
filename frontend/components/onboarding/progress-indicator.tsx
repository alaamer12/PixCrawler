'use client'

import {Check, Sparkles} from 'lucide-react'
import {cn} from '@/lib/utils'

interface ProgressIndicatorProps {
  currentStep: number
  totalSteps: number
}

const stepLabels = ['Configure', 'Test', 'Launch']
const stepDescriptions = ['Set up your dataset', 'Validate & preview', 'Deploy & build']

export function ProgressIndicator({currentStep, totalSteps}: ProgressIndicatorProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-8">
      {Array.from({length: totalSteps}, (_, index) => {
        const stepNumber = index + 1
        const isActive = stepNumber === currentStep
        const isCompleted = stepNumber < currentStep
        const isLast = stepNumber === totalSteps

        return (
          <div key={stepNumber} className="flex flex-col items-center gap-4">
            <div className="flex flex-col items-center gap-2 group">
              {/* Step Circle */}
              <div className="relative">
                {/* Glow effect for active step */}
                {isActive && (
                  <>
                    <div className="absolute inset-0 rounded-full bg-primary/20 blur-xl animate-pulse" />
                    <div className="absolute inset-0 rounded-full border-2 border-primary animate-ping opacity-25" />
                  </>
                )}
                
                {/* Completion glow */}
                {isCompleted && (
                  <div className="absolute inset-0 rounded-full bg-primary/15 blur-lg" />
                )}
                
                <div
                  className={cn(
                    'relative flex size-12 items-center justify-center rounded-full border-2 font-bold transition-all duration-500 ease-out',
                    isCompleted && 'bg-gradient-to-br from-primary to-primary/80 border-primary text-primary-foreground shadow-xl shadow-primary/30 scale-105',
                    isActive && 'border-primary text-primary bg-gradient-to-br from-primary/15 via-purple-500/10 to-primary/15 scale-[1.15] shadow-2xl shadow-primary/25',
                    !isActive && !isCompleted && 'border-border/40 text-muted-foreground/60 bg-background/60 backdrop-blur-sm'
                  )}
                >
                  {/* Inner glow ring for active */}
                  {isActive && (
                    <div className="absolute inset-1 rounded-full border border-primary/30 animate-pulse" />
                  )}
                  
                  {isCompleted ? (
                    <Check className="size-5 animate-in zoom-in-50 spin-in-180 duration-500" strokeWidth={3} />
                  ) : (
                    <span className={cn(
                      "text-sm font-bold transition-all duration-300",
                      isActive && "scale-110"
                    )}>
                      {stepNumber}
                    </span>
                  )}
                  
                </div>
              </div>

              {/* Step Label */}
              <div className="flex flex-col items-center gap-0.5">
                <div
                  className={cn(
                    'text-xs font-bold transition-all duration-300 text-center',
                    isActive && 'text-foreground scale-105 tracking-tight',
                    isCompleted && 'text-foreground/70',
                    !isActive && !isCompleted && 'text-muted-foreground/50'
                  )}
                >
                  {stepLabels[index]}
                </div>
                <div
                  className={cn(
                    'text-[10px] transition-all duration-300 text-center leading-tight',
                    isActive && 'text-muted-foreground font-medium',
                    isCompleted && 'text-muted-foreground/50',
                    !isActive && !isCompleted && 'text-muted-foreground/40'
                  )}
                >
                  {stepDescriptions[index]}
                </div>
              </div>
            </div>

            {/* Vertical Connector Line */}
            {!isLast && (
              <div className="relative w-1 h-12 bg-gradient-to-b from-border/20 to-border/30 rounded-full overflow-hidden">
                {/* Progress fill */}
                <div
                  className={cn(
                    'absolute inset-0 bg-gradient-to-b from-primary via-purple-500 to-primary rounded-full transition-all duration-700 ease-out',
                    isCompleted ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0'
                  )}
                >
                  {/* Shimmer effect */}
                  {isCompleted && (
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/40 to-transparent animate-shimmer" />
                  )}
                </div>
                
                {/* Active pulse */}
                {isCompleted && (
                  <div className="absolute bottom-0 left-1/2 -translate-x-1/2 size-2 bg-primary rounded-full animate-pulse shadow-lg shadow-primary/50" />
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
