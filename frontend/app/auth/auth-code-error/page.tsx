import Link from 'next/link'
import {AlertCircle, ArrowLeft} from 'lucide-react'
import {Button} from '@/components/ui/button'

export default function AuthCodeErrorPage() {
  return (
    <div className="flex min-h-[calc(100vh-140px)] flex-col items-center justify-center gap-6 p-6 md:p-10">
      <div className="flex w-full max-w-md flex-col gap-6 text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex size-16 items-center justify-center rounded-full bg-destructive/10">
            <AlertCircle className="size-8 text-destructive"/>
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-bold tracking-tight">Authentication Error</h1>
            <p className="text-sm text-muted-foreground">
              Sorry, we couldn't complete your authentication. This could be due to an expired or invalid link.
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <Button asChild className="w-full">
            <Link href="/login">
              Try Again
            </Link>
          </Button>
          <Button asChild variant="outline" className="w-full">
            <Link href="/" className="inline-flex items-center gap-2">
              <ArrowLeft className="size-4"/>
              Back to Home
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
