'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  ArrowLeft,
  Database,
  Plus,
  Settings,
  Trash2,
  Edit,
  Download,
  FolderOpen,
  Image as ImageIcon,
  Activity,
  Calendar,
  BarChart3
} from 'lucide-react'
import Link from 'next/link'
import { DataTable, Column, StatusBadge } from '@/components/dashboard/data-table'
import { JobProgress } from '@/components/dashboard/progress-bar'
import { ActivityTimeline, ActivityItem } from '@/components/dashboard/activity-timeline'
import { QuickStatsCard } from '@/components/dashboard/stats-card'

interface Project {
  id: string
  name: string
  description?: string
  status: 'active' | 'archived'
  createdAt: Date
  updatedAt: Date
}

interface Dataset {
  id: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  imagesCollected: number
  totalImages: number
  keywords: string[]
  sources: string[]
  createdAt: Date
}

interface Job {
  id: string
  datasetId: string
  datasetName: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused'
  progress: number
  totalItems: number
  processedItems: number
  startedAt?: Date
  completedAt?: Date
}

export default function ProjectViewPage() {
  const router = useRouter()
  const params = useParams()
  const projectId = params.projectId as string

  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('datasets')
  const [project, setProject] = useState<Project | null>(null)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [activities, setActivities] = useState<ActivityItem[]>([])

  useEffect(() => {
    // TODO: Fetch project data from API
    // Simulate API call
    setTimeout(() => {
      setProject({
        id: projectId,
        name: 'Wildlife Conservation Dataset',
        description: 'African wildlife images for conservation AI and research purposes',
        status: 'active',
        createdAt: new Date('2024-01-15'),
        updatedAt: new Date('2024-01-20')
      })

      setDatasets([
        {
          id: '1',
          name: 'African Elephants',
          status: 'completed',
          imagesCollected: 2100,
          totalImages: 2100,
          keywords: ['african elephant', 'elephant herd', 'savanna elephant'],
          sources: ['google', 'unsplash'],
          createdAt: new Date('2024-01-15')
        },
        {
          id: '2',
          name: 'Lions and Tigers',
          status: 'processing',
          imagesCollected: 1520,
          totalImages: 3000,
          keywords: ['african lion', 'lion pride', 'bengal tiger'],
          sources: ['google', 'bing', 'pixabay'],
          createdAt: new Date('2024-01-18')
        },
        {
          id: '3',
          name: 'Safari Wildlife',
          status: 'pending',
          imagesCollected: 0,
          totalImages: 1500,
          keywords: ['safari animals', 'wild animals', 'african wildlife'],
          sources: ['google'],
          createdAt: new Date('2024-01-20')
        }
      ])

      setJobs([
        {
          id: '1',
          datasetId: '2',
          datasetName: 'Lions and Tigers',
          status: 'running',
          progress: 65,
          totalItems: 3000,
          processedItems: 1950,
          startedAt: new Date('2024-01-20T10:00:00')
        }
      ])

      setActivities([
        {
          id: '1',
          type: 'job_started',
          title: 'Processing started for Lions and Tigers',
          description: 'Crawling 3000 images from 3 sources',
          timestamp: new Date('2024-01-20T10:00:00')
        },
        {
          id: '2',
          type: 'dataset_created',
          title: 'New dataset created',
          description: 'Safari Wildlife dataset added',
          timestamp: new Date('2024-01-20T09:30:00')
        },
        {
          id: '3',
          type: 'job_completed',
          title: 'Processing completed',
          description: 'African Elephants dataset finished successfully',
          timestamp: new Date('2024-01-19T18:45:00'),
          metadata: { images: 2100, duration: '2h 15m' }
        }
      ])

      setLoading(false)
    }, 1000)
  }, [projectId])

  const totalImages = datasets.reduce((sum, ds) => sum + ds.imagesCollected, 0)
  const completedDatasets = datasets.filter(ds => ds.status === 'completed').length
  const activeJobs = jobs.filter(j => j.status === 'running').length

  const datasetColumns: Column<Dataset>[] = [
    {
      key: 'name',
      header: 'Dataset Name',
      cell: (dataset) => (
        <div>
          <p className="font-medium">{dataset.name}</p>
          <p className="text-xs text-muted-foreground">
            {dataset.keywords.slice(0, 2).join(', ')}
            {dataset.keywords.length > 2 && ` +${dataset.keywords.length - 2} more`}
          </p>
        </div>
      )
    },
    {
      key: 'status',
      header: 'Status',
      cell: (dataset) => <StatusBadge status={dataset.status} />
    },
    {
      key: 'progress',
      header: 'Progress',
      cell: (dataset) => (
        <div className="w-40">
          <JobProgress
            status={dataset.status as any}
            progress={(dataset.imagesCollected / dataset.totalImages) * 100}
            totalItems={dataset.totalImages}
            processedItems={dataset.imagesCollected}
          />
        </div>
      )
    },
    {
      key: 'sources',
      header: 'Sources',
      cell: (dataset) => (
        <div className="flex gap-1">
          {dataset.sources.map(source => (
            <Badge key={source} variant="outline" className="text-xs">
              {source}
            </Badge>
          ))}
        </div>
      )
    },
    {
      key: 'createdAt',
      header: 'Created',
      cell: (dataset) => new Date(dataset.createdAt).toLocaleDateString()
    }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading project...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <FolderOpen className="w-16 h-16 text-muted-foreground/50 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Project Not Found</h2>
          <p className="text-muted-foreground mb-4">The project you're looking for doesn't exist.</p>
          <Button onClick={() => router.push('/dashboard')}>
            Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 mx-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/dashboard">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Link>
            </Button>
            <StatusBadge status={project.status} />
          </div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            {project.name}
          </h1>
          {project.description && (
            <p className="text-base text-muted-foreground max-w-3xl">
              {project.description}
            </p>
          )}
          <div className="flex items-center gap-4 text-sm text-muted-foreground pt-2">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              Created {new Date(project.createdAt).toLocaleDateString()}
            </div>
            <div className="flex items-center gap-1">
              <Activity className="w-4 h-4" />
              Updated {new Date(project.updatedAt).toLocaleDateString()}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            leftIcon={<Settings className="w-4 h-4" />}
            onClick={() => router.push(`/dashboard/projects/${projectId}/settings`)}
          >
            Settings
          </Button>
          <Button
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => router.push(`/dashboard/projects/${projectId}/datasets/new`)}
          >
            New Dataset
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <QuickStatsCard
          title="Total Datasets"
          value={datasets.length}
          icon={Database}
          description={`${completedDatasets} completed`}
        />
        <QuickStatsCard
          title="Total Images"
          value={totalImages.toLocaleString()}
          icon={ImageIcon}
          description="Across all datasets"
        />
        <QuickStatsCard
          title="Active Jobs"
          value={activeJobs}
          icon={Activity}
          description={activeJobs > 0 ? 'Currently processing' : 'No active jobs'}
        />
        <QuickStatsCard
          title="Completion Rate"
          value={`${Math.round((completedDatasets / datasets.length) * 100)}%`}
          icon={BarChart3}
          description={`${completedDatasets}/${datasets.length} datasets`}
        />
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="datasets">Datasets</TabsTrigger>
          <TabsTrigger value="jobs">Jobs</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="datasets" className="space-y-4">
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Datasets</CardTitle>
                <CardDescription>
                  Manage your image datasets within this project
                </CardDescription>
              </div>
              <Button
                leftIcon={<Plus className="w-4 h-4" />}
                onClick={() => router.push(`/dashboard/projects/${projectId}/datasets/new`)}
              >
                Create Dataset
              </Button>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={datasetColumns}
                data={datasets}
                onView={(dataset) => router.push(`/dashboard/projects/${projectId}/datasets/${dataset.id}`)}
                onEdit={(dataset) => router.push(`/dashboard/projects/${projectId}/datasets/${dataset.id}/edit`)}
                onDelete={(dataset) => {
                  // TODO: Implement delete confirmation
                  console.log('Delete dataset:', dataset.id)
                }}
                actions={[
                  {
                    label: 'Download',
                    icon: <Download className="mr-2 h-4 w-4" />,
                    onClick: (dataset) => console.log('Download dataset:', dataset.id)
                  }
                ]}
                emptyMessage="No datasets yet. Create your first dataset to get started."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="jobs" className="space-y-4">
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Processing Jobs</CardTitle>
              <CardDescription>
                Track the status of your dataset processing jobs
              </CardDescription>
            </CardHeader>
            <CardContent>
              {jobs.length === 0 ? (
                <div className="text-center py-12">
                  <Activity className="w-16 h-16 text-muted-foreground/50 mx-auto mb-4" />
                  <p className="text-muted-foreground">No jobs running</p>
                  <p className="text-sm text-muted-foreground/70 mt-1">
                    Jobs will appear here when datasets are being processed
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {jobs.map(job => (
                    <div key={job.id} className="p-4 rounded-lg border bg-muted/30">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <p className="font-medium">{job.datasetName}</p>
                          <p className="text-xs text-muted-foreground">Job #{job.id}</p>
                        </div>
                        <StatusBadge status={job.status} />
                      </div>
                      <JobProgress
                        status={job.status}
                        progress={job.progress}
                        totalItems={job.totalItems}
                        processedItems={job.processedItems}
                      />
                      {job.startedAt && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Started {new Date(job.startedAt).toLocaleString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <ActivityTimeline activities={activities} maxItems={20} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
