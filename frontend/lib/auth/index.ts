import { createClient } from '@/lib/supabase/client'
import { createClient as createServerClient } from '@/lib/supabase/server'
import type { User } from '@supabase/supabase-js'

export interface AuthUser extends User {
  profile?: {
    id: string
    email: string
    fullName?: string
    avatarUrl?: string
    role: string
  }
}

export class AuthService {
  private supabase = createClient()

  // Sign up with email and password
  async signUp(email: string, password: string, fullName?: string) {
    const { data, error } = await this.supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    })

    if (error) throw error
    return data
  }

  // Sign in with email and password
  async signIn(email: string, password: string) {
    const { data, error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) throw error
    return data
  }

  // Sign in with OAuth provider
  async signInWithOAuth(provider: 'github' | 'google', redirectTo?: string) {
    const { data, error } = await this.supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: redirectTo || `${window.location.origin}/auth/callback`,
      },
    })

    if (error) throw error
    return data
  }

  // Sign out
  async signOut() {
    const { error } = await this.supabase.auth.signOut()
    if (error) throw error
  }

  // Reset password
  async resetPassword(email: string) {
    const { data, error } = await this.supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    })

    if (error) throw error
    return data
  }

  // Update password
  async updatePassword(password: string) {
    const { data, error } = await this.supabase.auth.updateUser({
      password,
    })

    if (error) throw error
    return data
  }

  // Get current user
  async getCurrentUser(): Promise<AuthUser | null> {
    const { data: { user }, error } = await this.supabase.auth.getUser()
    
    if (error || !user) return null

    // Fetch user profile
    const { data: profile } = await this.supabase
      .from('profiles')
      .select('*')
      .eq('id', user.id)
      .single()

    return {
      ...user,
      profile,
    }
  }

  // Listen to auth state changes
  onAuthStateChange(callback: (user: AuthUser | null) => void) {
    return this.supabase.auth.onAuthStateChange(async (event, session) => {
      if (session?.user) {
        const user = await this.getCurrentUser()
        callback(user)
      } else {
        callback(null)
      }
    })
  }
}

// Server-side auth utilities
export async function getServerUser(): Promise<AuthUser | null> {
  const supabase = await createServerClient()
  
  const { data: { user }, error } = await supabase.auth.getUser()
  
  if (error || !user) return null

  // Fetch user profile
  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  return {
    ...user,
    profile,
  }
}

export const authService = new AuthService()