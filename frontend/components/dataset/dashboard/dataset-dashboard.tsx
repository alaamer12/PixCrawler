'use client'

import { useState } from 'react'
import { 
  BarChart3, 
  FileImage, 
  FolderOpen, 
  Settings,
  Download,
  RotateCcw,
  Grid3X3,
  List,
  Search,
  ChevronLeft,
  ChevronRight,
  FileText,
  MoreHorizontal
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface DatasetDashboardProps {
  datasetId: string
}

export function DatasetDashboard({ datasetId }: DatasetDashboardProps) {
  const [activeTab, setActiveTab] = useState('gallery')
  const [showFilesystem, setShowFilesystem] = useState(true)

  // Mock dataset data
  const dataset = {
    id: datasetId,
    name: 'cats_dogs_dataset',
    status: 'complete' as const,
    totalImages: 1847,
    categories: 2,
    qualityScore: 98.2,
    totalSize: '487 MB',
  }

  const tabs = [
    { id: 'overview', icon: BarChart3, label: 'Overview' },
    { id: 'gallery', icon: FileImage, label: 'Gallery' },
    { id: 'files', icon: FolderOpen, label: 'Files' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="flex h-16 shrink-0 items-center justify-between border-b px-6">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold tracking-tight">{dataset.name}</h1>
        </div>
        
        <div className="flex items-center space-x-3">
          <Badge variant="secondary" className="bg-emerald-50 text-emerald-700 border-emerald-200">
            <div className="w-2 h-2 bg-emerald-500 rounded-full mr-2" />
            Complete • {dataset.totalImages.toLocaleString()} images
          </Badge>
          
          <Button variant="outline" size="sm" className="h-8">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
          
          <Button variant="outline" size="sm" className="h-8">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          
          <Button size="sm" className="h-8">
            <RotateCcw className="w-4 h-4 mr-2" />
            Re-run
          </Button>
        </div>
      </header>

      <div className="flex-1 flex">
        {/* Left Sidebar */}
        <div className="w-16 border-r bg-muted/30 flex flex-col items-center py-4 gap-2">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "ghost"}
              size="sm"
              onClick={() => setActiveTab(tab.id)}
              className="w-10 h-10 p-0"
              title={tab.label}
            >
              <tab.icon className="h-4 w-4" />
            </Button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'overview' && <OverviewContent dataset={dataset} />}
          {activeTab === 'gallery' && <GalleryContent showFilesystem={showFilesystem} setShowFilesystem={setShowFilesystem} />}
          {activeTab === 'files' && <FilesContent />}
          {activeTab === 'settings' && <SettingsContent />}
        </div>
      </div>
    </div>
  )
}

