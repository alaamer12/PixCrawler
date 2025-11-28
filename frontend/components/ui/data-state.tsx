/**
 * Data State Components
 * 
 * Reusable components for displaying loading, error, and empty states.
 */

import React from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { AlertCircle, Inbox, Loader2, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

// ============================================================================
// Loading State Component
// ============================================================================

interface LoadingStateProps {
    variant?: 'skeleton' | 'spinner'
    message?: string
    className?: string
    skeletonCount?: number
}

export function LoadingState({
    variant = 'skeleton',
    message = 'Loading...',
    className,
    skeletonCount = 3,
}: LoadingStateProps) {
    if (variant === 'spinner') {
        return (
            <div className={cn('flex flex-col items-center justify-center py-12', className)}>
                <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
                <p className="text-sm text-muted-foreground">{message}</p>
            </div>
        )
    }

    // Skeleton variant
    return (
        <div className={cn('space-y-4', className)}>
            {Array.from({ length: skeletonCount }).map((_, i) => (
                <div key={i} className="flex items-start gap-4">
                    <Skeleton className="h-12 w-12 rounded-lg" />
                    <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                    </div>
                </div>
            ))}
        </div>
    )
}

// ============================================================================
// Error State Component
// ============================================================================

interface ErrorStateProps {
    title?: string
    message: string
    onRetry?: () => void
    retryLabel?: string
    actions?: React.ReactNode
    className?: string
}

export function ErrorState({
    title = 'Something went wrong',
    message,
    onRetry,
    retryLabel = 'Try again',
    actions,
    className,
}: ErrorStateProps) {
    return (
        <Card className={cn('border-destructive/50', className)}>
            <CardContent className="flex flex-col items-center justify-center py-12">
                <div className="rounded-full bg-destructive/10 p-3 mb-4">
                    <AlertCircle className="h-6 w-6 text-destructive" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground text-center mb-6 max-w-md">
                    {message}
                </p>
                <div className="flex items-center gap-2">
                    {onRetry && (
                        <Button onClick={onRetry} variant="outline" size="sm">
                            <RefreshCw className="h-4 w-4 mr-2" />
                            {retryLabel}
                        </Button>
                    )}
                    {actions}
                </div>
            </CardContent>
        </Card>
    )
}

// ============================================================================
// Empty State Component
// ============================================================================

interface EmptyStateProps {
    icon?: React.ElementType
    title: string
    message: string
    action?: {
        label: string
        onClick: () => void
    }
    className?: string
}

export function EmptyState({
    icon: Icon = Inbox,
    title,
    message,
    action,
    className,
}: EmptyStateProps) {
    return (
        <div className={cn('flex flex-col items-center justify-center py-12', className)}>
            <div className="rounded-full bg-muted p-4 mb-4">
                <Icon className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">{title}</h3>
            <p className="text-sm text-muted-foreground text-center mb-6 max-w-md">
                {message}
            </p>
            {action && (
                <Button onClick={action.onClick} variant="default">
                    {action.label}
                </Button>
            )}
        </div>
    )
}

// ============================================================================
// Data State Wrapper (combines all states)
// ============================================================================

interface DataStateProps<T> {
    loading: boolean
    error: Error | null
    data: T | null
    isEmpty?: (data: T) => boolean
    loadingComponent?: React.ReactNode
    errorComponent?: React.ReactNode
    emptyComponent?: React.ReactNode
    children: (data: T) => React.ReactNode
    onRetry?: () => void
}

export function DataState<T>({
    loading,
    error,
    data,
    isEmpty,
    loadingComponent,
    errorComponent,
    emptyComponent,
    children,
    onRetry,
}: DataStateProps<T>) {
    if (loading) {
        return <>{loadingComponent || <LoadingState />}</>
    }

    if (error) {
        return (
            <>
                {errorComponent || (
                    <ErrorState
                        message={error.message || 'Failed to load data'}
                        onRetry={onRetry}
                    />
                )}
            </>
        )
    }

    if (!data || (isEmpty && isEmpty(data))) {
        return (
            <>
                {emptyComponent || (
                    <EmptyState
                        title="No data available"
                        message="There's nothing to display here yet."
                    />
                )}
            </>
        )
    }

    return <>{children(data)}</>
}
