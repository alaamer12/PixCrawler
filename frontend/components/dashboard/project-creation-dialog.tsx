'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Database, FolderOpen, CheckCircle } from 'lucide-react'

interface ProjectCreationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  projectId: string
  projectName: string
}

export function ProjectCreationDialog({
  open,
  onOpenChange,
  projectId,
  projectName
}: ProjectCreationDialogProps) {
  const router = useRouter()

  const handleCreateDataset = () => {
    onOpenChange(false)
    router.push(`/dashboard/projects/${projectId}/datasets/new`)
  }

  const handleSkip = () => {
    onOpenChange(false)
    router.push(`/dashboard/projects/${projectId}`)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-green-500/10 mx-auto mb-4">
            <CheckCircle className="w-6 h-6 text-green-500" />
          </div>
          <DialogTitle className="text-center text-2xl">
            Project Created Successfully!
          </DialogTitle>
          <DialogDescription className="text-center">
            Your project "{projectName}" has been created. What would you like to do next?
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 mt-6">
          <Button
            className="w-full justify-start h-auto py-4"
            variant="default"
            leftIcon={<Database className="w-5 h-5" />}
            onClick={handleCreateDataset}
          >
            <div className="text-left flex-1">
              <div className="font-semibold">Create Dataset Now</div>
              <div className="text-xs text-muted-foreground font-normal">
                Start building your first image dataset
              </div>
            </div>
          </Button>

          <Button
            className="w-full justify-start h-auto py-4"
            variant="outline"
            leftIcon={<FolderOpen className="w-5 h-5" />}
            onClick={handleSkip}
          >
            <div className="text-left flex-1">
              <div className="font-semibold">View Project</div>
              <div className="text-xs text-muted-foreground font-normal">
                Go to project page and create datasets later
              </div>
            </div>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
