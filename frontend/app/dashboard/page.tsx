'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Activity,
  Database,
  FolderOpen,
  Plus,
  HardDrive,
  Zap,
  Image,
  Clock,
  BarChart3,
  ChevronRight
} from 'lucide-react'

import { useAuth } from '@/lib/auth/hooks'
import { useProjects, useDatasets, useJobs, useActivities, useDashboardStats, type Job as HookJob, type Activity as HookActivity } from '@/lib/hooks'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { StatsCard } from '@/components/dashboard/stats-card'
import { DataTable, StatusBadge } from '@/components/dashboard/data-table'
import { JobProgress } from '@/components/dashboard/progress-bar'
import { ActivityTimeline, type ActivityItem } from '@/components/dashboard/activity-timeline'
import { DashboardSkeleton } from '@/components/dashboard/dashboard-skeleton'

// Type definitions
import type { Project as DBProject } from '@/lib/db/schema'

interface Project extends DBProject {
  datasetsCount?: number
  totalImages?: number
}

interface Dataset {
  id: string
  projectId: string
  projectName: string
  name: string
  status: 'active' | 'processing' | 'completed' | 'failed'
  imageCount: number
  imagesCollected: number
  totalImages: number
  createdAt: Date
}

interface Job extends HookJob {
  datasetId?: string
  datasetName?: string
  totalItems?: number
  processedItems?: number
  startedAt?: Date
}

// Helper function to transform Activity to ActivityItem
function transformActivity(activity: HookActivity): ActivityItem {
  // Map activity type to a more specific type for the timeline
  const typeMap: Record<string, ActivityItem['type']> = {
    'CREATE_PROJECT': 'project_created',
    'START_CRAWL_JOB': 'job_started',
    'COMPLETE_CRAWL_JOB': 'job_completed',
    'DOWNLOAD_IMAGES': 'dataset_downloaded',
  }

  return {
    id: activity.id,
    type: (typeMap[activity.type] || 'settings_updated') as ActivityItem['type'],
    title: activity.message,
    description: undefined,
    timestamp: activity.timestamp,
    user: activity.userId,
    metadata: undefined,
  }
}

