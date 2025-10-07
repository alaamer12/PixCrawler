import {createClient} from '@/lib/supabase/server'
import type {User} from '@supabase/supabase-js'

export interface AuthUser extends User {
  profile?: {
    id: string
    email: string
    fullName?: string
    avatarUrl?: string
    role: string
  }
}

// Server-side auth utilities
export async function getServerUser(): Promise<AuthUser | null> {
  const supabase = await createClient()

  const {data: {user}, error} = await supabase.auth.getUser()

  if (error || !user) return null

  // Fetch user profile
  const {data: profile} = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  return {
    ...user,
    profile,
  }
}
