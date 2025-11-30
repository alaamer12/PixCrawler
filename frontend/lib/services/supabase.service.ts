/**
 * Supabase Service
 *
 * Centralized service for all Supabase database operations.
 * Handles profiles, projects, and generic CRUD operations.
 */

import { createClient } from '@/lib/supabase/client'
import { BaseService, ServiceResponse, ServiceError } from './base.service'
import type { SupabaseClient } from '@supabase/supabase-js'
import type { Project } from '@/lib/db/schema'

export interface Profile {
    id: string
    email: string
    fullName: string | null
    avatarUrl: string | null
    onboardingCompleted: boolean
    createdAt: Date
    updatedAt: Date
}

export interface CreateProjectInput {
    name: string
    description?: string
    user_id: string
}

export interface UpdateProjectInput {
    name?: string
    description?: string
    status?: 'active' | 'archived'
}

export class SupabaseService extends BaseService {
    private readonly client: SupabaseClient

    constructor() {
        super()
        this.client = createClient()
    }

    /**
     * Get the current Supabase client
     */
    getClient(): SupabaseClient {
        return this.client
    }

    // ============================================================================
    // Profile Operations
    // ============================================================================

    /**
     * Get user profile by ID
     */
    async getProfile(userId: string): Promise<ServiceResponse<Profile>> {
        this.logRequest('GET', `/profiles/${userId}`)

        return this.executeRequest(async () => {
            const { data, error } = await this.client
                .from('profiles')
                .select('*')
                .eq('id', userId)
                .single()

            if (error) {
                throw new ServiceError(
                    `Failed to fetch profile: ${error.message}`,
                    error.code === 'PGRST116' ? 404 : 500,
                    error
                )
            }

            this.logResponse('GET', `/profiles/${userId}`, data)

            return {
                id: data.id,
                email: data.email,
                fullName: data.full_name,
                avatarUrl: data.avatar_url,
                onboardingCompleted: data.onboarding_completed,
                createdAt: new Date(data.created_at),
                updatedAt: new Date(data.updated_at),
            }
        })
    }

    /**
     * Update user profile
     */
    async updateProfile(
        userId: string,
        updates: Partial<Omit<Profile, 'id' | 'createdAt' | 'updatedAt'>>
    ): Promise<ServiceResponse<Profile>> {
        this.logRequest('PATCH', `/profiles/${userId}`, updates)

        return this.executeRequest(async () => {
            const dbUpdates: any = {}

            if (updates.fullName !== undefined) dbUpdates.full_name = updates.fullName
            if (updates.avatarUrl !== undefined) dbUpdates.avatar_url = updates.avatarUrl
            if (updates.onboardingCompleted !== undefined) {
                dbUpdates.onboarding_completed = updates.onboardingCompleted
            }

            const { data, error } = await this.client
                .from('profiles')
                .update(dbUpdates)
                .eq('id', userId)
                .select()
                .single()

            if (error) {
                throw new ServiceError(
                    `Failed to update profile: ${error.message}`,
                    500,
                    error
                )
            }

            this.logResponse('PATCH', `/profiles/${userId}`, data)

            return {
                id: data.id,
                email: data.email,
                fullName: data.full_name,
                avatarUrl: data.avatar_url,
                onboardingCompleted: data.onboarding_completed,
                createdAt: new Date(data.created_at),
                updatedAt: new Date(data.updated_at),
            }
        })
    }

    // ============================================================================
    // Project Operations
    // ============================================================================

    /**
     * Get all projects for a user
     */
    async getProjects(userId: string): Promise<ServiceResponse<Project[]>> {
        this.logRequest('GET', '/projects', { userId })

        return this.executeRequest(async () => {
            const { data, error } = await this.client
                .from('projects')
                .select('*')
                .eq('user_id', userId)
                .order('created_at', { ascending: false })

            if (error) {
                throw new ServiceError(
                    `Failed to fetch projects: ${error.message}`,
                    500,
                    error
                )
            }

            this.logResponse('GET', '/projects', data)

            return data || []
        })
    }

    /**
     * Get a single project by ID
     */
    async getProject(projectId: string): Promise<ServiceResponse<Project>> {
        this.logRequest('GET', `/projects/${projectId}`)

        return this.executeRequest(async () => {
            const { data, error } = await this.client
                .from('projects')
                .select('*')
                .eq('id', projectId)
                .single()

            if (error) {
                throw new ServiceError(
                    `Failed to fetch project: ${error.message}`,
                    error.code === 'PGRST116' ? 404 : 500,
                    error
                )
            }

            this.logResponse('GET', `/projects/${projectId}`, data)

            return data
        })
    }

    /**
     * Create a new project
     */
    async createProject(
        input: CreateProjectInput
    ): Promise<ServiceResponse<Project>> {
        this.logRequest('POST', '/projects', input)

        return this.executeRequest(async () => {
            const { data, error } = await this.client
                .from('projects')
                .insert({
                    name: input.name,
                    description: input.description,
                    user_id: input.user_id,
                })
                .select()
                .single()

            if (error) {
                throw new ServiceError(
                    `Failed to create project: ${error.message}`,
                    500,
                    error
                )
            }

            this.logResponse('POST', '/projects', data)

            return data
        })
    }

    /**
     * Update a project
     */
    async updateProject(
        projectId: string,
        updates: UpdateProjectInput
    ): Promise<ServiceResponse<Project>> {
        this.logRequest('PATCH', `/projects/${projectId}`, updates)

        return this.executeRequest(async () => {
            const { data, error } = await this.client
                .from('projects')
                .update(updates)
                .eq('id', projectId)
                .select()
                .single()

            if (error) {
                throw new ServiceError(
                    `Failed to update project: ${error.message}`,
                    500,
                    error
                )
            }

            this.logResponse('PATCH', `/projects/${projectId}`, data)

            return data
        })
    }

    /**
     * Delete a project
     */
    async deleteProject(projectId: string): Promise<ServiceResponse<void>> {
        this.logRequest('DELETE', `/projects/${projectId}`)

        return this.executeRequest(async () => {
            const { error } = await this.client
                .from('projects')
                .delete()
                .eq('id', projectId)

            if (error) {
                throw new ServiceError(
                    `Failed to delete project: ${error.message}`,
                    500,
                    error
                )
            }

            this.logResponse('DELETE', `/projects/${projectId}`, 'Success')
        })
    }
}

// Export singleton instance
export const supabaseService = new SupabaseService()
