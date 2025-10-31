'use client'

import {useAuth} from '@/lib/auth/hooks'
import {Activity, Download, FolderOpen, Plus} from 'lucide-react'
import {Button} from '@/components/ui/button'
import Link from 'next/link'

export default function DashboardPage() {
  const {user} = useAuth()

  return (
    <div className="space-y-6 mx-6 py-8">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1
            className="text-4xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            {user?.profile?.fullName ? `Welcome back, ${user.profile.fullName}!` : 'Welcome to Your Dashboard'}
          </h1>
          <p className="text-base text-muted-foreground">
            Build and manage your AI-ready image datasets
          </p>
        </div>
        <Button asChild>
          <Link href="/dashboard/projects/new" className="inline-flex items-center gap-2">
            <Plus className="size-4"/>
            New Project
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground shadow-sm p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Projects</h3>
            <FolderOpen className="size-4 text-muted-foreground"/>
          </div>
          <div className="text-2xl font-bold">0</div>
          <p className="text-xs text-muted-foreground">
            No projects created yet
          </p>
        </div>

        <div className="rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground shadow-sm p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Active Jobs</h3>
            <Activity className="size-4 text-muted-foreground"/>
          </div>
          <div className="text-2xl font-bold">0</div>
          <p className="text-xs text-muted-foreground">
            No active crawl jobs
          </p>
        </div>

        <div className="rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground shadow-sm p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Images Collected</h3>
            <Download className="size-4 text-muted-foreground"/>
          </div>
          <div className="text-2xl font-bold">0</div>
          <p className="text-xs text-muted-foreground">
            No images collected yet
          </p>
        </div>

        <div className="rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground shadow-sm p-4">
          <div className="flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Storage Used</h3>
          </div>
          <div className="text-2xl font-bold">0 MB</div>
          <p className="text-xs text-muted-foreground">
            No storage used
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="size-12 mx-auto mb-4 opacity-50"/>
            <p>No recent activity</p>
            <p className="text-sm">Your project activity will appear here</p>
          </div>
        </div>

        <div className="rounded-lg border bg-card/80 backdrop-blur-md text-card-foreground shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link
              href="/dashboard/projects/new"
              className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent transition-colors"
            >
              <Plus className="size-5 text-primary"/>
              <div>
                <p className="font-medium">Create New Project</p>
                <p className="text-sm text-muted-foreground">Start a new image dataset project</p>
              </div>
            </Link>
            <Link
              href="/dashboard/projects"
              className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent transition-colors"
            >
              <FolderOpen className="size-5 text-primary"/>
              <div>
                <p className="font-medium">View All Projects</p>
                <p className="text-sm text-muted-foreground">Manage your existing projects</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
