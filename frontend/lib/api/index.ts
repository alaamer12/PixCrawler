/**
 * API Service Layer
 * Provides type-safe API methods for all backend endpoints
 */

import { apiClient } from './client'
import type { Project, CrawlJob, Notification } from '@/lib/db/schema'

/**
 * Projects API
 */
export const projectsApi = {
  getAll: async () => {
    return apiClient.get<Project[]>('/projects')
  },

  getById: async (id: string) => {
    return apiClient.get<Project>(`/projects/${id}`)
  },

  create: async (data: { name: string; description?: string }) => {
    return apiClient.post<Project>('/projects', data)
  },

  update: async (id: string, data: Partial<Project>) => {
    return apiClient.patch<Project>(`/projects/${id}`, data)
  },

  delete: async (id: string) => {
    return apiClient.delete(`/projects/${id}`)
  },
}

/**
 * Datasets API
 */
export const datasetsApi = {
  getByProject: async (projectId: string) => {
    return apiClient.get(`/projects/${projectId}/datasets`)
  },

  getById: async (projectId: string, datasetId: string) => {
    return apiClient.get(`/projects/${projectId}/datasets/${datasetId}`)
  },

  create: async (projectId: string, data: unknown) => {
    return apiClient.post(`/projects/${projectId}/datasets`, data)
  },

  delete: async (projectId: string, datasetId: string) => {
    return apiClient.delete(`/projects/${projectId}/datasets/${datasetId}`)
  },
}

/**
 * Jobs API
 */
export const jobsApi = {
  getAll: async () => {
    return apiClient.get<CrawlJob[]>('/jobs')
  },

  getById: async (jobId: string) => {
    return apiClient.get<CrawlJob>(`/jobs/${jobId}`)
  },

  start: async (datasetId: string) => {
    return apiClient.post<CrawlJob>(`/jobs/start`, { datasetId })
  },

  cancel: async (jobId: string) => {
    return apiClient.post(`/jobs/${jobId}/cancel`)
  },

  getLogs: async (jobId: string) => {
    return apiClient.get(`/jobs/${jobId}/logs`)
  },
}

/**
 * Notifications API
 */
export const notificationsApi = {
  getAll: async () => {
    return apiClient.get<Notification[]>('/notifications')
  },

  markAsRead: async (notificationId: number) => {
    return apiClient.patch(`/notifications/${notificationId}`, { is_read: true })
  },

  markAllAsRead: async () => {
    return apiClient.post('/notifications/mark-all-read')
  },

  delete: async (notificationId: number) => {
    return apiClient.delete(`/notifications/${notificationId}`)
  },
}

/**
 * Export API client
 */
export { apiClient }
