'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { OnboardingLayout } from '@/components/onboarding/onboarding-layout'
import { ConfigureStep } from '@/components/onboarding/configure-step'
import { TestStep } from '@/components/onboarding/test-step'
import { LaunchStep } from '@/components/onboarding/launch-step'
import type { User } from '@supabase/supabase-js'

export interface DatasetConfig {
  name: string
  categories: string[]
  imagesPerCategory: number
}

export interface TestResult {
  success: boolean
  imagesFound: number
  sampleImages?: string[]
  error?: string
  suggestions?: string[]
}

interface WelcomeFlowProps {
  user: User
}

export function WelcomeFlow({ user }: WelcomeFlowProps) {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [config, setConfig] = useState<DatasetConfig>({
    name: 'my_first_dataset',
    categories: ['cats', 'dogs', 'birds'],
    imagesPerCategory: 100,
  })
  const [testResult, setTestResult] = useState<TestResult | null>(null)

  const handleSkip = () => {
    router.push('/dashboard')
  }

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleConfigChange = (newConfig: DatasetConfig) => {
    setConfig(newConfig)
  }

  const handleTestComplete = (result: TestResult) => {
    setTestResult(result)
  }

  const handleLaunch = async () => {
    try {
      // Create dataset job
      const { onboardingService } = await import('@/lib/api/onboarding')
      const { jobId } = await onboardingService.createDatasetJob(config)
      
      // Mark onboarding as completed
      await onboardingService.completeOnboarding()
      
      // Redirect to dataset monitoring page
      router.push(`/dashboard/datasets/${jobId}`)
    } catch (error) {
      console.error('Failed to launch dataset:', error)
      // For now, just redirect to dashboard
      router.push('/dashboard')
    }
  }

  const userName = user.user_metadata?.full_name || user.email?.split('@')[0] || 'there'

  return (
    <OnboardingLayout
      currentStep={currentStep}
      totalSteps={3}
      onSkip={handleSkip}
    >
      {currentStep === 1 && (
        <ConfigureStep
          userName={userName}
          config={config}
          onConfigChange={handleConfigChange}
          onNext={handleNext}
        />
      )}
      
      {currentStep === 2 && (
        <TestStep
          config={config}
          testResult={testResult}
          onTestComplete={handleTestComplete}
          onNext={handleNext}
          onBack={handleBack}
        />
      )}
      
      {currentStep === 3 && (
        <LaunchStep
          config={config}
          onLaunch={handleLaunch}
          onBack={handleBack}
        />
      )}
    </OnboardingLayout>
  )
}