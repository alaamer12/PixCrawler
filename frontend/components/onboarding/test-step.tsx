'use client'

import {useState} from 'react'
import {ArrowLeft, TestTube} from 'lucide-react'
import {Button} from '@/components/ui/button'
import {TestResultsPanel} from './test-results-panel'
import type {DatasetConfig, TestResult} from '@/app/welcome/welcome-flow'

interface TestStepProps {
  config: DatasetConfig
  testResult: TestResult | null
  onTestComplete: (result: TestResult | null) => void
  onNext: () => void
  onBack: () => void
}

export function TestStep({
                           config,
                           testResult,
                           onTestComplete,
                           onNext,
                           onBack,
                         }: TestStepProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleRunTest = async () => {
    setIsLoading(true)

    try {
      const {onboardingService} = await import('@/lib/api/onboarding')
      const result = await onboardingService.runTestCrawl(config)
      onTestComplete(result)
    } catch (error) {
      const result: TestResult = {
        success: false,
        imagesFound: 0,
        error: 'Network error occurred',
        suggestions: ['Check your internet connection', 'Try again in a moment'],
      }
      onTestComplete(result)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRetry = () => {
    onTestComplete(null)
  }

  return (
    <div className="space-y-8">
      {/* Instruction Card */}
      <div className="bg-card border border-border rounded-xl shadow-lg p-8 text-center space-y-6">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <TestTube className="w-8 h-8 text-primary"/>
          </div>
        </div>

        <div className="space-y-3">
          <h2 className="text-3xl font-bold tracking-tight">
            Test Your Configuration
          </h2>
          <p className="text-lg text-muted-foreground max-w-md mx-auto">
            We'll do a quick test with 10 images to make sure everything works correctly.
            This only takes a few seconds.
          </p>
        </div>
      </div>

      {/* Test Button */}
      {!testResult && (
        <Button
          onClick={handleRunTest}
          loading={isLoading}
          loadingText="Running Test Crawl..."
          variant="brand"
          size="lg"
          className="w-full"
        >
          Run Test Crawl
        </Button>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="bg-card border border-border rounded-xl shadow-lg p-8">
          <div className="flex flex-col items-center space-y-4">
            <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"/>
            <div className="text-center space-y-2">
              <p className="font-medium">Testing your configuration...</p>
              <p className="text-sm text-muted-foreground">
                Searching for images with your categories
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Test Results */}
      {testResult && !isLoading && (
        <TestResultsPanel
          result={testResult}
          onRetry={handleRetry}
        />
      )}

      {/* Navigation Buttons */}
      <div className="flex gap-4">
        <Button
          onClick={onBack}
          variant="outline"
          size="lg"
          leftIcon={<ArrowLeft className="w-4 h-4"/>}
        >
          Back
        </Button>

        {testResult?.success && (
          <Button
            onClick={onNext}
            variant="brand"
            size="lg"
            className="flex-1"
            rightIcon={<span>→</span>}
          >
            Looks Good!
          </Button>
        )}
      </div>
    </div>
  )
}
