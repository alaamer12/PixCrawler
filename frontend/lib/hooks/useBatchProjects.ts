import { useState, useCallback } from 'react'
import { batchApi } from '@/lib/api/services/batch.service'
import { useToast } from '@/components/ui/use-toast'
import { parseApiError } from '@/lib/api/errors'

export function useBatchProjects() {
    const [loading, setLoading] = useState(false)
    const { toast } = useToast()

    const deleteProjects = useCallback(async (ids: number[]) => {
        if (ids.length === 0) return

        setLoading(true)
        const { data, error } = await batchApi.deleteProjects(ids)

        if (error) {
            toast({
                title: 'Error',
                description: parseApiError(error),
                variant: 'destructive',
            })
            setLoading(false)
            return null
        }

        if (data) {
            const { deleted_count, failed_ids } = data

            if (failed_ids.length > 0) {
                toast({
                    title: 'Partial Success',
                    description: `⚠️ Deleted ${deleted_count} projects. Failed to delete ${failed_ids.length} projects.`,
                    variant: 'default',
                })
            } else {
                toast({
                    title: 'Success',
                    description: `Successfully deleted ${deleted_count} projects`,
                })
            }
        }

        setLoading(false)
        return data
    }, [toast])

    return { deleteProjects, loading }
}