export default function DashboardPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')

  // Use custom hooks for data fetching
  const { projects, loading: projectsLoading } = useProjects(user?.id || '')
  const { datasets: hookDatasets, loading: datasetsLoading } = useDatasets()
  const { jobs: hookJobs, loading: jobsLoading } = useJobs()
  const { activities: hookActivities, loading: activitiesLoading } = useActivities()
  const { stats, loading: statsLoading } = useDashboardStats()

  // Transform data to match component expectations
  const jobs = hookJobs as Job[]
  const activities = hookActivities.map(transformActivity)
  
  // Mock datasets with proper structure (until API is implemented)
  const datasets = hookDatasets.map(ds => ({
    ...ds,
    projectName: 'Project Name', // TODO: Join with projects
    imagesCollected: ds.imageCount || 0,
    totalImages: ds.imageCount || 0,
  }))

  const loading = projectsLoading || datasetsLoading || jobsLoading || activitiesLoading || statsLoading

  if (loading) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6 mx-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            {user?.profile?.fullName ? `Welcome back, ${user.profile.fullName}!` : 'Dashboard Overview'}
          </h1>
          <p className="text-base text-muted-foreground">
            Manage your AI-powered image dataset projects
          </p>
        </div>
        <Button
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => router.push('/dashboard/projects/new')}
        >
          New Project
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <StatsCard
          title="Total Projects"
          value={stats?.totalProjects || 0}
          description="Active projects"
          icon={FolderOpen}
          trend={{ value: 12, label: 'from last month' }}
          iconColor="text-blue-500"
        />
        <StatsCard
          title="Active Jobs"
          value={stats?.activeJobs || 0}
          description="Currently processing"
          icon={Activity}
          iconColor="text-yellow-500"
        />
        <StatsCard
          title="Total Datasets"
          value={stats?.totalDatasets || 0}
          description="Across all projects"
          icon={Database}
          trend={{ value: 8, label: 'this week' }}
          iconColor="text-purple-500"
        />
        <StatsCard
          title="Images Collected"
          value={(stats?.totalImages || 0).toLocaleString()}
          description="Total processed"
          icon={Image}
          trend={{ value: 25, label: 'from last week' }}
          iconColor="text-green-500"
        />
        <StatsCard
          title="Storage Used"
          value={stats?.storageUsed || '0 GB'}
          description="Total storage"
          icon={HardDrive}
          iconColor="text-orange-500"
        />
        <StatsCard
          title="Processing Speed"
          value={`${stats?.processingSpeed || 0}/min`}
          description="Average speed"
          icon={Zap}
          trend={{ value: 5, label: 'improvement' }}
          iconColor="text-cyan-500"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="datasets">Datasets</TabsTrigger>
          <TabsTrigger value="jobs">Jobs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Projects Table */}
            <Card className="bg-card/80 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Recent Projects</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setActiveTab('projects')}
                  aria-label="View all projects"
                >
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                <DataTable
                  columns={[
                    {
                      key: 'name',
                      header: 'Name',
                      cell: (project: Project) => (
                        <div>
                          <p className="font-medium">{project.name}</p>
                          <p className="text-xs text-muted-foreground">{project.description}</p>
                        </div>
                      )
                    },
                    {
                      key: 'datasetsCount',
                      header: 'Datasets',
                      cell: (project: Project) => (
                        <Badge variant="outline">{project.datasetsCount || 0}</Badge>
                      )
                    },
                    {
                      key: 'status',
                      header: 'Status',
                      cell: (project: Project) => <StatusBadge status={project.status} />
                    }
                  ]}
                  data={projects.slice(0, 3)}
                  onView={(project) => router.push(`/dashboard/projects/${project.id}`)}
                  onEdit={(project) => router.push(`/dashboard/projects/${project.id}/edit`)}
                />
              </CardContent>
            </Card>

            {/* Active Jobs */}
            <Card className="bg-card/80 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Active Jobs</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setActiveTab('jobs')}
                  aria-label="View all jobs"
                >
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                {jobs.filter(job => job.status === 'running').length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Clock className="size-12 mx-auto mb-4 opacity-50" />
                    <p>No active jobs</p>
                    <p className="text-sm">Jobs will appear here when processing</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {jobs.filter(job => job.status === 'running').map(job => (
                      <div key={job.id} className="space-y-2 p-3 rounded-lg border bg-muted/30">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium text-sm">{job.datasetName || job.name || 'Unnamed Job'}</p>
                            <p className="text-xs text-muted-foreground">Job #{job.id}</p>
                          </div>
                          <StatusBadge status={job.status} />
                        </div>
                        <JobProgress
                          status={job.status}
                          progress={job.progress}
                          totalItems={job.totalItems || 0}
                          processedItems={job.processedItems || 0}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Activity Timeline and Quick Actions */}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ActivityTimeline activities={activities} />
            </div>

            <Card className="bg-card/80 backdrop-blur-md">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  className="w-full justify-between group"
                  size="lg"
                  variant="outline"
                  leftIcon={<Plus className="w-4 h-4" />}
                  rightIcon={<ChevronRight className="w-4 h-4 opacity-70 transition-transform duration-200 group-hover:translate-x-0.5" />}
                  onClick={() => router.push('/dashboard/projects/new')}
                  aria-label="Create new project"
                >
                  Create New Project
                </Button>
                <Button
                  className="w-full justify-between group"
                  size="lg"
                  variant="outline"
                  leftIcon={<Database className="w-4 h-4" />}
                  rightIcon={<ChevronRight className="w-4 h-4 opacity-70 transition-transform duration-200 group-hover:translate-x-0.5" />}
                  onClick={() => setActiveTab('datasets')}
                  aria-label="Browse datasets"
                >
                  Browse Datasets
                </Button>
                <Button
                  className="w-full justify-between group"
                  size="lg"
                  variant="outline"
                  leftIcon={<BarChart3 className="w-4 h-4" />}
                  rightIcon={<ChevronRight className="w-4 h-4 opacity-70 transition-transform duration-200 group-hover:translate-x-0.5" />}
                  onClick={() => router.push('/dashboard/analytics')}
                  aria-label="View analytics"
                >
                  View Analytics
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="projects">
          <Card>
            <CardHeader>
              <CardTitle>All Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={[
                  {
                    key: 'name',
                    header: 'Name',
                    cell: (project: Project) => (
                      <div>
                        <p className="font-medium">{project.name}</p>
                        <p className="text-xs text-muted-foreground">{project.description}</p>
                      </div>
                    )
                  },
                  {
                    key: 'datasetsCount',
                    header: 'Datasets',
                    cell: (project: Project) => (
                      <Badge variant="outline">{project.datasetsCount || 0}</Badge>
                    )
                  },
                  {
                    key: 'status',
                    header: 'Status',
                    cell: (project: Project) => <StatusBadge status={project.status} />
                  },
                  {
                    key: 'createdAt',
                    header: 'Created',
                    cell: (project: Project) => new Date(project.createdAt).toLocaleDateString()
                  }
                ]}
                data={projects}
                onView={(project) => router.push(`/dashboard/projects/${project.id}`)}
                onEdit={(project) => router.push(`/dashboard/projects/${project.id}/edit`)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="datasets">
          <Card>
            <CardHeader>
              <CardTitle>All Datasets</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={[
                  {
                    key: 'name',
                    header: 'Name',
                    cell: (dataset: Dataset) => (
                      <div>
                        <p className="font-medium">{dataset.name}</p>
                        <p className="text-xs text-muted-foreground">{dataset.projectName}</p>
                      </div>
                    )
                  },
                  {
                    key: 'status',
                    header: 'Status',
                    cell: (dataset: Dataset) => <StatusBadge status={dataset.status} />
                  },
                  {
                    key: 'imagesCollected',
                    header: 'Images',
                    cell: (dataset: Dataset) => (
                      <span>{dataset.imagesCollected} / {dataset.totalImages}</span>
                    )
                  },
                  {
                    key: 'createdAt',
                    header: 'Created',
                    cell: (dataset: Dataset) => new Date(dataset.createdAt).toLocaleDateString()
                  }
                ]}
                data={datasets}
                onView={(dataset) => router.push(`/dashboard/datasets/${dataset.id}`)}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="jobs">
          <Card>
            <CardHeader>
              <CardTitle>Processing Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {jobs.map(job => (
                  <div key={job.id} className="p-4 rounded-lg border bg-card">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h4 className="font-medium">{job.datasetName || job.name || 'Unnamed Job'}</h4>
                        <p className="text-sm text-muted-foreground">Job ID: {job.id}</p>
                      </div>
                      <StatusBadge status={job.status} />
                    </div>
                    <JobProgress
                      status={job.status}
                      progress={job.progress}
                      totalItems={job.totalItems || 0}
                      processedItems={job.processedItems || 0}
                    />
                    <div className="mt-4 flex justify-between text-sm text-muted-foreground">
                      <span>Started: {job.startedAt ? new Date(job.startedAt).toLocaleString() : '-'}</span>
                      <span>{job.processedItems || 0} / {job.totalItems || 0} items</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}