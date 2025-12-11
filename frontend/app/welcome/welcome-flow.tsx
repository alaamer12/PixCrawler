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
  const [isLaunching, setIsLaunching] = useState(false)

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

  const handleTestComplete = (result: TestResult | null) => {
    setTestResult(result)
  }

  const handleLaunch = async () => {
    if (isLaunching) return // Prevent multiple clicks
    
    setIsLaunching(true)
    console.log('🚀 Starting dataset creation...')
    
    let jobId: string
    
    try {
      // Create dataset job
      const { onboardingService } = await import('@/lib/api/onboarding')
      console.log('📋 Creating dataset job with config:', config)
      
      const result = await onboardingService.createDatasetJob(config)
      jobId = result.jobId
      console.log('✅ Dataset job created:', jobId)

      // Mark onboarding as completed (handles dev mode gracefully)
      await onboardingService.completeOnboarding()
      console.log('✅ Onboarding completed')
      
    } catch (error) {
      console.error('❌ Failed to launch dataset:', error)

      // Create a demo jobId for fallback
      jobId = `demo_${Date.now()}`
      console.log('🔄 Using demo jobId:', jobId)
    } finally {
      // Always redirect to usage page with jobId (after all async operations complete)
      console.log('🔄 Redirecting to usage page...')
      router.push(`/usage?jobId=${jobId}`)
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
          isLaunching={isLaunching}
        />
      )}
    </OnboardingLayout>
  )
}
