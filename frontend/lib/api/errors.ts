export function parseApiError(error: any): string {
    if (typeof error === 'string') return error
    if (error instanceof Error) return error.message
    if (error?.detail) return error.detail
    if (error?.error?.message) return error.error.message
    return 'An unexpected error occurred'
}

export function getErrorMessage(statusCode: number, defaultMessage: string): string {
    switch (statusCode) {
        case 401:
            return 'Please log in to continue'
        case 403:
            return 'You do not have permission to perform this action'
        case 404:
            return 'Resource not found'
        case 422:
            return defaultMessage || 'Invalid input'
        case 429:
            return 'Too many requests. Please try again later'
        case 500:
            return 'Server error. Please try again'
        default:
            return defaultMessage || 'An error occurred'
    }
}
