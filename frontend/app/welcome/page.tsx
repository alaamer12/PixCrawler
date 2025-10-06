import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { WelcomeFlow } from './welcome-flow'

export default async function WelcomePage() {
  const supabase = await createClient()
  
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Check if user has already completed onboarding
  const { data: profile } = await supabase
    .from('profiles')
    .select('onboarding_completed')
    .eq('id', user.id)
    .single()

  if (profile?.onboarding_completed) {
    redirect('/dashboard')
  }

  return <WelcomeFlow user={user} />
}