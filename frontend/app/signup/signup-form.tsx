'use client'

import { useState } from 'react'
import { authService } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { OAuthButtons } from '@/components/auth/oauth-buttons'
import { PasswordStrengthMeter } from '@/components/strength-meter'

export function SignupForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')

    try {
      const result = await authService.signUp(email, password, fullName)

      // Check if email confirmation is disabled (user is auto-confirmed)
      const isAutoConfirmed = result.user && result.user.email_confirmed_at !== null

      if (isAutoConfirmed) {
        // User is auto-confirmed, redirect to welcome/dashboard
        setMessage('Account created successfully! Redirecting...')
        setTimeout(() => {
          router.push('/welcome')
          router.refresh()
        }, 1000)
      } else {
        // Email confirmation required
        setMessage('Check your email for the confirmation link!')
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-card border border-border rounded-xl shadow-lg p-6 md:p-8 space-y-4">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-bold tracking-tight">Create your account</h1>
        <p className="text-sm text-muted-foreground">Start building your image datasets today</p>
      </div>

      <form className="space-y-3" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label htmlFor="fullName" className="text-sm font-medium">
              Full Name
            </label>
            <input
              id="fullName"
              name="fullName"
              type="text"
              required
              className="w-full px-3 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              placeholder="Enter your full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="w-full px-3 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <label htmlFor="password" className="text-sm font-medium">
            Password
          </label>
          <PasswordStrengthMeter
            value={password}
            onValueChange={setPassword}
            showText={true}
            showRequirements={true}
            showRequirementsAsTooltip={true}
            segments={4}
            placeholder="Enter a strong password"
            showPasswordToggle={true}
            inputClassName="px-3 py-2.5"
          />
        </div>

        {error && (
          <div
            className="bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-lg p-2.5 text-center">
            {error}
          </div>
        )}

        {message && (
          <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-lg p-2.5 text-center">
            {message}
          </div>
        )}

        <Button
          type="submit"
          loading={loading}
          loadingText="Creating account..."
          variant="brand"
          size="lg"
          className="w-full"
        >
          Create account
        </Button>
      </form>

      <OAuthButtons mode="signup" />

      <div className="text-center pt-3 border-t border-border">
        <p className="text-sm text-muted-foreground">
          Already have an account?{' '}
          <a href="/login" className="font-medium text-primary hover:underline">
            Sign in
          </a>
        </p>
      </div>
    </div>
  )
}
