import {createClient} from '@/lib/supabase/server'
import {redirect} from 'next/navigation'
import {Database} from 'lucide-react'
import {Logo} from '@/components/shared/Logo'
import {ForgotPasswordForm} from './forgot-password-form'

export default async function ForgotPasswordPage() {
  const supabase = await createClient()

  const {
    data: {user},
  } = await supabase.auth.getUser()

  if (user) {
    redirect('/dashboard')
  }

  return (
    <div className="flex min-h-[calc(100vh-140px)] flex-col items-center justify-center gap-6 p-6 md:p-10">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <a href="/" className="self-center hover:opacity-90 transition-opacity" aria-label="PixCrawler Home">
          <Logo showIcon showText size="md"/>
        </a>
        <ForgotPasswordForm/>
      </div>
    </div>
  )
}
