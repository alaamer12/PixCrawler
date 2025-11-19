'use client'

import {useEffect, useState} from 'react'
import {useRouter, useSearchParams} from 'next/navigation'
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card'
import {Button} from '@/components/ui/button'
import {Badge} from '@/components/ui/badge'
import {ArrowRight, CheckCircle, Download, HelpCircle, Loader2} from 'lucide-react'
import {getPlanById} from '@/lib/payments/plans'

// Types
interface PaymentDetails {
  sessionId: string
  planName: string
  amount: number
  currency: string
  status: string
  credits?: number
  isSubscription: boolean
}

// Loading State Component
const LoadingState = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center">
      <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary"/>
      <p className="text-muted-foreground">Loading payment details...</p>
    </div>
  </div>
)

// Error State Component
const ErrorState = ({error, onRetry}: { error: string; onRetry: () => void }) => {
  const router = useRouter()

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6 text-center">
          <div className="text-red-500 mb-4">
            <CheckCircle className="w-12 h-12 mx-auto"/>
          </div>
          <h1 className="text-xl font-bold mb-2">Payment Error</h1>
          <p className="text-muted-foreground mb-4">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button onClick={() => router.push('/pricing')} variant="outline">
              Back to Pricing
            </Button>
            <Button onClick={onRetry}>Try Again</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Payment Details Row Component
const DetailRow = ({
                     label,
                     value,
                     variant = 'text'
                   }: {
  label: string
  value: string | number | any
  variant?: 'text' | 'badge-outline' | 'badge-success'
}) => (
  <div className="flex justify-between items-center">
    <span className="text-muted-foreground">{label}:</span>
    {variant === 'text' && <span className="font-semibold">{value}</span>}
    {variant === 'badge-outline' && <Badge variant="outline">{value}</Badge>}
    {variant === 'badge-success' && (
      <Badge variant="default" className="bg-green-500">{value}</Badge>
    )}
  </div>
)

// Payment Summary Component
const PaymentSummary = ({details}: { details: PaymentDetails }) => (
  <div className="bg-muted/50 rounded-lg p-4 space-y-3">
    <DetailRow label="Plan" value={details.planName}/>
    <DetailRow
      label="Amount"
      value={`$${details.amount.toFixed(2)} ${details.currency.toUpperCase()}`}
    />
    <DetailRow
      label="Type"
      value={details.isSubscription ? 'Subscription' : 'One-time'}
      variant="badge-outline"
    />
    <DetailRow
      label="Status"
      value={details.status}
      variant="badge-success"
    />
    {details.credits && (
      <DetailRow
        label="Credits Added"
        value={details.credits.toLocaleString()}
      />
    )}
    <DetailRow
      label="Transaction ID"
      value={
        <span className="font-mono text-xs">{details.sessionId.slice(-12)}</span>
      }
    />
  </div>
)

// Success Checklist Item Component
const ChecklistItem = ({text}: { text: string }) => (
  <div className="flex items-center gap-2">
    <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0"/>
    <span>{text}</span>
  </div>
)

// Next Steps Component
const NextSteps = ({hasCredits}: { hasCredits: boolean }) => (
  <div className="text-left space-y-4">
    <h3 className="font-semibold">What's Next?</h3>
    <div className="space-y-2 text-sm">
      <ChecklistItem text="Your account has been upgraded"/>
      {hasCredits && <ChecklistItem text="Credits have been added to your account"/>}
      <ChecklistItem text="You can now start building datasets"/>
      <ChecklistItem text="Receipt sent to your email"/>
    </div>
  </div>
)

// Action Buttons Component
const ActionButtons = ({isDevMode}: { isDevMode: boolean }) => {
  const router = useRouter()

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      <Button
        onClick={() => router.push(isDevMode ? '/dashboard?dev_bypass=true' : '/dashboard')}
        className="flex-1"
        rightIcon={<ArrowRight className="w-4 h-4"/>}
      >
        Go to Dashboard
      </Button>
      <Button
        variant="outline"
        onClick={() => router.push(isDevMode ? '/dashboard/billing?dev_bypass=true' : '/dashboard/billing')}
        className="flex-1"
        leftIcon={<Download className="w-4 h-4"/>}
      >
        View Receipt
      </Button>
    </div>
  )
}

