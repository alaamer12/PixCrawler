'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Check, Copy, Terminal, ArrowLeft, ExternalLink } from 'lucide-react'
import { useState, Suspense } from 'react'

function UsageContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const jobId = searchParams.get('jobId') || 'your_job_id'
    // TODO: implement this
    const apiKey = 'your_api_key' // In a real app, fetch this securely

    const [copiedInstall, setCopiedInstall] = useState(false)
    const [copiedCode, setCopiedCode] = useState(false)

    const installCommand = 'pip install pixcrawler-sdk'
    const pythonCode = `from pixcrawler import load_dataset

# Load your dataset
dataset = load_dataset(
    job_id="${jobId}",
    api_key="${apiKey}"
)

# Iterate through images
for image, label in dataset:
    print(f"Image shape: {image.shape}, Label: {label}")`

    const copyToClipboard = (text: string, setCopied: (val: boolean) => void) => {
        navigator.clipboard.writeText(text)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
            <div className="w-full max-w-3xl space-y-4">
                {/* Back Button */}
                <Button
                    variant="ghost"
                    onClick={() => router.push('/')}
                    className="gap-2"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Dashboard
                </Button>

                <Card className="shadow-lg border-2">
                    <CardHeader className="space-y-3 pb-6">
                        <div className="flex items-center gap-3">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
                                <Check className="h-6 w-6 text-green-500" />
                            </div>
                            <div>
                                <CardTitle className="text-3xl">Dataset Created Successfully!</CardTitle>
                                <CardDescription className="text-base mt-1">
                                    Job ID: <code className="font-mono bg-muted px-2 py-0.5 rounded text-xs">{jobId}</code>
                                </CardDescription>
                            </div>
                        </div>
                        <p className="text-muted-foreground">
                            Your dataset is ready to use. Follow the steps below to integrate it into your Python projects.
                        </p>
                    </CardHeader>

                    <CardContent className="space-y-6">
                        {/* Step 1: Install */}
                        <div className="space-y-3">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                                    1
                                </span>
                                Install the SDK
                            </h3>
                            <div className="relative rounded-lg bg-slate-950 p-4 font-mono text-sm border">
                                <div className="flex items-center justify-between">
                                    <span className="flex items-center gap-2 text-green-400">
                                        <Terminal className="h-4 w-4" />
                                        <span className="text-slate-100">{installCommand}</span>
                                    </span>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8 hover:bg-slate-800"
                                        onClick={() => copyToClipboard(installCommand, setCopiedInstall)}
                                    >
                                        {copiedInstall ? (
                                            <Check className="h-4 w-4 text-green-400" />
                                        ) : (
                                            <Copy className="h-4 w-4 text-slate-400" />
                                        )}
                                    </Button>
                                </div>
                            </div>
                        </div>

                        {/* Step 2: Code Snippet */}
                        <div className="space-y-3">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                                    2
                                </span>
                                Use in your code
                            </h3>
                            <div className="relative rounded-lg bg-slate-950 p-4 font-mono text-sm border">
                                <pre className="overflow-x-auto text-slate-100">
                                    <code>{pythonCode}</code>
                                </pre>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="absolute right-2 top-2 h-8 w-8 hover:bg-slate-800"
                                    onClick={() => copyToClipboard(pythonCode, setCopiedCode)}
                                >
                                    {copiedCode ? (
                                        <Check className="h-4 w-4 text-green-400" />
                                    ) : (
                                        <Copy className="h-4 w-4 text-slate-400" />
                                    )}
                                </Button>
                            </div>
                        </div>

                        {/* Additional Info */}
                        <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-4 space-y-2">
                            <h4 className="font-semibold text-sm text-blue-700 dark:text-blue-400">
                                📚 Need Help?
                            </h4>
                            <p className="text-sm text-muted-foreground">
                                Check out our documentation for more examples and advanced usage.
                            </p>
                            <Button variant="link" className="h-auto p-0 text-blue-600 dark:text-blue-400">
                                View Documentation
                                <ExternalLink className="ml-1 h-3 w-3" />
                            </Button>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-3 pt-2">
                            <Button
                                className="flex-1"
                                onClick={() => router.push('/datasets')}
                            >
                                View All Datasets
                            </Button>
                            <Button
                                variant="outline"
                                className="flex-1"
                                onClick={() => router.push('/create')}
                            >
                                Create Another Dataset
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default function UsagePage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
                    <p className="text-muted-foreground">Loading...</p>
                </div>
            </div>
        }>
            <UsageContent />
        </Suspense>
    )
}