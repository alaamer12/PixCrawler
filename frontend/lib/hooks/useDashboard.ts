/**
 * Dashboard Hooks
 * 
 * Custom React hooks for dashboard data operations.
 * Provides hooks for datasets, jobs, activities, and stats.
 */

import { useState, useEffect, useCallback } from 'react'
import { apiService } from '@/lib/services'
import { dashboardApi } from '@/lib/api/services/dashboard.service'

// Types for dashboard data
export interface Dataset {
    id: string
    name: string
    status: 'active' | 'processing' | 'completed' | 'failed'
    imageCount: number
    createdAt: Date
    projectId: string
}

export interface Job {
    id: string
    name: string
    status: 'pending' | 'running' | 'completed' | 'failed'
    progress: number
    createdAt: Date
    projectId: string
}

export interface Activity {
    id: string
    type: string
    message: string
    timestamp: Date
    userId: string
}

export interface DashboardStats {
    totalProjects: number
    totalDatasets: number
    totalImages: number
    activeJobs: number
    storageUsed?: string
    processingSpeed?: string
}

/**
 * Hook to fetch datasets
 */
export function useDatasets() {
    const [datasets, setDatasets] = useState<Dataset[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchDatasets = useCallback(async () => {
        setLoading(true)
        setError(null)

        // TODO: Implement proper datasets fetching - currently returning empty array
        // The apiService.getDatasets() requires a projectId parameter
        // For dashboard view, we need an endpoint that returns all datasets for the user
        setDatasets([])
        setLoading(false)
    }, [])

    useEffect(() => {
        fetchDatasets()
    }, [fetchDatasets])

    return {
        datasets,
        loading,
        error,
        refetch: fetchDatasets,
    }
}

/**
 * Hook to fetch jobs
 */
export function useJobs() {
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchJobs = useCallback(async () => {
        setLoading(true)
        setError(null)

        // TODO: Implement proper jobs fetching - currently returning empty array
        // The apiService.getJobs() requires a datasetId parameter
        // For dashboard view, we need an endpoint that returns all jobs for the user
        setJobs([])
        setLoading(false)
    }, [])

    useEffect(() => {
        fetchJobs()
    }, [fetchJobs])

    return {
        jobs,
        loading,
        error,
        refetch: fetchJobs,
    }
}

/**
 * Hook to fetch activities
 */
export function useActivities() {
    const [activities, setActivities] = useState<Activity[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchActivities = useCallback(async () => {
        setLoading(true)
        setError(null)

        // TODO: Implement proper activities fetching - currently returning empty array
        // Need to create proper activities endpoint in the backend
        setActivities([])
        setLoading(false)
    }, [])

    useEffect(() => {
        fetchActivities()
    }, [fetchActivities])

    return {
        activities,
        loading,
        error,
        refetch: fetchActivities,
    }
}

/**
 * Hook to fetch dashboard stats
 */
export function useDashboardStats() {
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchStats = useCallback(async () => {
        setLoading(true)
        setError(null)

        const { data, error: fetchError } = await dashboardApi.getStats()

        if (fetchError) {
            setError(fetchError)
        } else if (data) {
            setStats({
                totalProjects: data.total_projects,
                totalDatasets: data.total_datasets,
                totalImages: data.total_images,
                activeJobs: data.active_jobs,
            })
        }

        setLoading(false)
    }, [])

    useEffect(() => {
        fetchStats()
    }, [fetchStats])

    return {
        stats,
        loading,
        error,
        refetch: fetchStats,
    }
}
