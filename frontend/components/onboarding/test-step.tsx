'use client'

import {useState} from 'react'
import {ArrowLeft, TestTube} from 'lucide-react'
import {TestResultsPanel} from './test-results-panel'
import type {DatasetConfig, TestResult} from '@/app/welcome/welcome-flow'

interface TestStepProps {
  config: DatasetConfig
  testResult: TestResult | null
  onTestComplete: (result: TestResult) => void
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
        <button
          onClick={handleRunTest}
          disabled={isLoading}
          className="w-full py-4 px-6 bg-gradient-to-r from-primary to-secondary text-primary-foreground font-semibold rounded-lg hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
        >
          {isLoading ? 'Running Test Crawl...' : 'Run Test Crawl'}
        </button>
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
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-6 py-3 border border-border rounded-lg hover:bg-accent transition-colors"
        >
          <ArrowLeft className="w-4 h-4"/>
          Back
        </button>

        {testResult?.success && (
          <button
            onClick={onNext}
            className="flex-1 py-3 px-6 bg-gradient-to-r from-primary to-secondary text-primary-foreground font-semibold rounded-lg hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all shadow-lg hover:shadow-xl"
          >
            Looks Good! →
          </button>
        )}
      </div>
    </div>
  )
}
