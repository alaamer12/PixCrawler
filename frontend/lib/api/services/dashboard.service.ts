import { apiClient } from '../client'

export interface DashboardStats {
    total_projects: number
    active_jobs: number
    total_datasets: number
    total_images: number
    storage_used: string
    processing_speed: string
    credits_remaining: number
}

export const dashboardApi = {
    getStats: async () => {
        return apiClient.get<DashboardStats>('/dashboard/stats')
    },
}
