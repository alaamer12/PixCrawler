'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  ArrowLeft,
  Download,
  Settings,
  Image as ImageIcon,
  Activity,
  Calendar,
  Database,
  FileText,
  CheckCircle2
} from 'lucide-react'
import Link from 'next/link'
import { StatusBadge } from '@/components/dashboard/data-table'
import { JobProgress } from '@/components/dashboard/progress-bar'
import { QuickStatsCard } from '@/components/dashboard/stats-card'

interface Dataset {
  id: string
  projectId: string
  projectName: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  imagesCollected: number
  totalImages: number
  keywords: string[]
  sources: string[]
  config: {
    aiExpansion: boolean
    deduplicationLevel: string
    minImageSize: number
    imageFormat: string
    safeSearch: boolean
  }
  createdAt: Date
  completedAt?: Date
}

interface Job {
  id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  progress: number
  totalItems: number
  processedItems: number
  startedAt?: Date
  completedAt?: Date
  logs: JobLog[]
}

interface JobLog {
  id: string
  timestamp: Date
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
}

export default function DatasetViewPage() {
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string
  const datasetId = params.datasetId as string

  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [job, setJob] = useState<Job | null>(null)

  useEffect(() => {
    // TODO: Fetch dataset and job data from API
    // Simulate API call
    setTimeout(() => {
      setDataset({
        id: datasetId,
        projectId,
        projectName: 'Wildlife Conservation Dataset',
        name: 'Lions and Tigers',
        status: 'processing',
        imagesCollected: 1520,
        totalImages: 3000,
        keywords: ['african lion', 'lion pride', 'bengal tiger', 'tiger cub', 'wild cats'],
        sources: ['google', 'bing', 'pixabay'],
        config: {
          aiExpansion: true,
          deduplicationLevel: 'medium',
          minImageSize: 512,
          imageFormat: 'any',
          safeSearch: true
        },
        createdAt: new Date('2024-01-18T10:00:00')
      })

      setJob({
        id: 'job_1',
        status: 'running',
        progress: 65,
        totalItems: 3000,
        processedItems: 1950,
        startedAt: new Date('2024-01-20T10:00:00'),
        logs: [
          {
            id: '1',
            timestamp: new Date('2024-01-20T10:00:00'),
            level: 'info',
            message: 'Job started - Initializing crawlers for 3 sources'
          },
          {
            id: '2',
            timestamp: new Date('2024-01-20T10:05:00'),
            level: 'success',
            message: 'Google Images: Successfully fetched 800 images'
          },
          {
            id: '3',
            timestamp: new Date('2024-01-20T10:15:00'),
            level: 'success',
            message: 'Bing Images: Successfully fetched 650 images'
          },
          {
            id: '4',
            timestamp: new Date('2024-01-20T10:25:00'),
            level: 'info',
            message: 'Running deduplication - Found 120 duplicate images'
          },
          {
            id: '5',
            timestamp: new Date('2024-01-20T10:30:00'),
            level: 'warning',
            message: 'Pixabay: Rate limit reached, retrying in 30 seconds'
          },
          {
            id: '6',
            timestamp: new Date('2024-01-20T10:35:00'),
            level: 'success',
            message: 'Pixabay: Successfully fetched 500 images'
          },
          {
            id: '7',
            timestamp: new Date('2024-01-20T10:40:00'),
            level: 'info',
            message: 'Quality validation in progress - 1950/3000 images processed'
          }
        ]
      })

      setLoading(false)
    }, 1000)

    // TODO: Set up SSE connection for real-time updates
    // const eventSource = new EventSource(`/api/jobs/${jobId}/sse`)
    // eventSource.onmessage = (event) => {
    //   const data = JSON.parse(event.data)
    //   setJob(prev => ({ ...prev, ...data }))
    // }
    // return () => eventSource.close()
  }, [projectId, datasetId])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dataset...</p>
        </div>
      </div>
    )
  }

  if (!dataset) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Database className="w-16 h-16 text-muted-foreground/50 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Dataset Not Found</h2>
          <p className="text-muted-foreground mb-4">The dataset you're looking for doesn't exist.</p>
          <Button onClick={() => router.push(`/dashboard/projects/${projectId}`)}>
            Back to Project
          </Button>
        </div>
      </div>
    )
  }

  const completionRate = Math.round((dataset.imagesCollected / dataset.totalImages) * 100)

  return (
    <div className="space-y-6 mx-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/dashboard/projects/${projectId}`}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Project
              </Link>
            </Button>
            <StatusBadge status={dataset.status} />
          </div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            {dataset.name}
          </h1>
          <p className="text-base text-muted-foreground">
            Project: <Link href={`/dashboard/projects/${projectId}`} className="hover:underline font-medium">{dataset.projectName}</Link>
          </p>
          <div className="flex items-center gap-4 text-sm text-muted-foreground pt-2">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              Created {new Date(dataset.createdAt).toLocaleDateString()}
            </div>
            {dataset.completedAt && (
              <div className="flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" />
                Completed {new Date(dataset.completedAt).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {dataset.status === 'completed' && (
            <Button
              variant="outline"
              leftIcon={<Download className="w-4 h-4" />}
            >
              Download
            </Button>
          )}
          <Button
            variant="outline"
            leftIcon={<Settings className="w-4 h-4" />}
          >
            Settings
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <QuickStatsCard
          title="Images Found"
          value={dataset.imagesCollected.toLocaleString()}
          icon={ImageIcon}
          description={`of ${dataset.totalImages.toLocaleString()} target`}
          accent="blue"
        />
        <QuickStatsCard
          title="Completion"
          value={`${completionRate}%`}
          icon={Activity}
          description={dataset.status === 'processing' ? 'In progress' : 'Complete'}
          accent="yellow"
        />
        <QuickStatsCard
          title="Corrupted Images"
          value={dataset.keywords.length}
          icon={FileText}
          description="Search terms"
          accent="red"
        />
        <QuickStatsCard
          title="Validated Images"
          value={dataset.sources.length}
          icon={Database}
          description="Image sources"
          accent="green"
        />
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Progress Card */}
            <Card className="bg-card/80 backdrop-blur-md">
              <CardHeader>
                <CardTitle>Processing Progress</CardTitle>
                <CardDescription>Current status of dataset creation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {job && (
                  <JobProgress
                    status={job.status}
                    progress={job.progress}
                    totalItems={job.totalItems}
                    processedItems={job.processedItems}
                  />
                )}
                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Total Target</p>
                    <p className="text-2xl font-bold">{dataset.totalImages.toLocaleString()}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Collected</p>
                    <p className="text-2xl font-bold text-primary">{dataset.imagesCollected.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Keywords Card */}
            <Card className="bg-card/80 backdrop-blur-md">
              <CardHeader>
                <CardTitle>Search Keywords</CardTitle>
                <CardDescription>Keywords used for image crawling</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {dataset.keywords.map((keyword, index) => (
                    <Badge key={index} variant="secondary">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          
        </TabsContent>
      </Tabs>
    </div>
  )
}
