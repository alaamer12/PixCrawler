/**
 * Global Error Boundary
 * 
 * Catches errors in the component tree and displays a fallback UI.
 * Integrates with error handler for logging and user-friendly messages.
 */

'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle, Home, RefreshCw } from 'lucide-react'
import { ErrorHandler } from '@/lib/utils/error-handler'

interface Props {
    children: ReactNode
    fallback?: (error: Error, reset: () => void) => ReactNode
}

interface State {
    hasError: boolean
    error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    }

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        // Log error to error tracking service
        ErrorHandler.logError(error, {
            componentStack: errorInfo.componentStack,
            errorBoundary: 'GlobalErrorBoundary',
        })
    }

    private handleReset = () => {
        this.setState({ hasError: false, error: null })
    }

    private handleGoHome = () => {
        window.location.href = '/'
    }

    public render() {
        if (this.state.hasError && this.state.error) {
            // Use custom fallback if provided
            if (this.props.fallback) {
                return this.props.fallback(this.state.error, this.handleReset)
            }

            // Default error UI
            const errorMessage = ErrorHandler.getUserFriendlyMessage(this.state.error)

            return (
                <div className="min-h-screen flex items-center justify-center p-4 bg-background">
                    <Card className="max-w-lg w-full">
                        <CardHeader>
                            <div className="flex items-center gap-3 mb-2">
                                <div className="rounded-full bg-destructive/10 p-2">
                                    <AlertTriangle className="h-6 w-6 text-destructive" />
                                </div>
                                <CardTitle className="text-2xl">Something went wrong</CardTitle>
                            </div>
                            <CardDescription className="text-base">
                                {errorMessage}
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {process.env.NODE_ENV === 'development' && (
                                <details className="rounded-lg border p-4 bg-muted/50">
                                    <summary className="cursor-pointer font-medium text-sm mb-2">
                                        Error Details (Development Only)
                                    </summary>
                                    <pre className="text-xs overflow-auto max-h-48 mt-2">
                                        {this.state.error.stack}
                                    </pre>
                                </details>
                            )}
                            <div className="flex items-center gap-2">
                                <Button onClick={this.handleReset} variant="default" className="flex-1">
                                    <RefreshCw className="h-4 w-4 mr-2" />
                                    Try Again
                                </Button>
                                <Button onClick={this.handleGoHome} variant="outline" className="flex-1">
                                    <Home className="h-4 w-4 mr-2" />
                                    Go Home
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )
        }

        return this.props.children
    }
}

// Hook-based error boundary for functional components
export function useErrorHandler() {
    const [error, setError] = React.useState<Error | null>(null)

    React.useEffect(() => {
        if (error) {
            throw error
        }
    }, [error])

    return setError
}
