import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Database } from 'lucide-react'
import { ForgotPasswordForm } from './forgot-password-form'

export default async function ForgotPasswordPage() {
  const supabase = await createClient()
  
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (user) {
    redirect('/dashboard')
  }

  return (
    <div className="flex min-h-[calc(100vh-140px)] flex-col items-center justify-center gap-6 p-6 md:p-10">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <a href="/" className="flex items-center gap-2 self-center font-medium text-foreground hover:opacity-80 transition-opacity">
          <div className="bg-gradient-to-br from-primary to-secondary text-primary-foreground flex size-8 items-center justify-center rounded-lg shadow-lg">
            <Database className="size-5" />
          </div>
          <span className="text-xl font-bold">PixCrawler</span>
        </a>
        <ForgotPasswordForm />
      </div>
    </div>
  )
}