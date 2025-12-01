/**
 * API Service
 * 
 * Centralized service for all REST API operations.
 * Handles notifications, datasets, jobs, and account management.
 */

import { BaseService, ServiceResponse, ServiceError } from './base.service'
import type { Notification } from '@/lib/db/schema'

export interface NotificationFilter {
    unread?: boolean
}

export interface PaginatedResponse<T> {
    data: T[]
    total: number
    page: number
    pageSize: number
    hasMore: boolean
}

export interface CreateNotificationInput {
    userId: string
    type: string
    title: string
    message: string
    icon?: string
    iconColor?: string
    actionUrl?: string
    metadata?: Record<string, any>
}

export class ApiService extends BaseService {
    private baseUrl: string

    constructor(baseUrl: string = '/api') {
        super()
        this.baseUrl = baseUrl

        // Add auth interceptor
        this.addRequestInterceptor(async (config) => {
            // Add authentication headers if needed
            // const token = await getAuthToken()
            // config.headers = {
            //   ...config.headers,
            //   'Authorization': `Bearer ${token}`
            // }
            return config
        })

        // Add error response interceptor
        this.addResponseInterceptor(async (response) => {
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new ServiceError(
                    errorData.message || response.statusText,
                    response.status
                )
            }
            return response
        })
    }

    /**
     * Make a fetch request with error handling
     */
    private async fetch<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`
        this.logRequest(options.method || 'GET', endpoint, options.body)

        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        }

        const response = await fetch(url, config)
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new ServiceError(
                errorData.message || response.statusText,
                response.status
            )
        }

        const data = await response.json()
        this.logResponse(options.method || 'GET', endpoint, data)

        return data
    }

    // ============================================================================
    // Notification Operations
    // ============================================================================

    /**
     * Get all notifications for the current user
     */
    async getNotifications(
        filter?: NotificationFilter
    ): Promise<ServiceResponse<Notification[]>> {
        const queryParams = new URLSearchParams()
        if (filter?.unread) {
            queryParams.append('unread', 'true')
        }

        const endpoint = `/notifications${queryParams.toString() ? `?${queryParams}` : ''}`

        return this.executeRequest(async () => {
            const response = await this.fetch<{ notifications: Notification[] }>(endpoint)
            return response.notifications
        })
    }

    /**
     * Get a single notification by ID
     */
    async getNotification(id: number): Promise<ServiceResponse<Notification>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ notification: Notification }>(
                `/notifications/${id}`
            )
            return response.notification
        })
    }

    /**
     * Mark a notification as read
     */
    async markNotificationAsRead(id: number): Promise<ServiceResponse<Notification>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ notification: Notification }>(
                `/notifications/${id}`,
                {
                    method: 'PATCH',
                    body: JSON.stringify({ isRead: true }),
                }
            )
            return response.notification
        })
    }

    /**
     * Mark all notifications as read
     */
    async markAllNotificationsAsRead(): Promise<ServiceResponse<void>> {
        return this.executeRequest(async () => {
            await this.fetch('/notifications/mark-all-read', {
                method: 'POST',
            })
        })
    }

    /**
     * Delete a notification
     */
    async deleteNotification(id: number): Promise<ServiceResponse<void>> {
        return this.executeRequest(async () => {
            await this.fetch(`/notifications/${id}`, {
                method: 'DELETE',
            })
        })
    }

    /**
     * Create a notification
     */
    async createNotification(
        input: CreateNotificationInput
    ): Promise<ServiceResponse<Notification>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ notification: Notification }>(
                '/notifications',
                {
                    method: 'POST',
                    body: JSON.stringify(input),
                }
            )
            return response.notification
        })
    }

    // ============================================================================
    // Account Operations
    // ============================================================================

    /**
     * Delete user account
     */
    async deleteAccount(): Promise<ServiceResponse<void>> {
        return this.executeRequest(async () => {
            await this.fetch('/account/delete', {
                method: 'DELETE',
            })
        }, { retries: 0 }) // Don't retry account deletion
    }

    /**
     * Export user data
     */
    async exportUserData(): Promise<ServiceResponse<Blob>> {
        return this.executeRequest(async () => {
            const response = await fetch(`${this.baseUrl}/account/export`, {
                method: 'GET',
            })

            if (!response.ok) {
                throw new ServiceError(
                    'Failed to export user data',
                    response.status
                )
            }

            return await response.blob()
        })
    }

    // ============================================================================
    // Project Operations (API endpoints)
    // ============================================================================

    /**
     * Get projects via API (alternative to Supabase)
     */
    async getProjectsViaApi(): Promise<ServiceResponse<any[]>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ projects: any[] }>('/projects')
            return response.projects
        })
    }

    /**
     * Create project via API
     */
    async createProjectViaApi(data: any): Promise<ServiceResponse<any>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ project: any }>('/projects', {
                method: 'POST',
                body: JSON.stringify(data),
            })
            return response.project
        })
    }

    // ============================================================================
    // Dataset Operations
    // ============================================================================

    /**
     * Get datasets for a project
     */
    async getDatasets(projectId: string): Promise<ServiceResponse<any[]>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ datasets: any[] }>(
                `/projects/${projectId}/datasets`
            )
            return response.datasets
        })
    }

    /**
     * Create a dataset
     */
    async createDataset(projectId: string, data: any): Promise<ServiceResponse<any>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ dataset: any }>(
                `/projects/${projectId}/datasets`,
                {
                    method: 'POST',
                    body: JSON.stringify(data),
                }
            )
            return response.dataset
        })
    }

    // ============================================================================
    // Job Operations
    // ============================================================================

    /**
     * Get jobs for a dataset
     */
    async getJobs(datasetId: string): Promise<ServiceResponse<any[]>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ jobs: any[] }>(
                `/datasets/${datasetId}/jobs`
            )
            return response.jobs
        })
    }

    /**
     * Get all jobs for the current user
     */
    async getAllJobs(): Promise<ServiceResponse<any[]>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ jobs: any[] }>('/jobs')
            return response.jobs
        })
    }

    /**
     * Start a job
     */
    async startJob(jobId: string): Promise<ServiceResponse<any>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ job: any }>(`/jobs/${jobId}/start`, {
                method: 'POST',
            })
            return response.job
        })
    }

    /**
     * Pause a job
     */
    async pauseJob(jobId: string): Promise<ServiceResponse<any>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ job: any }>(`/jobs/${jobId}/pause`, {
                method: 'POST',
            })
            return response.job
        })
    }

    /**
     * Cancel a job
     */
    async cancelJob(jobId: string): Promise<ServiceResponse<any>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ job: any }>(`/jobs/${jobId}/cancel`, {
                method: 'POST',
            })
            return response.job
        })
    }

    // ============================================================================
    // Activity Operations
    // ============================================================================

    /**
     * Get recent activities
     */
    async getActivities(limit: number = 10): Promise<ServiceResponse<any[]>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ activities: any[] }>(
                `/activities?limit=${limit}`
            )
            return response.activities
        })
    }

    // ============================================================================
    // Stats Operations
    // ============================================================================

    /**
     * Get dashboard statistics
     */
    async getDashboardStats(): Promise<ServiceResponse<any>> {
        return this.executeRequest(async () => {
            const response = await this.fetch<{ stats: any }>('/stats/dashboard')
            return response.stats
        })
    }
}

// Export singleton instance
export const apiService = new ApiService()
