'use client'

import {useRouter} from 'next/navigation'
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card'
import {Button} from '@/components/ui/button'
import {ArrowLeft, HelpCircle, RefreshCw, XCircle} from 'lucide-react'

export const PaymentCancel = () => {
  const router = useRouter()

  return (
    <div
      className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full space-y-6">
        {/* Cancel Card */}
        <Card className="text-center">
          <CardHeader>
            <div className="text-red-500 mb-4">
              <XCircle className="w-16 h-16 mx-auto"/>
            </div>
            <CardTitle className="text-2xl">Payment Cancelled</CardTitle>
            <p className="text-muted-foreground">
              Your payment was cancelled. No charges have been made to your account.
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* What Happened */}
            <div className="bg-muted/50 rounded-lg p-4 text-left">
              <h3 className="font-semibold mb-3">What happened?</h3>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>• You cancelled the payment process</p>
                <p>• No payment method was charged</p>
                <p>• Your account remains unchanged</p>
                <p>• You can try again at any time</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                onClick={() => router.push('/pricing')}
                className="flex-1"
                leftIcon={<RefreshCw className="w-4 h-4"/>}
              >
                Try Again
              </Button>
              <Button
                variant="outline"
                onClick={() => router.back()}
                className="flex-1"
                leftIcon={<ArrowLeft className="w-4 h-4"/>}
              >
                Go Back
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Help Card */}
        <Card>
          <CardContent className="pt-6">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <HelpCircle className="w-4 h-4"/>
              Need Assistance?
            </h3>
            <div className="text-sm text-muted-foreground space-y-3">
              <p>
                If you're experiencing issues with the payment process or have questions
                about our pricing plans, we're here to help.
              </p>

              <div
                className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                  Common reasons for payment cancellation:
                </h4>
                <ul className="text-blue-800 dark:text-blue-200 text-xs space-y-1">
                  <li>• Browser back button was pressed</li>
                  <li>• Payment window was closed</li>
                  <li>• Session timeout occurred</li>
                  <li>• Network connectivity issues</li>
                </ul>
              </div>

              <div className="flex gap-4 mt-4">
                <Button variant="outline" size="sm">
                  Contact Support
                </Button>
                <Button variant="outline" size="sm">
                  View FAQ
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => router.push('/dashboard')}
                >
                  Dashboard
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
