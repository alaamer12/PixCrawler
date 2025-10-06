'use client'

import { Download, RotateCcw, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SidebarTrigger } from '@/components/ui/sidebar'

interface Dataset {
  id: string
  name: string
  status: 'processing' | 'complete' | 'failed' | 'paused'
  totalImages: number
  categories: number
  qualityScore: number
  totalSize: string
}

interface DatasetTopBarProps {
  dataset: Dataset
}

const statusConfig = {
  processing: { 
    label: 'Processing', 
    className: 'bg-blue-100 text-blue-800 border-blue-200' 
  },
  complete: { 
    label: `✓ Complete - ${0} images`, 
    className: 'bg-green-100 text-green-800 border-green-200' 
  },
  failed: { 
    label: 'Failed', 
    className: 'bg-red-100 text-red-800 border-red-200' 
  },
  paused: { 
    label: 'Paused', 
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200' 
  },
}

export function DatasetTopBar({ dataset }: DatasetTopBarProps) {
  const status = statusConfig[dataset.status]
  const statusLabel = dataset.status === 'complete' 
    ? `✓ Complete - ${dataset.totalImages.toLocaleString()} images`
    : status.label

  return (
    <div className="h-14 border-b bg-background flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <SidebarTrigger />
        <h1 className="text-lg font-semibold">{dataset.name}</h1>
      </div>

      <div className="flex items-center gap-3">
        <Badge 
          variant="outline" 
          className={status.className}
        >
          {statusLabel}
        </Badge>
        
        <Button variant="outline" size="sm">
          <Settings className="w-4 h-4 mr-2" />
          Settings
        </Button>
        
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" />
          Download
        </Button>
        
        <Button size="sm">
          <RotateCcw className="w-4 h-4 mr-2" />
          Re-run
        </Button>
      </div>
    </div>
  )
}