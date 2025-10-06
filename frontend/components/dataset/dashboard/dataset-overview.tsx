'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Dataset {
  id: string
  name: string
  status: 'processing' | 'complete' | 'failed' | 'paused'
  totalImages: number
  categories: number
  qualityScore: number
  totalSize: string
  createdAt?: string
  completedAt?: string
}

interface DatasetOverviewProps {
  dataset: Dataset
}

export function DatasetOverview({ dataset }: DatasetOverviewProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  const processingStats = {
    started: 'Jan 15, 2025 14:32',
    completed: 'Jan 15, 2025 14:47',
    duration: '15 minutes',
    processed: 2103,
    valid: 1847,
    duplicatesRemoved: 256,
  }

  const validationResults = {
    formatValidation: 100,
    sizeValidation: 98.7,
    integrityCheck: 99.1,
    duplicateDetection: 'Complete',
    qualityAssessment: 'Complete',
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto bg-muted/30">
      <div>
        <h2 className="text-2xl font-bold mb-6">Dataset Overview</h2>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="text-3xl font-bold mb-2">
                {dataset.totalImages.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Total Images</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="text-3xl font-bold mb-2">{dataset.categories}</div>
              <div className="text-sm text-muted-foreground">Categories</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="text-3xl font-bold mb-2">{dataset.qualityScore}%</div>
              <div className="text-sm text-muted-foreground">Quality Score</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="text-3xl font-bold mb-2">{dataset.totalSize}</div>
              <div className="text-sm text-muted-foreground">Total Size</div>
            </CardContent>
          </Card>
        </div>

        {/* Distribution Chart Placeholder */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Distribution by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 bg-muted rounded-lg flex items-center justify-center text-muted-foreground">
              Bar Chart: Category Distribution
            </div>
          </CardContent>
        </Card>

        {/* Quality Metrics Chart Placeholder */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Quality Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48 bg-muted rounded-lg flex items-center justify-center text-muted-foreground">
              Quality Score Distribution Chart
            </div>
          </CardContent>
        </Card>

        {/* Processing Summary and Validation Results */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Processing Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Started:</span>
                <span>{processingStats.started}</span>
              </div>
              <div className="flex justify-between">
                <span>Completed:</span>
                <span>{processingStats.completed}</span>
              </div>
              <div className="flex justify-between">
                <span>Duration:</span>
                <span>{processingStats.duration}</span>
              </div>
              <div className="flex justify-between">
                <span>Images processed:</span>
                <span>{processingStats.processed.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Valid images:</span>
                <span>{processingStats.valid.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Duplicates removed:</span>
                <span>{processingStats.duplicatesRemoved}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Validation Results</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Format validation:</span>
                <span>{validationResults.formatValidation}%</span>
              </div>
              <div className="flex justify-between">
                <span>Size validation:</span>
                <span>{validationResults.sizeValidation}%</span>
              </div>
              <div className="flex justify-between">
                <span>Integrity check:</span>
                <span>{validationResults.integrityCheck}%</span>
              </div>
              <div className="flex justify-between">
                <span>Duplicate detection:</span>
                <Badge variant="outline" className="text-xs">
                  {validationResults.duplicateDetection}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span>Quality assessment:</span>
                <Badge variant="outline" className="text-xs">
                  {validationResults.qualityAssessment}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}