// Success Header Component
const SuccessHeader = () => (
  <CardHeader>
    <div className="text-green-500 mb-4">
      <CheckCircle className="w-16 h-16 mx-auto"/>
    </div>
    <CardTitle className="text-2xl">Payment Successful!</CardTitle>
    <p className="text-muted-foreground">
      Thank you for your purchase. Your payment has been processed successfully.
    </p>
  </CardHeader>
)

// Help Section Component
const HelpSection = () => {
  const router = useRouter()

  return (
    <Card>
      <CardContent className="pt-6">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <HelpCircle className="w-4 h-4"/>
          Need Help?
        </h3>
        <div className="text-sm text-muted-foreground space-y-2">
          <p>
            If you have any questions about your purchase or need assistance getting started,
            our support team is here to help.
          </p>
          <div className="flex flex-wrap gap-3 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/contact')}
            >
              Contact Support
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/docs')}
            >
              View Documentation
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Success Content Component
const SuccessContent = ({details, isDevMode}: { details: PaymentDetails; isDevMode: boolean }) => (
  <div className="min-h-screen bg-gradient-to-br from-primary/5 to-secondary/5 flex items-center justify-center p-4">
    <div className="max-w-2xl w-full space-y-6">
      <Card className="text-center">
        <SuccessHeader/>
        <CardContent className="space-y-6">
          <PaymentSummary details={details}/>
          <NextSteps hasCredits={!!details.credits}/>
          <ActionButtons isDevMode={isDevMode}/>
        </CardContent>
      </Card>
      <HelpSection/>
    </div>
  </div>
)

// Custom Hook for Payment Data
const usePaymentDetails = (sessionId: string | null, isDevMode: boolean) => {
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string>('')

  const fetchPaymentDetails = async () => {
    // Dev mode bypass - create mock payment details
    if (isDevMode) {
      setIsLoading(true)
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulate loading

      setPaymentDetails({
        sessionId: 'dev_session_mock_123',
        planName: 'Pro Plan (Dev Mode)',
        amount: 29.99,
        currency: 'usd',
        status: 'paid',
        credits: 1000,
        isSubscription: true,
      })
      setIsLoading(false)
      return
    }

    if (!sessionId) {
      setError('No session ID provided')
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch(`/api/stripe/session/${sessionId}`)

      if (!response.ok) {
        throw new Error('Failed to fetch payment details')
      }

      const session = await response.json()
      const planId = session.metadata?.planId
      const plan = planId ? getPlanById(planId) : null

      setPaymentDetails({
        sessionId: session.id,
        planName: plan?.name || 'Unknown Plan',
        amount: session.amount_total / 100,
        currency: session.currency,
        status: session.payment_status,
        credits: plan?.credits,
        isSubscription: session.mode === 'subscription',
      })
    } catch (err) {
      setError('Failed to load payment details. Please try again.')
      console.error('Error fetching payment details:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchPaymentDetails()
  }, [sessionId, isDevMode])

  return {paymentDetails, isLoading, error, retry: fetchPaymentDetails}
}

// Main Component
export const PaymentSuccess = () => {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id')
  const isDevMode = process.env.NODE_ENV === 'development' && searchParams.get('dev_bypass') === 'true'
  const {paymentDetails, isLoading, error, retry} = usePaymentDetails(sessionId, isDevMode)

  if (isLoading) {
    return <LoadingState/>
  }

  if (error || !paymentDetails) {
    return <ErrorState error={error || 'Unable to load payment details'} onRetry={retry}/>
  }

  return <SuccessContent details={paymentDetails} isDevMode={isDevMode}/>
}
