'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { ArrowLeft, FolderPlus, Info, Sparkles } from 'lucide-react'
import Link from 'next/link'
import { ProjectCreationDialog } from '@/components/dashboard/project-creation-dialog'

export default function NewProjectPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isDevMode = searchParams.get('dev_bypass') === 'true'

  const [projectName, setProjectName] = useState('')
  const [description, setDescription] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [showSuccessDialog, setShowSuccessDialog] = useState(false)
  const [createdProjectId, setCreatedProjectId] = useState('')

  const handleCreateProject = async () => {
    if (!projectName.trim()) return

    setIsCreating(true)
    
    try {
      // TODO: Implement actual project creation API call
      // const response = await fetch('/api/projects', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ name: projectName, description })
      // })
      // const data = await response.json()
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Mock project ID - replace with actual ID from API
      const mockProjectId = `proj_${Date.now()}`
      setCreatedProjectId(mockProjectId)
      setShowSuccessDialog(true)
    } catch (error) {
      console.error('Failed to create project:', error)
      // TODO: Show error toast
    } finally {
      setIsCreating(false)
    }
  }

  const isFormValid = projectName.trim().length > 0

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
                <ArrowLeft className="w-4 h-4 mr-2"/>
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
            Projects organize your datasets and image collections
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary"/>
          <span className="text-sm text-muted-foreground">AI-Powered</span>
        </div>
      </div>

      {/* Main Form */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Form */}
        <div className="lg:col-span-2">
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderPlus className="w-5 h-5" />
                Project Information
              </CardTitle>
              <CardDescription>
                Provide basic details about your project. You'll create datasets within this project later.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="project-name">
                  Project Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="project-name"
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="e.g., Wildlife Conservation Dataset"
                  className="bg-background/50"
                  maxLength={100}
                />
                <p className="text-xs text-muted-foreground">
                  Choose a descriptive name for your project
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="project-description">Description (Optional)</Label>
                <Textarea
                  id="project-description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the purpose of this project and what kind of datasets you plan to create..."
                  rows={6}
                  className="bg-background/50 resize-none"
                  maxLength={500}
                />
                <p className="text-xs text-muted-foreground">
                  {description.length}/500 characters
                </p>
              </div>

              <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
                <div className="flex gap-3">
                  <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-blue-500">What happens next?</p>
                    <p className="text-xs text-muted-foreground">
                      After creating your project, you'll be able to create multiple datasets within it. 
                      Each dataset can have different keywords, sources, and configurations.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Summary & Actions */}
        <div className="space-y-6">
          {/* Project Summary */}
          <Card className="bg-card/80 backdrop-blur-md">
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between items-start py-2 border-b border-border/50">
                  <span className="text-sm text-muted-foreground">Project Name</span>
                  <span className="text-sm font-medium text-right max-w-[180px] truncate">
                    {projectName || <span className="text-muted-foreground">Not set</span>}
                  </span>
                </div>
                <div className="flex justify-between items-start py-2">
                  <span className="text-sm text-muted-foreground">Description</span>
                  <span className="text-sm font-medium text-right max-w-[180px] truncate">
                    {description ? (
                      <span className="text-xs">{description.substring(0, 50)}{description.length > 50 ? '...' : ''}</span>
                    ) : (
                      <span className="text-muted-foreground">None</span>
                    )}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card className="bg-gradient-to-br from-primary/10 to-purple-500/10 border-primary/20 backdrop-blur-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <Sparkles className="w-5 h-5" />
                Project Benefits
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Organize multiple related datasets</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Track progress across datasets</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Centralized management</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary mt-0.5">✓</span>
                  <span>Easy collaboration & sharing</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button
              onClick={handleCreateProject}
              disabled={!isFormValid || isCreating}
              loading={isCreating}
              loadingText="Creating..."
              className="w-full"
              size="lg"
              leftIcon={<FolderPlus className="w-4 h-4" />}
            >
              Create Project
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

      {/* Success Dialog */}
      <ProjectCreationDialog
        open={showSuccessDialog}
        onOpenChange={setShowSuccessDialog}
        projectId={createdProjectId}
        projectName={projectName}
      />
    </div>
  )
}
