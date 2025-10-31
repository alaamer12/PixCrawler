'use client'

import {useState} from 'react'
import {useRouter, useSearchParams} from 'next/navigation'
import {Card, CardContent, CardDescription, CardHeader, CardTitle} from '@/components/ui/card'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {ArrowLeft, Sparkles, Image, Search, Settings, Zap} from 'lucide-react'
import Link from 'next/link'

export default function NewProjectPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isDevMode = searchParams.get('dev_bypass') === 'true'
  
  const [projectName, setProjectName] = useState('')
  const [keywords, setKeywords] = useState('')
  const [selectedSources, setSelectedSources] = useState<string[]>(['google'])
  const [imageCount, setImageCount] = useState(100)
  const [isCreating, setIsCreating] = useState(false)

  const sources = [
    {id: 'google', name: 'Google Images', icon: Search},
    {id: 'bing', name: 'Bing Images', icon: Search},
    {id: 'unsplash', name: 'Unsplash', icon: Image},
    {id: 'pixabay', name: 'Pixabay', icon: Image},
  ]

  const handleSourceToggle = (sourceId: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    )
  }

  const handleCreateProject = async () => {
    setIsCreating(true)
    // TODO: Implement actual project creation API call
    setTimeout(() => {
      setIsCreating(false)
      router.push(isDevMode ? '/dashboard?dev_bypass=true' : '/dashboard')
    }, 2000)
  }

  const isFormValid = projectName.trim() && keywords.trim() && selectedSources.length > 0

  return (
    <div className="space-y-6 mx-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              asChild
            >
              <Link href={isDevMode ? '/dashboard?dev_bypass=true' : '/dashboard'}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Link>
            </Button>
            {isDevMode && (
              <Badge variant="outline" className="bg-yellow-500/10 border-yellow-500/30 text-yellow-600">
                Dev Mode
              </Badge>
            )}
          </div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            Create New Project
          </h1>
          <p className="text-base text-muted-foreground">
            Build your AI-ready image dataset in minutes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <span className="text-sm text-muted-foreground">AI-Powered</span>
        </div>
      </div>

      {/* Main Form */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Project Details Card */}
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Project Details</CardTitle>
              <CardDescription>Give your dataset a name and define what you're looking for</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Project Name</label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="e.g., Cat Breeds Dataset"
                  className="w-full px-4 py-2 rounded-lg border bg-background/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Search Keywords</label>
                <textarea
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  placeholder="Enter keywords separated by commas (e.g., persian cat, siamese cat, maine coon)"
                  rows={4}
                  className="w-full px-4 py-2 rounded-lg border bg-background/50 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                />
                <p className="text-xs text-muted-foreground">
                  AI will automatically expand and optimize your keywords
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Images per Keyword</label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="10"
                    max="500"
                    step="10"
                    value={imageCount}
                    onChange={(e) => setImageCount(Number(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-sm font-semibold min-w-[60px] text-right">{imageCount} images</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Image Sources Card */}
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Image Sources</CardTitle>
              <CardDescription>Select where to crawl images from</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col gap-3">
                {sources.map((source) => {
                  const Icon = source.icon
                  const isSelected = selectedSources.includes(source.id)
                  return (
                    <Button
                      key={source.id}
                      onClick={() => handleSourceToggle(source.id)}
                      className={`flex items-center gap-3 p-4 rounded-lg border transition-all ${
                        isSelected
                          ? 'bg-primary/10 border-primary shadow-md'
                          : 'bg-background/50 hover:bg-accent'
                      }`}
                    >
                      <Icon className={`w-5 h-5 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                      <span className={`font-medium ${isSelected ? 'text-primary' : ''}`}>
                        {source.name}
                      </span>
                    </Button>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Summary & Actions */}
        <div className="space-y-6">
          {/* Project Summary */}
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-border/50">
                  <span className="text-sm text-muted-foreground">Project Name</span>
                  <span className="text-sm font-medium">{projectName || 'Not set'}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border/50">
                  <span className="text-sm text-muted-foreground">Keywords</span>
                  <span className="text-sm font-medium">
                    {keywords ? keywords.split(',').length : 0} keywords
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border/50">
                  <span className="text-sm text-muted-foreground">Sources</span>
                  <span className="text-sm font-medium">{selectedSources.length} selected</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-muted-foreground">Est. Images</span>
                  <span className="text-sm font-semibold text-primary">
                    ~{imageCount * (keywords.split(',').filter(k => k.trim()).length || 1)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Features Card */}
          <Card className="bg-gradient-to-br from-primary/10 to-purple-500/10 border-primary/20 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <Zap className="w-5 h-5" />
                What You Get
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>AI-powered keyword expansion</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Automatic deduplication</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Quality validation & filtering</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>ML-ready label formats</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Organized folder structure</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleCreateProject}
              disabled={!isFormValid || isCreating}
              className="w-full"
              size="lg"
            >
              {isCreating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                  Creating Project...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Create Project
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(isDevMode ? '/dashboard?dev_bypass=true' : '/dashboard')}
              className="w-full"
              disabled={isCreating}
            >
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
