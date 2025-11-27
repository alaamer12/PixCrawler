'use client'

import {useSearchParams} from 'next/navigation'
import Link from 'next/link'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card'
import {FolderOpen, Plus} from 'lucide-react'
import {useAuth} from '@/lib/auth/hooks'
import {ProjectsList} from '@/app/dashboard/projects-list'

export default function ProjectsPage() {
  const searchParams = useSearchParams()
  const isDevMode = searchParams.get('dev_bypass') === 'true'
  const {user} = useAuth()

  return (
    <div className="space-y-6 mx-6 py-8">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <FolderOpen className="w-5 h-5 text-primary"/>
            <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Projects
            </h1>
            {null}
          </div>
          <p className="text-base text-muted-foreground">
            Organize datasets and manage image collection projects
          </p>
        </div>
        <Button asChild leftIcon={<Plus className="w-4 h-4"/>}>
          <Link href={isDevMode ? '/dashboard/projects/new?dev_bypass=true' : '/dashboard/projects/new'}>
            New Project
          </Link>
        </Button>
      </div>

      <Card className="bg-card/80 backdrop-blur-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Your Projects</CardTitle>
          <Button asChild variant="outline">
            <Link href={isDevMode ? '/dashboard?dev_bypass=true' : '/dashboard'}>
              Back to Dashboard
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {user?.id ? (
            <ProjectsList userId={user.id}/>
          ) : (
            <div className="text-center py-12">
              <div className="text-gray-400 text-4xl mb-4">📁</div>
              <p className="text-muted-foreground">Loading user...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
