/**
 * Projects Hooks
 * 
 * Custom React hooks for project-related data operations.
 * Provides hooks for fetching, creating, updating, and deleting projects.
 */

import { useState, useEffect, useCallback } from 'react'
import { supabaseService, type CreateProjectInput, type UpdateProjectInput } from '@/lib/services'
import type { Project } from '@/lib/db/schema'
import { useToast } from '@/components/ui/use-toast'

interface UseProjectsResult {
    projects: Project[]
    loading: boolean
    error: Error | null
    refetch: () => Promise<void>
}

interface UseProjectResult {
    project: Project | null
    loading: boolean
    error: Error | null
    refetch: () => Promise<void>
}

interface UseCreateProjectResult {
    createProject: (input: Omit<CreateProjectInput, 'user_id'>) => Promise<Project | null>
    loading: boolean
    error: Error | null
}

interface UseUpdateProjectResult {
    updateProject: (projectId: string, updates: UpdateProjectInput) => Promise<Project | null>
    loading: boolean
    error: Error | null
}

interface UseDeleteProjectResult {
    deleteProject: (projectId: string) => Promise<boolean>
    loading: boolean
    error: Error | null
}

/**
 * Hook to fetch all projects for the current user
 */
export function useProjects(userId: string): UseProjectsResult {
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchProjects = useCallback(async () => {
        if (!userId) {
            setLoading(false)
            return
        }

        setLoading(true)
        setError(null)

        const response = await supabaseService.getProjects(userId)

        if (response.error) {
            setError(response.error)
            setProjects([])
        } else {
            setProjects(response.data || [])
        }

        setLoading(false)
    }, [userId])

    useEffect(() => {
        fetchProjects()
    }, [fetchProjects])

    return {
        projects,
        loading,
        error,
        refetch: fetchProjects,
    }
}

/**
 * Hook to fetch a single project by ID
 */
export function useProject(projectId: string): UseProjectResult {
    const [project, setProject] = useState<Project | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchProject = useCallback(async () => {
        if (!projectId) {
            setLoading(false)
            return
        }

        setLoading(true)
        setError(null)

        const response = await supabaseService.getProject(projectId)

        if (response.error) {
            setError(response.error)
            setProject(null)
        } else {
            setProject(response.data)
        }

        setLoading(false)
    }, [projectId])

    useEffect(() => {
        fetchProject()
    }, [fetchProject])

    return {
        project,
        loading,
        error,
        refetch: fetchProject,
    }
}

/**
 * Hook to create a new project
 */
export function useCreateProject(userId: string): UseCreateProjectResult {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<Error | null>(null)
    const { toast } = useToast()

    const createProject = useCallback(
        async (input: Omit<CreateProjectInput, 'user_id'>): Promise<Project | null> => {
            setLoading(true)
            setError(null)

            const response = await supabaseService.createProject({
                ...input,
                user_id: userId,
            })

            if (response.error) {
                setError(response.error)
                toast({
                    title: 'Error',
                    description: 'Failed to create project. Please try again.',
                    variant: 'destructive',
                })
                setLoading(false)
                return null
            }

            toast({
                title: 'Success',
                description: 'Project created successfully',
            })

            setLoading(false)
            return response.data
        },
        [userId, toast]
    )

    return {
        createProject,
        loading,
        error,
    }
}

/**
 * Hook to update a project
 */
export function useUpdateProject(): UseUpdateProjectResult {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<Error | null>(null)
    const { toast } = useToast()

    const updateProject = useCallback(
        async (projectId: string, updates: UpdateProjectInput): Promise<Project | null> => {
            setLoading(true)
            setError(null)

            const response = await supabaseService.updateProject(projectId, updates)

            if (response.error) {
                setError(response.error)
                toast({
                    title: 'Error',
                    description: 'Failed to update project. Please try again.',
                    variant: 'destructive',
                })
                setLoading(false)
                return null
            }

            toast({
                title: 'Success',
                description: 'Project updated successfully',
            })

            setLoading(false)
            return response.data
        },
        [toast]
    )

    return {
        updateProject,
        loading,
        error,
    }
}

/**
 * Hook to delete a project
 */
export function useDeleteProject(): UseDeleteProjectResult {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<Error | null>(null)
    const { toast } = useToast()

    const deleteProject = useCallback(
        async (projectId: string): Promise<boolean> => {
            setLoading(true)
            setError(null)

            const response = await supabaseService.deleteProject(projectId)

            if (response.error) {
                setError(response.error)
                toast({
                    title: 'Error',
                    description: 'Failed to delete project. Please try again.',
                    variant: 'destructive',
                })
                setLoading(false)
                return false
            }

            toast({
                title: 'Success',
                description: 'Project deleted successfully',
            })

            setLoading(false)
            return true
        },
        [toast]
    )

    return {
        deleteProject,
        loading,
        error,
    }
}
