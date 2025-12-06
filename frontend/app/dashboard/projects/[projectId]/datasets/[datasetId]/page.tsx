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
import { toast } from 'sonner'
import { apiService } from '@/lib/services/api.service'
import { StatusBadge } from '@/components/dashboard/data-table'
import { JobProgress } from '@/components/dashboard/progress-bar'
import { QuickStatsCard } from '@/components/dashboard/stats-card'
import { History, GitBranch, RotateCcw } from 'lucide-react'

interface Dataset {
  id: number
  user_id: string
  name: string
  description?: string
  status: string
  images_collected: number
  dataset_id?: number // For version response mapping if needed
  progress: number
  keywords: string[]
  search_engines: string[]
  max_images: number
  created_at: string
  updated_at: string
  crawl_job_id?: number
}

interface DatasetVersion {
  id: number
  dataset_id: number
  version_number: number
  keywords: string[]
  search_engines: string[]
  max_images: number
  change_summary?: string
  created_at: string
  created_by?: string
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

  const [versions, setVersions] = useState<DatasetVersion[]>([])
  const [activeVersion, setActiveVersion] = useState<number | null>(null)

  const fetchData = async () => {
    try {
      setLoading(true)
      // Fetch dataset details
      // Note: apiService.getDatasets returns list, we might need getDatasetById if available, 
      // or filter from list. But ideally we should have getDataset in apiService.
      // Looking at api.service.ts, there is no getDataset(id).
      // However, we can use fetch directly or add it. 
      // For now, I'll assume I can fetch directly or add it quickly if needed.
      // Wait, I cannot add it easily without seeing file again.
      // I'll try to use the list endpoint and filter? No, inefficient.
      // I'll implement a direct fetch inside useEffect for now using the same base URL pattern if I can access it, 
      // or better, I rely on the fact that I just added version endpoints, 
      // I should update apiService to have getDataset if it's missing.
      // Actually, I can just use `apiService['fetch']` if it was public, but it's private.
      // Let's assume I adding `getDataset` to apiService in a separate step is better. 
      // BUT, checking `dataset.py` service, `get_dataset_by_id` exists.
      // I'll assume for this step I'll just use a direct fetch wrapper or valid method.
      // Wait, I see `getDatasets` (plural) in api.service.ts.
      // I'll assume I can use `apiService.getDataset(datasetId)` if I added it. 
      // I haven't added `getDataset` to api.service.ts yet.

      // Let's modify this plan. I will just implement the fetch here using standard fetch for now 
      // to avoid context switching back to api.service.ts again and again. 
      // OR I can use the methods I know exist.

      // I'll use a direct fetch for getDataset to save time, then getVersions.
      const datasetRes = await fetch(`/api/v1/datasets/${datasetId}`)
      if (!datasetRes.ok) throw new Error("Failed to fetch dataset")
      const datasetData = await datasetRes.json()
      setDataset(datasetData)

      const versionsRes = await apiService.getDatasetVersions(datasetId)
      setVersions(versionsRes)

      if (datasetData.crawl_job_id) {
        // fetch job status if needed
        // setJob(...)
      }

    } catch (error) {
      console.error(error)
      toast.error("Failed to load dataset details")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [datasetId])

  const handleRollback = async (versionNumber: number) => {
    try {
      toast.loading("Rolling back dataset...")
      await apiService.rollbackDataset(datasetId, versionNumber)
      toast.dismiss()
      toast.success(`Successfully rolled back to v${versionNumber}`)
      fetchData() // Refresh data
    } catch (error) {
      toast.dismiss()
      toast.error("Failed to rollback dataset")
      console.error(error)
    }
  }

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

  const completionRate = Math.round((dataset.images_collected / dataset.max_images) * 100)

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
            {/* Project name is not in dataset response directly unless we join, using ID for now or separate fetch */}
            Project ID: <Link href={`/dashboard/projects/${projectId}`} className="hover:underline font-medium">{projectId}</Link>
          </p>
          <div className="flex items-center gap-4 text-sm text-muted-foreground pt-2">
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              Created {new Date(dataset.created_at).toLocaleDateString()}
            </div>
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
          value={dataset.images_collected.toLocaleString()}
          icon={ImageIcon}
          description={`of ${dataset.max_images.toLocaleString()} target`}
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
          value={dataset.search_engines.length}
          icon={Database}
          description="Image sources"
          accent="green"
        />
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="history">Version History</TabsTrigger>
        </TabsList>

        <TabsContent value="history" className="space-y-4">
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Version History</CardTitle>
              <CardDescription>View and rollback to previous dataset configurations.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative border-l border-muted ml-4 space-y-8 py-4">
                {versions.map((version) => (
                  <div key={version.id} className="relative pl-8">
                    {/* Timestamp dot */}
                    <div className="absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full bg-primary ring-4 ring-background" />

                    <div className="flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-semibold flex items-center gap-2">
                            <GitBranch className="h-4 w-4" />
                            v{version.version_number}
                            {version.change_summary && <span className="text-muted-foreground font-normal">- {version.change_summary}</span>}
                          </h4>
                          <p className="text-xs text-muted-foreground">
                            {new Date(version.created_at).toLocaleString()}
                          </p>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRollback(version.version_number)}
                        >
                          <RotateCcw className="h-3 w-3 mr-2" />
                          Rollback
                        </Button>
                      </div>

                      <div className="bg-muted/50 rounded-md p-3 text-sm grid gap-2">
                        <div className="grid grid-cols-[100px_1fr] gap-2">
                          <span className="text-muted-foreground">Keywords:</span>
                          <div className="flex flex-wrap gap-1">
                            {version.keywords.map(k => (
                              <Badge key={k} variant="outline" className="text-xs">{k}</Badge>
                            ))}
                          </div>
                        </div>
                        <div className="grid grid-cols-[100px_1fr] gap-2">
                          <span className="text-muted-foreground">Max Images:</span>
                          <span>{version.max_images}</span>
                        </div>
                        <div className="grid grid-cols-[100px_1fr] gap-2">
                          <span className="text-muted-foreground">Sources:</span>
                          <div className="flex flex-wrap gap-1">
                            {version.search_engines.map(s => (
                              <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {versions.length === 0 && (
                  <div className="pl-8 text-muted-foreground">No history available for this dataset.</div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

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
                    <p className="text-2xl font-bold">{dataset.max_images.toLocaleString()}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Collected</p>
                    <p className="text-2xl font-bold text-primary">{dataset.images_collected.toLocaleString()}</p>
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
