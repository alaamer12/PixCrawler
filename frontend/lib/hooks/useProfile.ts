/**
 * Profile Hooks
 * 
 * Custom React hooks for user profile-related data operations.
 * Provides hooks for fetching, updating profile, and deleting account.
 */

import { useState, useEffect, useCallback } from 'react'
import { supabaseService, apiService, type Profile } from '@/lib/services'
import { useToast } from '@/components/ui/use-toast'
import { useAuth } from '@/lib/auth/hooks'

interface UseProfileResult {
    profile: Profile | null
    loading: boolean
    error: Error | null
    refetch: () => Promise<void>
}

interface UseUpdateProfileResult {
    updateProfile: (updates: Partial<Omit<Profile, 'id' | 'createdAt' | 'updatedAt'>>) => Promise<Profile | null>
    loading: boolean
    error: Error | null
}

interface UseDeleteAccountResult {
    deleteAccount: () => Promise<boolean>
    loading: boolean
    error: Error | null
}

/**
 * Hook to fetch the current user's profile
 */
export function useProfile(userId?: string): UseProfileResult {
    const [profile, setProfile] = useState<Profile | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const fetchProfile = useCallback(async () => {
        if (!userId) {
            setLoading(false)
            return
        }

        setLoading(true)
        setError(null)

        const response = await supabaseService.getProfile(userId)

        if (response.error) {
            setError(response.error)
            setProfile(null)
        } else {
            setProfile(response.data)
        }

        setLoading(false)
    }, [userId])

    useEffect(() => {
        fetchProfile()
    }, [fetchProfile])

    return {
        profile,
        loading,
        error,
        refetch: fetchProfile,
    }
}

/**
 * Hook to update the current user's profile
 */
export function useUpdateProfile(userId: string): UseUpdateProfileResult {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<Error | null>(null)
    const { toast } = useToast()
    const { updateUser } = useAuth()

    const updateProfile = useCallback(
        async (updates: Partial<Omit<Profile, 'id' | 'createdAt' | 'updatedAt'>>): Promise<Profile | null> => {
            setLoading(true)
            setError(null)

            const response = await supabaseService.updateProfile(userId, updates)

            if (response.error) {
                setError(response.error)
                toast({
                    title: 'Error',
                    description: 'Failed to update profile. Please try again.',
                    variant: 'destructive',
                })
                setLoading(false)
                return null
            }

            // Update global auth state
            if (response.data) {
                updateUser({
                    email: response.data.email,
                    profile: {
                        ...response.data,
                        fullName: response.data.fullName ?? undefined,
                        avatarUrl: response.data.avatarUrl ?? undefined,
                    },
                })
            }

            toast({
                title: 'Success',
                description: 'Profile updated successfully',
            })

            setLoading(false)
            return response.data
        },
        [userId, toast, updateUser]
    )

    return {
        updateProfile,
        loading,
        error,
    }
}

/**
 * Hook to delete the current user's account
 */
export function useDeleteAccount(): UseDeleteAccountResult {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<Error | null>(null)
    const { toast } = useToast()
    const { signOut } = useAuth()

    const deleteAccount = useCallback(async (): Promise<boolean> => {
        setLoading(true)
        setError(null)

        const response = await apiService.deleteAccount()

        if (response.error) {
            setError(response.error)
            toast({
                title: 'Error',
                description: 'Failed to delete account. Please try again.',
                variant: 'destructive',
            })
            setLoading(false)
            return false
        }

        toast({
            title: 'Account deleted',
            description: 'Your account has been permanently deleted',
        })

        // Sign out and redirect
        setTimeout(async () => {
            await signOut()
            window.location.href = '/'
        }, 1000)

        setLoading(false)
        return true
    }, [toast, signOut])

    return {
        deleteAccount,
        loading,
        error,
    }
}
