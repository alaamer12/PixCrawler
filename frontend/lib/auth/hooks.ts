'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { authService, type AuthUser } from './index'

import { useAuthContext } from '@/components/providers/auth-provider'

export function useAuth() {
  const { user, loading, signOut, updateUser } = useAuthContext()

  return {
    user,
    loading,
    signOut,
    updateUser,
    isAuthenticated: !!user,
  }
}

export function useRequireAuth(redirectTo = '/login') {
  const { user, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Skip redirect if dev bypass is enabled
    const isDevBypass = process.env.NODE_ENV === 'development' &&
      searchParams.get('dev_bypass') === 'true'

    if (!loading && !user && !isDevBypass) {
      router.push(redirectTo)
    }
  }, [user, loading, router, redirectTo, searchParams])

  return { user, loading }
}
