/**
 * Error Handler Utility
 * 
 * Centralized error handling with user-friendly messages,
 * logging, and retry logic for transient errors.
 */

import { ServiceError } from '@/lib/services/base.service'

// Error type definitions
export enum ErrorType {
    NETWORK = 'NETWORK',
    AUTHENTICATION = 'AUTHENTICATION',
    AUTHORIZATION = 'AUTHORIZATION',
    VALIDATION = 'VALIDATION',
    NOT_FOUND = 'NOT_FOUND',
    SERVER = 'SERVER',
    UNKNOWN = 'UNKNOWN',
}

// User-friendly error messages
const ERROR_MESSAGES: Record<ErrorType, string> = {
    [ErrorType.NETWORK]: 'Unable to connect. Please check your internet connection and try again.',
    [ErrorType.AUTHENTICATION]: 'Your session has expired. Please sign in again.',
    [ErrorType.AUTHORIZATION]: 'You don\'t have permission to perform this action.',
    [ErrorType.VALIDATION]: 'Please check your input and try again.',
    [ErrorType.NOT_FOUND]: 'The requested resource was not found.',
    [ErrorType.SERVER]: 'Something went wrong on our end. Please try again later.',
    [ErrorType.UNKNOWN]: 'An unexpected error occurred. Please try again.',
}

// Transient error codes that should be retried
const TRANSIENT_ERROR_CODES = [408, 429, 500, 502, 503, 504]

export class ErrorHandler {
    /**
     * Classify error type based on error object
     */
    static classifyError(error: unknown): ErrorType {
        if (error instanceof ServiceError) {
            const statusCode = error.statusCode

            if (statusCode === 401) return ErrorType.AUTHENTICATION
            if (statusCode === 403) return ErrorType.AUTHORIZATION
            if (statusCode === 404) return ErrorType.NOT_FOUND
            if (statusCode === 422 || statusCode === 400) return ErrorType.VALIDATION
            if (statusCode >= 500) return ErrorType.SERVER
        }

        if (error instanceof TypeError && error.message.includes('fetch')) {
            return ErrorType.NETWORK
        }

        return ErrorType.UNKNOWN
    }

    /**
     * Get user-friendly error message
     */
    static getUserFriendlyMessage(error: unknown, customMessage?: string): string {
        if (customMessage) return customMessage

        const errorType = this.classifyError(error)
        return ERROR_MESSAGES[errorType]
    }

    /**
     * Check if error is transient and should be retried
     */
    static isTransientError(error: unknown): boolean {
        if (error instanceof ServiceError) {
            return TRANSIENT_ERROR_CODES.includes(error.statusCode)
        }

        // Network errors are transient
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return true
        }

        return false
    }

    /**
     * Log error to console (in development) or error tracking service (in production)
     */
    static logError(error: unknown, context?: Record<string, any>) {
        const isDevelopment = process.env.NODE_ENV === 'development'

        const errorInfo = {
            message: error instanceof Error ? error.message : 'Unknown error',
            type: this.classifyError(error),
            timestamp: new Date().toISOString(),
            context,
            stack: error instanceof Error ? error.stack : undefined,
        }

        if (isDevelopment) {
            console.error('[ErrorHandler]', errorInfo)
        } else {
            // In production, send to error tracking service (e.g., Sentry)
            // Example: Sentry.captureException(error, { extra: errorInfo })
            console.error('[ErrorHandler]', errorInfo)
        }
    }

    /**
     * Handle error with logging and user-friendly message
     */
    static handleError(
        error: unknown,
        options?: {
            customMessage?: string
            context?: Record<string, any>
            silent?: boolean
        }
    ): {
        message: string
        type: ErrorType
        shouldRetry: boolean
    } {
        const { customMessage, context, silent = false } = options || {}

        // Log error
        if (!silent) {
            this.logError(error, context)
        }

        return {
            message: this.getUserFriendlyMessage(error, customMessage),
            type: this.classifyError(error),
            shouldRetry: this.isTransientError(error),
        }
    }

    /**
     * Retry function with exponential backoff
     */
    static async retryWithBackoff<T>(
        fn: () => Promise<T>,
        options?: {
            maxRetries?: number
            initialDelay?: number
            maxDelay?: number
            onRetry?: (attempt: number, error: unknown) => void
        }
    ): Promise<T> {
        const {
            maxRetries = 3,
            initialDelay = 1000,
            maxDelay = 10000,
            onRetry,
        } = options || {}

        let lastError: unknown

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                return await fn()
            } catch (error) {
                lastError = error

                // Don't retry if it's not a transient error
                if (!this.isTransientError(error)) {
                    throw error
                }

                // Don't retry if we've exhausted attempts
                if (attempt === maxRetries) {
                    throw error
                }

                // Calculate delay with exponential backoff
                const delay = Math.min(initialDelay * Math.pow(2, attempt), maxDelay)

                // Call retry callback
                if (onRetry) {
                    onRetry(attempt + 1, error)
                }

                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, delay))
            }
        }

        throw lastError
    }
}

// Convenience functions
export const getUserFriendlyError = (error: unknown, customMessage?: string) =>
    ErrorHandler.getUserFriendlyMessage(error, customMessage)

export const logError = (error: unknown, context?: Record<string, any>) =>
    ErrorHandler.logError(error, context)

export const handleError = (
    error: unknown,
    options?: Parameters<typeof ErrorHandler.handleError>[1]
) => ErrorHandler.handleError(error, options)

export const retryWithBackoff = <T>(
    fn: () => Promise<T>,
    options?: Parameters<typeof ErrorHandler.retryWithBackoff>[1]
) => ErrorHandler.retryWithBackoff(fn, options)
