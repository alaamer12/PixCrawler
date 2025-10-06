'use client'

import { useState } from 'react'
import { Grid3X3, List, Search, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface ImageItem {
  id: string
  name: string
  size: string
  dimensions: string
  status: 'valid' | 'invalid' | 'processing'
  category?: string
}

interface DatasetGalleryProps {
  datasetId: string
  showFilesystemToggle?: boolean
  onShowFilesystem?: () => void
}

// Mock image data
const mockImages: ImageItem[] = [
  { id: '1', name: 'cat_001.jpg', size: '245 KB', dimensions: '1024x768', status: 'valid', category: 'cats' },
  { id: '2', name: 'cat_002.jpg', size: '189 KB', dimensions: '800x600', status: 'valid', category: 'cats' },
  { id: '3', name: 'cat_003.jpg', size: '312 KB', dimensions: '1280x960', status: 'valid', category: 'cats' },
  { id: '4', name: 'cat_004.jpg', size: '267 KB', dimensions: '1024x768', status: 'valid', category: 'cats' },
  { id: '5', name: 'cat_005.jpg', size: '198 KB', dimensions: '900x700', status: 'valid', category: 'cats' },
  { id: '6', name: 'cat_006.jpg', size: '289 KB', dimensions: '1100x850', status: 'valid', category: 'cats' },
  { id: '7', name: 'dog_001.jpg', size: '234 KB', dimensions: '1024x768', status: 'valid', category: 'dogs' },
  { id: '8', name: 'dog_002.jpg', size: '276 KB', dimensions: '1200x900', status: 'valid', category: 'dogs' },
]

export function DatasetGallery({ 
  datasetId, 
  showFilesystemToggle = false, 
  onShowFilesystem 
}: DatasetGalleryProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('cats')

  const filteredImages = mockImages.filter(image => {
    const matchesSearch = image.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = !selectedCategory || image.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const categoryCount = selectedCategory === 'cats' ? 912 : 1847

  return (
    <div className="flex-1 flex flex-col bg-muted/30">
      {/* Gallery Header */}
      <div className="h-12 border-b bg-background flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          {showFilesystemToggle && onShowFilesystem && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={onShowFilesystem}
            >
              <ChevronRight className="w-4 h-4 mr-2" />
              Show Filesystem
            </Button>
          )}
          <h3 className="font-medium">
            {selectedCategory} ({categoryCount.toLocaleString()} images)
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center border rounded-md">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="rounded-r-none"
            >
              <Grid3X3 className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="rounded-l-none"
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search images..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 w-64"
            />
          </div>
        </div>
      </div>

      {/* Gallery Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
            {filteredImages.map((image) => (
              <div
                key={image.id}
                className="bg-background border rounded-lg overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="aspect-square bg-muted flex items-center justify-center text-xs text-muted-foreground">
                  Image Preview
                </div>
                <div className="p-2">
                  <div className="font-medium text-xs truncate mb-1">
                    {image.name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {image.dimensions} • {image.size}
                    {image.status === 'valid' && (
                      <span className="text-green-600 ml-1">• Valid</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredImages.map((image) => (
              <div
                key={image.id}
                className="bg-background border rounded-lg p-4 flex items-center gap-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="w-16 h-16 bg-muted rounded flex items-center justify-center text-xs text-muted-foreground">
                  IMG
                </div>
                <div className="flex-1">
                  <div className="font-medium">{image.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {image.dimensions} • {image.size}
                    {image.status === 'valid' && (
                      <span className="text-green-600 ml-2">Valid</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}