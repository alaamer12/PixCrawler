'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { authService, type AuthUser } from '@/lib/auth'

interface AuthContextType {
    user: AuthUser | null
    loading: boolean
    signOut: () => Promise<void>
    updateUser: (updates: Partial<AuthUser>) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(null)
    const [loading, setLoading] = useState(true)
    const router = useRouter()
    const searchParams = useSearchParams()

    useEffect(() => {
        // Check for dev bypass
        const isDevBypass = process.env.NODE_ENV === 'development' &&
            searchParams.get('dev_bypass') === 'true'

        if (isDevBypass) {
            // Create mock user for dev bypass
            const mockUser: AuthUser = {
                id: 'dev-user-123',
                email: 'dev@pixcrawler.dev',
                aud: 'authenticated',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                app_metadata: {},
                user_metadata: { full_name: 'Dev User' },
                profile: {
                    id: 'dev-user-123',
                    email: 'dev@pixcrawler.dev',
                    fullName: 'Dev User',
                    avatarUrl: 'https://github.com/shadcn.png',
                    role: 'user'
                }
            }
            setUser(mockUser)
            setLoading(false)
            return
        }

        // Get initial user
        authService.getCurrentUser().then((user) => {
            setUser(user)
            setLoading(false)
        })

        // Listen for auth changes
        const { data: { subscription } } = authService.onAuthStateChange((user) => {
            setUser(user)
            setLoading(false)
        })

        return () => subscription.unsubscribe()
    }, [searchParams])

    const signOut = async () => {
        try {
            await authService.signOut()
            router.push('/')
            router.refresh()
        } catch (error) {
            console.error('Error signing out:', error)
        }
    }

    const updateUser = (updates: Partial<AuthUser>) => {
        setUser(prev => prev ? { ...prev, ...updates } : null)
    }

    return (
        <AuthContext.Provider value={{ user, loading, signOut, updateUser }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuthContext() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuthContext must be used within an AuthProvider')
    }
    return context
}
