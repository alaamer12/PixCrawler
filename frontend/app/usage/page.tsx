'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Check, Copy, Terminal } from 'lucide-react'
import { useState, Suspense } from 'react'
import { cn } from '@/lib/utils'

function UsageContent() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const jobId = searchParams.get('jobId') || 'your_job_id'
    const apiKey = 'your_api_key' // In a real app, we might fetch this or show a placeholder

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
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
            <Card className="w-full max-w-2xl">
                <CardHeader>
                    <CardTitle className="text-2xl">Dataset Created Successfully! 🎉</CardTitle>
                    <CardDescription>
                        Your dataset is ready. Here's how to use it in your Python projects.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">

                    {/* Step 1: Install */}
                    <div className="space-y-2">
                        <h3 className="font-medium flex items-center gap-2">
                            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">1</span>
                            Install the SDK
                        </h3>
                        <div className="relative rounded-md bg-muted p-4 font-mono text-sm">
                            <div className="flex items-center justify-between">
                                <span className="flex items-center gap-2">
                                    <Terminal className="h-4 w-4 text-muted-foreground" />
                                    {installCommand}
                                </span>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => copyToClipboard(installCommand, setCopiedInstall)}
                                >
                                    {copiedInstall ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                </Button>
                            </div>
                        </div>
                    </div>

                    {/* Step 2: Code Snippet */}
                    <div className="space-y-2">
                        <h3 className="font-medium flex items-center gap-2">
                            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">2</span>
                            Use in your code
                        </h3>
                        <div className="relative rounded-md bg-muted p-4 font-mono text-sm">
                            <pre className="overflow-x-auto">
                                <code>{pythonCode}</code>
                            </pre>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="absolute right-2 top-2 h-8 w-8"
                                onClick={() => copyToClipboard(pythonCode, setCopiedCode)}
}

                            export default function UsagePage() {
    return (
                            <Suspense fallback={<div>Loading...</div>}>
                                <UsageContent />
                            </Suspense>
                            )
}
