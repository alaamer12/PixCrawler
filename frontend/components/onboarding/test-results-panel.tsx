'use client'

import { Check, AlertTriangle, RotateCcw } from 'lucide-react'
import type { TestResult } from '@/app/welcome/welcome-flow'

interface TestResultsPanelProps {
  result: TestResult
  onRetry: () => void
}

export function TestResultsPanel({ result, onRetry }: TestResultsPanelProps) {
  if (result.success) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-lg p-8">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <Check className="w-8 h-8 text-green-600" />
            </div>
          </div>
          
          <div className="space-y-2">
            <h3 className="text-2xl font-bold text-green-600">
              Found {result.imagesFound} images successfully!
            </h3>
            <p className="text-muted-foreground">
              Your configuration is working perfectly
            </p>
          </div>

          {result.sampleImages && result.sampleImages.length > 0 && (
            <div className="space-y-4">
              <p className="text-sm font-medium">Sample images found:</p>
              <div className="flex justify-center gap-4">
                {result.sampleImages.slice(0, 4).map((imageUrl, index) => (
                  <div
                    key={index}
                    className="w-20 h-20 bg-muted border border-border rounded-lg flex items-center justify-center text-xs text-muted-foreground"
                  >
                    Image {index + 1}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-xl shadow-lg p-8">
      <div className="text-center space-y-6">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-red-600" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h3 className="text-2xl font-bold text-red-600">
            {result.error || 'Test failed'}
          </h3>
          <p className="text-muted-foreground">
            Only found {result.imagesFound} images with current settings
          </p>
        </div>

        {result.suggestions && result.suggestions.length > 0 && (
          <div className="border-t border-border pt-6 text-left max-w-md mx-auto">
            <h4 className="font-semibold text-sm mb-3">Try these fixes:</h4>
            <ul className="space-y-2">
              {result.suggestions.map((suggestion, index) => (
                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Retry Test Crawl
        </button>
      </div>
    </div>
  )
}