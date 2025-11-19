'use client'

import {AlertTriangle, Check, RotateCcw} from 'lucide-react'
import {Button} from '@/components/ui/button'
import Image from 'next/image'
import type {TestResult} from '@/app/welcome/welcome-flow'

// TODO: ⚠️ CRITICAL - PRODUCTION CHANGE REQUIRED ⚠️
// This uses random local images for demo purposes ONLY.
// In PRODUCTION, replace this with a fast API endpoint that:
// - Fetches real crawled images from the test run
// - Returns optimized thumbnails for quick loading
// - Uses CDN/caching for performance
// Example: GET /api/onboarding/test-images?testId={id}
const SAMPLE_IMAGES = Array.from({length: 43}, (_, i) =>
  `/images/vechile/car/${String(i + 1).padStart(4, '0')}.webp`
)

function getRandomImages(count: number): string[] {
  const shuffled = [...SAMPLE_IMAGES].sort(() => Math.random() - 0.5)
  return shuffled.slice(0, count)
}

interface TestResultsPanelProps {
  result: TestResult
  onRetry: () => void
}

export function TestResultsPanel({result, onRetry}: TestResultsPanelProps) {
  if (result.success) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-lg p-8">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <Check className="w-8 h-8 text-green-600"/>
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
                {getRandomImages(4).map((imagePath, index) => (
                  <div
                    key={index}
                    className="relative w-20 h-20 bg-muted border border-border rounded-lg overflow-hidden group hover:scale-105 transition-transform duration-200"
                  >
                    <Image
                      src={imagePath}
                      alt={`Sample ${index + 1}`}
                      fill
                      className="object-cover"
                      sizes="80px"
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors"/>
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
            <AlertTriangle className="w-8 h-8 text-red-600"/>
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

        <Button
          onClick={onRetry}
          variant="default"
          leftIcon={<RotateCcw className="w-4 h-4"/>}
        >
          Retry Test Crawl
        </Button>
      </div>
    </div>
  )
}
