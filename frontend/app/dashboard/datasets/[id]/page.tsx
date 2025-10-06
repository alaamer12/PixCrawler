'use client'

import {useParams} from 'next/navigation'
import {ArrowLeft, Pause, X} from 'lucide-react'
import Link from 'next/link'

export default function DatasetDetailPage() {
  const params = useParams()
  const jobId = params.id as string

  // Mock data for now
  const dataset = {
    id: jobId,
    name: 'my_first_dataset',
    status: 'processing',
    progress: 45,
    categories: ['cats', 'dogs', 'birds'],
    totalImages: 300,
    downloadedImages: 135,
    validImages: 128,
    currentStage: 'Downloading images...',
    estimatedTimeRemaining: '3 minutes',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4"/>
            Back to Dashboard
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="flex items-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-accent transition-colors">
            <Pause className="w-4 h-4"/>
            Pause
          </button>
          <button
            className="flex items-center gap-2 px-3 py-2 border border-destructive text-destructive rounded-lg hover:bg-destructive/10 transition-colors">
            <X className="w-4 h-4"/>
            Cancel
          </button>
        </div>
      </div>

      {/* Dataset Info */}
      <div className="bg-card border border-border rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">{dataset.name}</h1>
            <p className="text-muted-foreground">
              Categories: {dataset.categories.join(', ')}
            </p>
          </div>

          <div className="text-right">
            <div className="text-2xl font-bold text-primary">{dataset.progress}%</div>
            <div className="text-sm text-muted-foreground">Complete</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2 mb-6">
          <div className="flex justify-between text-sm">
            <span>{dataset.currentStage}</span>
            <span>{dataset.estimatedTimeRemaining} remaining</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-gradient-to-r from-primary to-secondary h-2 rounded-full transition-all duration-500"
              style={{width: `${dataset.progress}%`}}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-muted/30 rounded-lg">
            <div className="text-2xl font-bold">{dataset.downloadedImages}</div>
            <div className="text-sm text-muted-foreground">Downloaded</div>
          </div>
          <div className="text-center p-4 bg-muted/30 rounded-lg">
            <div className="text-2xl font-bold">{dataset.validImages}</div>
            <div className="text-sm text-muted-foreground">Valid</div>
          </div>
          <div className="text-center p-4 bg-muted/30 rounded-lg">
            <div className="text-2xl font-bold">{dataset.totalImages}</div>
            <div className="text-sm text-muted-foreground">Target</div>
          </div>
        </div>
      </div>

      {/* Live Image Stream */}
      <div className="bg-card border border-border rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Live Image Stream</h3>
        <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4">
          {Array.from({length: 16}, (_, i) => (
            <div
              key={i}
              className="aspect-square bg-muted border border-border rounded-lg flex items-center justify-center text-xs text-muted-foreground animate-pulse"
            >
              {i < 8 ? `Image ${i + 1}` : '...'}
            </div>
          ))}
        </div>
      </div>

      {/* Congratulations Message */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-xl p-6 text-center">
        <div className="text-2xl mb-2">🎉</div>
        <h3 className="text-lg font-semibold text-green-800 mb-2">
          Congratulations on creating your first dataset!
        </h3>
        <p className="text-green-700 mb-4">
          Your dataset is being processed. You can monitor the progress here and will be notified when it's complete.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/dashboard"
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Go to Dashboard
          </Link>
          <button className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors">
            Learn More
          </button>
        </div>
      </div>
    </div>
  )
}
