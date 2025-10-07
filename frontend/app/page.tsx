import {createClient} from '@/lib/supabase/server'
import {redirect} from 'next/navigation'
import {Features, Hero, HowItWorks, UseCases,} from '@/components/LandingPage'

export default async function HomePage() {
  const supabase = await createClient()

  const {
    data: {user},
  } = await supabase.auth.getUser()

  // Redirect authenticated users to dashboard
  if (user) {
    redirect('/dashboard')
  }

  return (
    <>
      <Hero/>
      <Features/>
      <HowItWorks/>
      <UseCases/>
    </>
  )
}
