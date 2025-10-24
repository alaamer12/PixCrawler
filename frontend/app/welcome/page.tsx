import {createClient} from '@/lib/supabase/server'
import {redirect} from 'next/navigation'
import {WelcomeFlow} from './welcome-flow'
import {getDevBypassFromSearchParams} from '@/lib/dev-utils'

interface Props {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export default async function WelcomePage({searchParams}: Props) {
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

  const {isEnabled: isDevBypass, mockUser} = getDevBypassFromSearchParams(urlSearchParams)

  // If dev bypass is enabled, use mock user
  if (isDevBypass) {
    return <WelcomeFlow user={mockUser}/>
  }

  const supabase = await createClient()

  const {
    data: {user},
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Check if user has already completed onboarding
  const {data: profile} = await supabase
    .from('profiles')
    .select('onboarding_completed')
    .eq('id', user.id)
    .single()

  if (profile?.onboarding_completed) {
    redirect('/dashboard')
  }

  return <WelcomeFlow user={user}/>
}
