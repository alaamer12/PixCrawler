'use client'

import { useState } from 'react'
import { 
  BarChart3, 
  FileImage, 
  FolderOpen, 
  Settings, 
  FileText, 
  TrendingUp,
  Download,
  RotateCcw,
  Grid3X3,
  List,
  Search,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { 
  Sidebar,
  SidebarContent,
  SidebarProvider,
  SidebarTrigger,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarSeparator
} from '@/components/ui/sidebar'
import { cn } from '@/lib/utils'
import { DatasetTopBar } from '@/components/dataset/dashboard/dataset-top-bar'
import { DatasetFilesystem } from '@/components/dataset/dashboard/dataset-filesystem'  
import { DatasetGallery } from '@/components/dataset/dashboard/dataset-gallery'
import { DatasetOverview } from '@/components/dataset/dashboard/dataset-overview'
import { DatasetSettings } from '@/components/dataset/dashboard/dataset-settings'

interface DatasetDashboardProps {
  datasetId: string
}

type TabType = 'overview' | 'gallery' | 'filesystem' | 'settings' | 'logs' | 'analytics'

const sidebarItems = [
  { id: 'overview', icon: BarChart3, label: 'Overview' },
  { id: 'gallery', icon: FileImage, label: 'Gallery' },
  { id: 'filesystem', icon: FolderOpen, label: 'Files' },
  { id: 'settings', icon: Settings, label: 'Settings' },
  { id: 'logs', icon: FileText, label: 'Logs' },
  { id: 'analytics', icon: TrendingUp, label: 'Analytics' },
] as const

export function DatasetDashboard({ datasetId }: DatasetDashboardProps) {
  const [activeTab, setActiveTab] = useState<TabType>('gallery')
  const [filesystemCollapsed, setFilesystemCollapsed] = useState(false)

  // Mock dataset data
  const dataset = {
    id: datasetId,
    name: 'cats_dogs_dataset',
    status: 'complete' as const,
    totalImages: 1847,
    categories: 2,
    qualityScore: 98.2,
    totalSize: '487 MB',
    createdAt: '2025-01-15T14:32:00Z',
    completedAt: '2025-01-15T14:47:00Z',
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <DatasetOverview dataset={dataset} />
      case 'gallery':
        return (
          <div className="flex h-full">
            {!filesystemCollapsed && (
              <DatasetFilesystem 
                datasetId={datasetId}
                onCollapse={() => setFilesystemCollapsed(true)}
              />
            )}
            <DatasetGallery 
              datasetId={datasetId}
              showFilesystemToggle={filesystemCollapsed}
              onShowFilesystem={() => setFilesystemCollapsed(false)}
            />
          </div>
        )
      case 'filesystem':
        return <DatasetFilesystem datasetId={datasetId} />
      case 'settings':
        return <DatasetSettings dataset={dataset} />
      case 'logs':
        return <div className="p-6">Logs content coming soon...</div>
      case 'analytics':
        return <div className="p-6">Analytics content coming soon...</div>
      default:
        return <DatasetGallery datasetId={datasetId} />
    }
  }

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="flex h-screen w-full">
        {/* Navigation Sidebar */}
        <Sidebar className="border-r">
          <SidebarContent>
            <div className="p-4">
              <SidebarMenu>
                {sidebarItems.map((item) => (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={activeTab === item.id}
                      onClick={() => setActiveTab(item.id as TabType)}
                      tooltip={item.label}
                    >
                      <item.icon className="w-4 h-4" />
                      <span>{item.label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
              <SidebarSeparator className="my-4" />
            </div>
          </SidebarContent>
        </Sidebar>

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          <DatasetTopBar dataset={dataset} />
          <div className="flex-1 overflow-hidden">
            {renderContent()}
          </div>
        </div>
      </div>
    </SidebarProvider>
  )
}