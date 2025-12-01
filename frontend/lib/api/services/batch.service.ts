import { apiClient } from '../client'

export const batchApi = {
    deleteProjects: async (ids: number[]) => {
        return apiClient.post<{ deleted_count: number; failed_ids: number[] }>(
            '/batch/projects/batch-delete',
            { ids }
        )
    },
}
