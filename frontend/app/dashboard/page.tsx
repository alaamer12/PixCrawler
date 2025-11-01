'use client'

import { useState, useEffect, memo } from 'react'
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
  BarChart3
} from 'lucide-react'

import { useAuth } from '@/lib/auth/hooks'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { StatsCard } from '@/components/dashboard/stats-card'
import { DataTable, Column, StatusBadge } from '@/components/dashboard/data-table'
import { JobProgress } from '@/components/dashboard/progress-bar'
import { ActivityTimeline, ActivityItem } from '@/components/dashboard/activity-timeline'
import { DashboardSkeleton } from '@/components/dashboard/dashboard-skeleton'

// Type definitions
interface Project {
  id: string
  name: string
  description?: string
  datasetsCount: number
  totalImages: number
  status: 'active' | 'archived'
  createdAt: Date
  updatedAt: Date
}

interface Dataset {
  id: string
  projectId: string
  projectName: string
  name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  imagesCollected: number
  totalImages: number
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

function DashboardPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  
  // Mock data - replace with actual API calls
  const [projects, setProjects] = useState<Project[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [stats, setStats] = useState({
    totalProjects: 0,
    activeJobs: 0,
    totalDatasets: 0,
    totalImages: 0,
    storageUsed: '0 MB',
    processingSpeed: '0'
  })

  useEffect(() => {
    // Simulate loading data
    setTimeout(() => {
      // Mock data for demonstration
      setStats({
        totalProjects: 3,
        activeJobs: 2,
        totalDatasets: 7,
        totalImages: 15420,
        storageUsed: '2.4 GB',
        processingSpeed: '120'
      })
      
      setProjects([
        {
          id: '1',
          name: 'Wildlife Dataset',
          description: 'African wildlife images for conservation AI',
          datasetsCount: 3,
          totalImages: 5420,
          status: 'active',
          createdAt: new Date('2024-01-15'),
          updatedAt: new Date('2024-01-20')
        },
        {
          id: '2',
          name: 'Urban Architecture',
          description: 'Modern building facades and structures',
          datasetsCount: 2,
          totalImages: 8200,
          status: 'active',
          createdAt: new Date('2024-01-10'),
          updatedAt: new Date('2024-01-18')
        },
        {
          id: '3',
          name: 'Medical Imaging',
          description: 'X-ray and MRI scan datasets',
          datasetsCount: 2,
          totalImages: 1800,
          status: 'active',
          createdAt: new Date('2024-01-05'),
          updatedAt: new Date('2024-01-19')
        }
      ])
      
      setDatasets([
        {
          id: '1',
          projectId: '1',
          projectName: 'Wildlife Dataset',
          name: 'African Elephants',
          status: 'completed',
          imagesCollected: 2100,
          totalImages: 2100,
          createdAt: new Date('2024-01-15')
        },
        {
          id: '2',
          projectId: '1',
          projectName: 'Wildlife Dataset',
          name: 'Lions and Tigers',
          status: 'processing',
          imagesCollected: 1520,
          totalImages: 3000,
          createdAt: new Date('2024-01-18')
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
        },
        {
          id: '2',
          datasetId: '3',
          datasetName: 'Modern Skyscrapers',
          status: 'running',
          progress: 32,
          totalItems: 5000,
          processedItems: 1600,
          startedAt: new Date('2024-01-20T11:30:00')
        }
      ])
      
      setActivities([
        {
          id: '1',
          type: 'job_started',
          title: 'Job started for Lions and Tigers',
          description: 'Processing 3000 images from multiple sources',
          timestamp: new Date('2024-01-20T10:00:00'),
          user: user?.email
        },
        {
          id: '2',
          type: 'dataset_created',
          title: 'New dataset created',
          description: 'Modern Skyscrapers dataset added to Urban Architecture',
          timestamp: new Date('2024-01-20T09:30:00'),
          user: user?.email
        },
        {
          id: '3',
          type: 'job_completed',
          title: 'Job completed successfully',
          description: 'African Elephants dataset processing finished',
          timestamp: new Date('2024-01-19T18:45:00'),
          user: user?.email,
          metadata: { images: 2100, duration: '2h 15m' }
        }
      ])
      
      setLoading(false)
    }, 1000)
  }, [])

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
          value={stats.totalProjects}
          description="Active projects"
          icon={FolderOpen}
          trend={{ value: 12, label: 'from last month' }}
          iconColor="text-blue-500"
        />
        <StatsCard
          title="Active Jobs"
          value={stats.activeJobs}
          description="Currently processing"
          icon={Activity}
          iconColor="text-yellow-500"
        />
        <StatsCard
          title="Total Datasets"
          value={stats.totalDatasets}
          description="Across all projects"
          icon={Database}
          trend={{ value: 8, label: 'this week' }}
          iconColor="text-purple-500"
        />
        <StatsCard
          title="Images Collected"
          value={stats.totalImages.toLocaleString()}
          description="Total processed"
          icon={Image}
          trend={{ value: 25, label: 'from last week' }}
          iconColor="text-green-500"
        />
        <StatsCard
          title="Storage Used"
          value={stats.storageUsed}
          description="Total storage"
          icon={HardDrive}
          iconColor="text-orange-500"
        />
        <StatsCard
          title="Processing Speed"
          value={`${stats.processingSpeed}/min`}
          description="Average speed"
          icon={Zap}
          trend={{ value: 5, label: 'improvement' }}
          iconColor="text-cyan-500"
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full max-w-[400px] grid-cols-4">
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
                        <Badge variant="outline">{project.datasetsCount}</Badge>
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
                            <p className="font-medium text-sm">{job.datasetName}</p>
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
                  className="w-full justify-start"
                  variant="outline"
                  leftIcon={<Plus className="w-4 h-4" />}
                  onClick={() => router.push('/dashboard/projects/new')}
                  aria-label="Create new project"
                >
                  Create New Project
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  leftIcon={<Database className="w-4 h-4" />}
                  onClick={() => router.push('/dashboard/projects')}
                  aria-label="Browse all projects"
                >
                  Browse Projects
                </Button>
                <Button
                  className="w-full justify-start"
                  variant="outline"
                  leftIcon={<BarChart3 className="w-4 h-4" />}
                  onClick={() => router.push('/dashboard/analytics')}
                  aria-label="View analytics dashboard"
                >
                  View Analytics
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="projects" className="space-y-4">
          <ProjectsTable projects={projects} />
        </TabsContent>

        <TabsContent value="datasets" className="space-y-4">
          <DatasetsTable datasets={datasets} />
        </TabsContent>

        <TabsContent value="jobs" className="space-y-4">
          <JobsTable jobs={jobs} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default memo(DashboardPage)
DashboardPage.displayName = 'DashboardPage'

// Component for Projects Table
const ProjectsTable = memo(function ProjectsTable({ projects }: { projects: Project[] }) {
  const router = useRouter()
  
  const columns: Column<Project>[] = [
    { 
      key: 'name', 
      header: 'Project Name',
      cell: (project) => (
        <div>
          <p className="font-medium">{project.name}</p>
          {project.description && (
            <p className="text-xs text-muted-foreground">{project.description}</p>
          )}
        </div>
      )
    },
    { 
      key: 'datasetsCount', 
      header: 'Datasets',
      cell: (project) => (
        <Badge variant="outline">{project.datasetsCount} datasets</Badge>
      )
    },
    { 
      key: 'totalImages', 
      header: 'Total Images',
      cell: (project) => project.totalImages.toLocaleString()
    },
    { 
      key: 'status', 
      header: 'Status',
      cell: (project) => <StatusBadge status={project.status} />
    },
    { 
      key: 'createdAt', 
      header: 'Created',
      cell: (project) => new Date(project.createdAt).toLocaleDateString()
    }
  ]

  return (
    <Card className="bg-card/80 backdrop-blur-md">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>All Projects</CardTitle>
        <Button 
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => router.push('/dashboard/projects/new')}
        >
          New Project
        </Button>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={projects}
          onView={(project) => router.push(`/dashboard/projects/${project.id}`)}
          onEdit={(project) => router.push(`/dashboard/projects/${project.id}/edit`)}
          actions={[
            {
              label: 'Add Dataset',
              icon: <Database className="mr-2 h-4 w-4" />,
              onClick: (project) => router.push(`/dashboard/projects/${project.id}/datasets/new`)
            }
          ]}
        />
      </CardContent>
    </Card>
  )
})
ProjectsTable.displayName = 'ProjectsTable'

// Component for Datasets Table
const DatasetsTable = memo(function DatasetsTable({ datasets }: { datasets: Dataset[] }) {
  const router = useRouter()
  
  const columns: Column<Dataset>[] = [
    { 
      key: 'name', 
      header: 'Dataset Name',
      cell: (dataset) => (
        <div>
          <p className="font-medium">{dataset.name}</p>
          <p className="text-xs text-muted-foreground">{dataset.projectName}</p>
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
        <div className="w-32">
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
      key: 'createdAt', 
      header: 'Created',
      cell: (dataset) => new Date(dataset.createdAt).toLocaleDateString()
    }
  ]

  return (
    <Card className="bg-card/80 backdrop-blur-md">
      <CardHeader>
        <CardTitle>All Datasets</CardTitle>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={datasets}
          onView={(dataset) => router.push(`/dashboard/projects/${dataset.projectId}/datasets/${dataset.id}`)}
        />
      </CardContent>
    </Card>
  )
})
DatasetsTable.displayName = 'DatasetsTable'

// Component for Jobs Table
const JobsTable = memo(function JobsTable({ jobs }: { jobs: Job[] }) {
  const columns: Column<Job>[] = [
    { 
      key: 'id', 
      header: 'Job ID',
      cell: (job) => <code className="text-xs">#{job.id}</code>
    },
    { 
      key: 'datasetName', 
      header: 'Dataset'
    },
    { 
      key: 'status', 
      header: 'Status',
      cell: (job) => <StatusBadge status={job.status} />
    },
    { 
      key: 'progress', 
      header: 'Progress',
      cell: (job) => (
        <div className="w-40">
          <JobProgress
            status={job.status}
            progress={job.progress}
            totalItems={job.totalItems}
            processedItems={job.processedItems}
          />
        </div>
      )
    },
    { 
      key: 'startedAt', 
      header: 'Started',
      cell: (job) => job.startedAt ? new Date(job.startedAt).toLocaleString() : '-'
    }
  ]

  return (
    <Card className="bg-card/80 backdrop-blur-md">
      <CardHeader>
        <CardTitle>All Jobs</CardTitle>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={jobs}
          actions={[
            {
              label: 'View Logs',
              icon: <Activity className="mr-2 h-4 w-4" />,
              onClick: (job) => {
                // TODO: Implement view logs functionality
                console.info('View logs for job:', job.id)
              }
            }
          ]}
        />
      </CardContent>
    </Card>
  )
})
JobsTable.displayName = 'JobsTable'