// Overview Content Component
function OverviewContent({ dataset }: { dataset: any }) {
  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-6">Dataset Overview</h2>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Images</p>
                  <p className="text-3xl font-bold">{dataset.totalImages.toLocaleString()}</p>
                </div>
                <FileImage className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Categories</p>
                  <p className="text-3xl font-bold">{dataset.categories}</p>
                </div>
                <FolderOpen className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Quality Score</p>
                  <p className="text-3xl font-bold">{dataset.qualityScore}%</p>
                </div>
                <BarChart3 className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Size</p>
                  <p className="text-3xl font-bold">{dataset.totalSize}</p>
                </div>
                <Settings className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Processing Summary */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardContent className="p-6">
              <h3 className="font-semibold mb-4">Processing Summary</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Started:</span>
                  <span>Jan 15, 2025 14:32</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Completed:</span>
                  <span>Jan 15, 2025 14:47</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duration:</span>
                  <span>15 minutes</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Images processed:</span>
                  <span>2,103</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Valid images:</span>
                  <span>1,847</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duplicates removed:</span>
                  <span>256</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <h3 className="font-semibold mb-4">Validation Results</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Format validation:</span>
                  <span>100%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Size validation:</span>
                  <span>98.7%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Integrity check:</span>
                  <span>99.1%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duplicate detection:</span>
                  <Badge variant="secondary" className="text-xs">Complete</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Quality assessment:</span>
                  <Badge variant="secondary" className="text-xs">Complete</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

// Gallery Content Component
function GalleryContent({ showFilesystem, setShowFilesystem }: { showFilesystem: boolean, setShowFilesystem: (show: boolean) => void }) {
  return (
    <div className="flex h-full">
      {/* File System Panel */}
      {showFilesystem && (
        <div className="w-80 border-r bg-muted/20">
          <div className="flex h-12 items-center justify-between border-b px-4">
            <h3 className="font-medium">File System</h3>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setShowFilesystem(false)}
              className="h-8 w-8 p-0"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>
          <div className="p-4">
            <SimpleFileTree />
          </div>
        </div>
      )}

      {/* Gallery Content */}
      <div className="flex-1 flex flex-col">
        <div className="flex h-12 items-center justify-between border-b px-6">
          <div className="flex items-center space-x-4">
            {!showFilesystem && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowFilesystem(true)}
                className="h-8"
              >
                <ChevronRight className="h-4 w-4 mr-2" />
                Show Files
              </Button>
            )}
            <h3 className="font-medium">cats (912 images)</h3>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="flex border rounded-md">
              <Button variant="default" size="sm" className="h-8 rounded-r-none">
                <Grid3X3 className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" className="h-8 rounded-l-none">
                <List className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Search images..." className="h-8 w-64 pl-9" />
            </div>
          </div>
        </div>
        
        <div className="flex-1 overflow-auto p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
            {Array.from({ length: 32 }, (_, i) => (
              <Card key={i} className="overflow-hidden hover:shadow-sm transition-shadow">
                <div className="aspect-square bg-muted flex items-center justify-center">
                  <FileImage className="h-8 w-8 text-muted-foreground" />
                </div>
                <CardContent className="p-3">
                  <p className="text-xs font-medium truncate">cat_{String(i + 1).padStart(3, '0')}.jpg</p>
                  <p className="text-xs text-muted-foreground">1024×768 • 245 KB</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// Simple File Tree Component (no animations)
function SimpleFileTree() {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['root', 'cats']))

  const toggleFolder = (id: string) => {
    const newExpanded = new Set(expanded)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpanded(newExpanded)
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 p-2 text-sm font-medium">
        <FolderOpen className="h-4 w-4 text-blue-600" />
        <span>cats_dogs_dataset</span>
      </div>
      
      <div className="ml-4 space-y-1">
        <div 
          className={cn(
            "flex items-center gap-2 p-2 text-sm rounded cursor-pointer",
            expanded.has('cats') ? "bg-primary text-primary-foreground" : "hover:bg-muted"
          )}
          onClick={() => toggleFolder('cats')}
        >
          {expanded.has('cats') ? <FolderOpen className="h-4 w-4" /> : <FolderOpen className="h-4 w-4" />}
          <span>cats (912 images)</span>
        </div>
        
        {expanded.has('cats') && (
          <div className="ml-6 space-y-1">
            <div className="flex items-center gap-2 p-1 text-xs text-muted-foreground">
              <FileImage className="h-3 w-3" />
              <span>cat_001.jpg</span>
            </div>
            <div className="flex items-center gap-2 p-1 text-xs text-muted-foreground">
              <FileImage className="h-3 w-3" />
              <span>cat_002.jpg</span>
            </div>
            <div className="flex items-center gap-2 p-1 text-xs text-muted-foreground">
              <FileImage className="h-3 w-3" />
              <span>cat_003.jpg</span>
            </div>
            <div className="flex items-center gap-2 p-1 text-xs text-muted-foreground">
              <MoreHorizontal className="h-3 w-3" />
              <span>+ 908 more</span>
            </div>
          </div>
        )}
        
        <div 
          className="flex items-center gap-2 p-2 text-sm hover:bg-muted rounded cursor-pointer"
          onClick={() => toggleFolder('dogs')}
        >
          <FolderOpen className="h-4 w-4 text-blue-600" />
          <span>dogs (935 images)</span>
        </div>
        
        <div className="flex items-center gap-2 p-2 text-sm hover:bg-muted rounded">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span>manifest.json</span>
        </div>
        
        <div className="flex items-center gap-2 p-2 text-sm hover:bg-muted rounded">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span>metadata.csv</span>
        </div>
        
        <div className="flex items-center gap-2 p-2 text-sm hover:bg-muted rounded">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span>labels.txt</span>
        </div>
      </div>
    </div>
  )
}

// Files Content Component
function FilesContent() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold tracking-tight mb-6">Files</h2>
      <Card>
        <CardContent className="p-6">
          <SimpleFileTree />
        </CardContent>
      </Card>
    </div>
  )
}

// Settings Content Component
function SettingsContent() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold tracking-tight mb-6">Settings</h2>
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">Settings interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}