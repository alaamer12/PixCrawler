'use client'

import { useState } from 'react'
import { 
  ChevronLeft, 
  ChevronRight, 
  Folder, 
  FolderOpen, 
  FileImage, 
  FileText,
  MoreHorizontal
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface FileSystemItem {
  id: string
  name: string
  type: 'folder' | 'image' | 'file'
  size?: string
  count?: number
  children?: FileSystemItem[]
  expanded?: boolean
}

interface DatasetFilesystemProps {
  datasetId: string
  onCollapse?: () => void
}

// Mock filesystem data
const mockFileSystem: FileSystemItem[] = [
  {
    id: 'root',
    name: 'cats_dogs_dataset',
    type: 'folder',
    expanded: true,
    children: [
      {
        id: 'cats',
        name: 'cats',
        type: 'folder',
        count: 912,
        expanded: true,
        children: [
          { id: 'cat_001', name: 'cat_001.jpg', type: 'image', size: '245 KB' },
          { id: 'cat_002', name: 'cat_002.jpg', type: 'image', size: '189 KB' },
          { id: 'cat_003', name: 'cat_003.jpg', type: 'image', size: '312 KB' },
          { id: 'more_cats', name: '+ 908 more', type: 'file' },
        ]
      },
      {
        id: 'dogs',
        name: 'dogs',
        type: 'folder',
        count: 935,
        children: []
      },
      { id: 'manifest', name: 'manifest.json', type: 'file', size: '12 KB' },
      { id: 'metadata', name: 'metadata.csv', type: 'file', size: '89 KB' },
      { id: 'labels', name: 'labels.txt', type: 'file', size: '2 KB' },
    ]
  }
]

export function DatasetFilesystem({ datasetId, onCollapse }: DatasetFilesystemProps) {
  const [fileSystem, setFileSystem] = useState<FileSystemItem[]>(mockFileSystem)
  const [selectedItem, setSelectedItem] = useState<string>('cats')

  const toggleFolder = (itemId: string) => {
    const updateItems = (items: FileSystemItem[]): FileSystemItem[] => {
      return items.map(item => {
        if (item.id === itemId) {
          return { ...item, expanded: !item.expanded }
        }
        if (item.children) {
          return { ...item, children: updateItems(item.children) }
        }
        return item
      })
    }
    setFileSystem(updateItems(fileSystem))
  }

  const renderIcon = (item: FileSystemItem) => {
    if (item.type === 'folder') {
      return item.expanded ? (
        <FolderOpen className="w-4 h-4 text-blue-600" />
      ) : (
        <Folder className="w-4 h-4 text-blue-600" />
      )
    }
    if (item.type === 'image') {
      return <FileImage className="w-4 h-4 text-green-600" />
    }
    return <FileText className="w-4 h-4 text-gray-600" />
  }

  const renderFileSystemItem = (item: FileSystemItem, depth = 0) => {
    const isSelected = selectedItem === item.id
    const hasChildren = item.children && item.children.length > 0

    return (
      <div key={item.id}>
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer hover:bg-muted/50 rounded-sm",
            isSelected && "bg-primary text-primary-foreground",
            depth > 0 && "ml-4"
          )}
          style={{ paddingLeft: `${depth * 16 + 12}px` }}
          onClick={() => {
            if (item.type === 'folder') {
              toggleFolder(item.id)
            }
            setSelectedItem(item.id)
          }}
        >
          {renderIcon(item)}
          <span className="flex-1 truncate">{item.name}</span>
          {item.count && (
            <span className="text-xs text-muted-foreground">
              ({item.count} images)
            </span>
          )}
          {item.name === '+ 908 more' && (
            <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
          )}
        </div>
        
        {item.expanded && item.children && (
          <div>
            {item.children.map(child => renderFileSystemItem(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="w-72 border-r bg-background flex flex-col">
      {/* Header */}
      <div className="h-12 border-b flex items-center justify-between px-4">
        <h3 className="font-medium text-sm">File System</h3>
        {onCollapse && (
          <Button 
            variant="ghost" 
            size="sm"
            onClick={onCollapse}
            className="h-6 w-6 p-0"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-y-auto p-3">
        {fileSystem.map(item => renderFileSystemItem(item))}
      </div>
    </div>
  )
}