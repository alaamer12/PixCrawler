import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { WelcomeFlow } from './welcome-flow'
import { getDevBypassFromSearchParams } from '@/lib/dev-utils'

interface Props {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export default async function WelcomePage({ searchParams }: Props) {
  const params = await searchParams
  const urlSearchParams = new URLSearchParams(
    Object.entries(params).reduce((acc, [key, value]) => {
      if (typeof value === 'string') {
        acc[key] = value
      } else if (Array.isArray(value)) {
        acc[key] = value[0] || ''
      }
      return acc
    }, {} as Record<string, string>)
  )

  const { isEnabled: isDevBypass, mockUser } = getDevBypassFromSearchParams(urlSearchParams)

  // If dev bypass is enabled, use mock user
  if (isDevBypass) {
    return <WelcomeFlow user={mockUser} />
  }

  const supabase = await createClient()

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Check if user has already completed onboarding using direct DB query
  // We use the server client here to ensure we have the correct session context
  const { data: profile, error } = await supabase
    .from('profiles')
    .select('onboarding_completed')
    .eq('id', user.id)
    .single()

  if (error) {
    console.error('Error fetching profile:', error)
    // Continue to welcome flow if profile fetch fails
  }

  if (profile?.onboarding_completed) {
    redirect('/dashboard')
  }

  return <WelcomeFlow user={user} />
}
