'use client'

import { useState, useMemo } from 'react'
import {
  ArrowLeft,
  Search,
  ChevronDown,
  Grid3X3,
  List,
  Download,
  GitFork,
  Eye,
  EyeOff,
  Filter,
  Image as ImageIcon,
  BarChart3,
  Database,
  Settings,
  Zap,
  Edit3
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/utils'
import Link from 'next/link'

interface DatasetDashboardProps {
  datasetId: string
}

export function DatasetDashboard({ datasetId }: DatasetDashboardProps) {
  const [selectedImages, setSelectedImages] = useState<Set<number>>(new Set())
  const [showAnnotations, setShowAnnotations] = useState(true)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('newest')
  const [splitFilter, setSplitFilter] = useState('all')
  const [classFilter, setClassFilter] = useState('all')

  // Mock images data
  const images = useMemo(() => 
    Array.from({ length: 24 }, (_, i) => ({
      id: i,
      src: `https://picsum.photos/400/400?random=${i + 100}`,
      filename: `${i + 107}.jpg`,
      hasAnnotations: Math.random() > 0.3
    })),
    []
  )

  const filteredImages = useMemo(() => {
    return images.filter(img => 
      img.filename.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [images, searchQuery])

  const toggleImageSelection = (imageId: number) => {
    setSelectedImages(prev => {
      const newSet = new Set(prev)
      if (newSet.has(imageId)) {
        newSet.delete(imageId)
      } else {
        newSet.add(imageId)
      }
      return newSet
    })
  }

  const selectAllImages = () => {
    if (selectedImages.size === filteredImages.length) {
      setSelectedImages(new Set())
    } else {
      setSelectedImages(new Set(filteredImages.map(img => img.id)))
    }
  }

  // Sidebar navigation items
  const sidebarItems = [
    { id: 'overview', icon: BarChart3, label: 'Overview', section: 'GENERAL' },
    { id: 'images', icon: ImageIcon, label: 'Images', count: '1.8k', active: true, section: 'DATA' },
    { id: 'dataset', icon: Database, label: 'Dataset', count: '2', section: 'DATA' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics', section: 'DATA' },
    { id: 'model', icon: Zap, label: 'Model', count: '1', section: 'DEPLOY' },
    { id: 'api', icon: Settings, label: 'API Docs', section: 'DEPLOY' },
  ]

  const groupedItems = sidebarItems.reduce((acc, item) => {
    if (!acc[item.section]) acc[item.section] = []
    acc[item.section].push(item)
    return acc
  }, {} as Record<string, typeof sidebarItems>)

  return (
    <div className="h-screen flex bg-gray-900">
      {/* Dark Left Sidebar with Icons */}
      <div className="w-16 bg-gradient-to-b from-blue-600 to-blue-800 flex flex-col items-center py-4">
        {/* Logo */}
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center mb-6">
          <svg className="w-5 h-5 text-white" viewBox="0 0 100 100" fill="currentColor">
            <path d="M20 30 Q20 20 30 20 L70 20 Q80 20 80 30 L80 40 Q80 50 70 50 L50 50 Q40 50 40 60 L40 70 Q40 80 50 80 L70 80 Q80 80 80 70" stroke="currentColor" strokeWidth="8" fill="none" strokeLinecap="round"/>
          </svg>
        </div>

        {/* Navigation Icons */}
        <div className="flex flex-col gap-2">
          <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-white cursor-pointer hover:bg-white/20 transition-colors">
            <ImageIcon className="w-5 h-5" />
          </div>
          <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white/60 cursor-pointer hover:bg-white/10 transition-colors">
            <Database className="w-5 h-5" />
          </div>
          <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white/60 cursor-pointer hover:bg-white/10 transition-colors">
            <BarChart3 className="w-5 h-5" />
          </div>
        </div>

        {/* Bottom Icons */}
        <div className="mt-auto">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white/60 cursor-pointer hover:bg-white/10 transition-colors">
            <Settings className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* White Side Panel */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-2 mb-4 text-gray-600">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back</span>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-16 h-12 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
              <img 
                src="https://picsum.photos/64/48?random=1" 
                alt="Dataset preview"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="min-w-0">
              <h1 className="font-semibold text-lg text-gray-900 truncate">animals</h1>
              <p className="text-sm text-gray-500">Object Detection</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 p-4 overflow-y-auto">
          {Object.entries(groupedItems).map(([section, items]) => (
            <div key={section} className="mb-6">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
                {section}
              </div>
              <div className="space-y-1">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className={cn(
                      "flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-all duration-200",
                      item.active 
                        ? "bg-purple-50 text-purple-700 border border-purple-200" 
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm font-medium">{item.label}</span>
                    </div>
                    {item.count && (
                      <Badge variant="secondary" className="text-xs bg-gray-100 text-gray-600">
                        {item.count}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-5 h-5 text-blue-400" />
                <h2 className="text-xl font-semibold text-white">Images</h2>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="text-blue-400 border-blue-600 hover:bg-blue-900/50 bg-gray-800">
                <Download className="w-4 h-4 mr-2" />
                Clone Images
              </Button>
              <Button variant="outline" size="sm" className="text-blue-400 border-blue-600 hover:bg-blue-900/50 bg-gray-800">
                <GitFork className="w-4 h-4 mr-2" />
                Fork Dataset
              </Button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex items-center gap-4 mb-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search images"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-gray-700 border-gray-600 text-white placeholder-gray-400"
              />
            </div>
            <Button variant="outline" size="sm" className="bg-gray-700 border-gray-600 text-white hover:bg-gray-600">
              <Search className="w-4 h-4 mr-2" />
              Search
            </Button>
          </div>

          {/* Filter Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Select value={splitFilter} onValueChange={setSplitFilter}>
                <SelectTrigger className="w-24 h-8 text-sm bg-gray-700 border-gray-600 text-white">
                  <SelectValue placeholder="Split" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Split</SelectItem>
                  <SelectItem value="train">Train</SelectItem>
                  <SelectItem value="valid">Valid</SelectItem>
                  <SelectItem value="test">Test</SelectItem>
                </SelectContent>
              </Select>

              <Select value={classFilter} onValueChange={setClassFilter}>
                <SelectTrigger className="w-28 h-8 text-sm bg-gray-700 border-gray-600 text-white">
                  <SelectValue placeholder="Classes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Classes</SelectItem>
                  <SelectItem value="cat">Cat</SelectItem>
                  <SelectItem value="dog">Dog</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-32 h-8 text-sm bg-gray-700 border-gray-600 text-white">
                  <SelectValue placeholder="Sort By" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Newest</SelectItem>
                  <SelectItem value="oldest">Oldest</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="sm" className="h-8 text-sm bg-gray-700 border-gray-600 text-white hover:bg-gray-600">
                <Filter className="w-4 h-4 mr-2" />
                Search by image
              </Button>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={selectedImages.size === filteredImages.length && filteredImages.length > 0}
                  onCheckedChange={selectAllImages}
                />
                <span className="text-sm text-muted-foreground">
                  {selectedImages.size} images selected
                </span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Show annotations</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAnnotations(!showAnnotations)}
                  className="p-1 h-8 w-8"
                >
                  {showAnnotations ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                </Button>
              </div>

              <div className="flex border rounded-md overflow-hidden">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                  className="rounded-none h-8 px-3"
                >
                  <Grid3X3 className="w-4 h-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="rounded-none h-8 px-3"
                >
                  <List className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Images Grid */}
        <div className="flex-1 overflow-auto p-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
            {filteredImages.map((image) => (
              <div key={image.id} className="relative group">
                <div
                  className={cn(
                    "relative rounded-lg overflow-hidden border-2 transition-all duration-200 cursor-pointer",
                    selectedImages.has(image.id) 
                      ? "border-blue-500 shadow-lg shadow-blue-500/20" 
                      : "border-transparent hover:border-border hover:shadow-md"
                  )}
                >
                  {/* Selection Checkbox */}
                  <div className="absolute top-2 left-2 z-10">
                    <Checkbox
                      checked={selectedImages.has(image.id)}
                      onCheckedChange={() => toggleImageSelection(image.id)}
                      className="bg-background/90 shadow-sm"
                    />
                  </div>

                  {/* Annotation Indicator */}
                  {image.hasAnnotations && showAnnotations && (
                    <div className="absolute top-2 right-2 z-10">
                      <div className="w-6 h-6 bg-warning rounded-sm flex items-center justify-center shadow-sm">
                        <Edit3 className="w-3 h-3 text-warning-foreground" />
                      </div>
                    </div>
                  )}

                  {/* Image */}
                  <div className="aspect-square bg-muted overflow-hidden">
                    <img
                      src={image.src}
                      alt={image.filename}
                      className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                    />
                  </div>

                  {/* Image Name */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                    <p className="text-primary-foreground text-xs font-medium truncate">{image.filename}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}