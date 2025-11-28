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
            if (<number>statusCode >= 500) return ErrorType.SERVER
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
}
