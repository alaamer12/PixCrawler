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
  Trash2,
  Play,
  Pause,
  RotateCw,
  Image as ImageIcon,
  Activity,
  Calendar,
  Database,
  FileText,
  CheckCircle2,
  XCircle,
  AlertCircle
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
          title="Images Collected"
          value={dataset.imagesCollected.toLocaleString()}
          icon={ImageIcon}
          description={`of ${dataset.totalImages.toLocaleString()} target`}
        />
        <QuickStatsCard
          title="Completion"
          value={`${completionRate}%`}
          icon={Activity}
          description={dataset.status === 'processing' ? 'In progress' : 'Complete'}
        />
        <QuickStatsCard
          title="Keywords"
          value={dataset.keywords.length}
          icon={FileText}
          description="Search terms"
        />
        <QuickStatsCard
          title="Sources"
          value={dataset.sources.length}
          icon={Database}
          description="Image sources"
        />
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="job">Job Status</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
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

          {/* Sources Card */}
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Image Sources</CardTitle>
              <CardDescription>Platforms used for image collection</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                {dataset.sources.map((source) => (
                  <div key={source} className="flex items-center gap-2 px-4 py-2 rounded-lg border bg-muted/30">
                    <Database className="w-4 h-4 text-primary" />
                    <span className="font-medium capitalize">{source}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="job" className="space-y-4">
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Job Status</CardTitle>
                <CardDescription>Real-time processing information</CardDescription>
              </div>
              {job && job.status === 'running' && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" leftIcon={<Pause className="w-4 h-4" />}>
                    Pause
                  </Button>
                  <Button variant="outline" size="sm" leftIcon={<RotateCw className="w-4 h-4" />}>
                    Restart
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent>
              {job ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Job ID</p>
                      <code className="text-sm font-mono">{job.id}</code>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Status</p>
                      <StatusBadge status={job.status} />
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Started</p>
                      <p className="text-sm">{job.startedAt ? new Date(job.startedAt).toLocaleString() : '-'}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">Completed</p>
                      <p className="text-sm">{job.completedAt ? new Date(job.completedAt).toLocaleString() : '-'}</p>
                    </div>
                  </div>

                  <JobProgress
                    status={job.status}
                    progress={job.progress}
                    totalItems={job.totalItems}
                    processedItems={job.processedItems}
                  />
                </div>
              ) : (
                <div className="text-center py-8">
                  <Activity className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No job information available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Processing Logs</CardTitle>
              <CardDescription>Real-time logs from the crawling job</CardDescription>
            </CardHeader>
            <CardContent>
              {job && job.logs.length > 0 ? (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {job.logs.map((log) => (
                    <div key={log.id} className="flex gap-3 p-3 rounded-lg border bg-muted/20">
                      <div className="flex-shrink-0 mt-0.5">
                        {log.level === 'success' && <CheckCircle2 className="w-4 h-4 text-green-500" />}
                        {log.level === 'error' && <XCircle className="w-4 h-4 text-destructive" />}
                        {log.level === 'warning' && <AlertCircle className="w-4 h-4 text-yellow-500" />}
                        {log.level === 'info' && <Activity className="w-4 h-4 text-blue-500" />}
                      </div>
                      <div className="flex-1 space-y-1">
                        <p className="text-sm">{log.message}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No logs available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="config" className="space-y-4">
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Dataset Configuration</CardTitle>
              <CardDescription>Settings used for this dataset</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b border-border/50">
                    <span className="text-sm text-muted-foreground">AI Keyword Expansion</span>
                    <Badge variant={dataset.config.aiExpansion ? 'default' : 'outline'}>
                      {dataset.config.aiExpansion ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-border/50">
                    <span className="text-sm text-muted-foreground">Deduplication Level</span>
                    <Badge variant="outline" className="capitalize">{dataset.config.deduplicationLevel}</Badge>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-border/50">
                    <span className="text-sm text-muted-foreground">Min Image Size</span>
                    <span className="text-sm font-medium">{dataset.config.minImageSize}px</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b border-border/50">
                    <span className="text-sm text-muted-foreground">Image Format</span>
                    <Badge variant="outline" className="uppercase">{dataset.config.imageFormat}</Badge>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-border/50">
                    <span className="text-sm text-muted-foreground">Safe Search</span>
                    <Badge variant={dataset.config.safeSearch ? 'default' : 'outline'}>
                      {dataset.config.safeSearch ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
