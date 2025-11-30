/**
 * Base Service Class
 *
 * Provides common functionality for all service classes including:
 * - Error handling
 * - Request/response interceptors
 * - Retry logic with exponential backoff
 * - Request deduplication
 * - Loading state management
 */

export interface ServiceResponse<T> {
    data: T | null
    error: Error | null
    loading?: boolean
}

export interface RequestConfig {
    retries?: number
    retryDelay?: number
    timeout?: number
    deduplicate?: boolean
}

export class ServiceError extends Error {
    constructor(
        message: string,
        public statusCode?: number,
    ) {
        super(message)
        this.name = 'ServiceError'
    }
}

export abstract class BaseService {
    private pendingRequests: Map<string, Promise<any>> = new Map()
    private requestInterceptors: Array<(config: any) => any> = []
    private responseInterceptors: Array<(response: any) => any> = []

    /**
     * Add a request interceptor
     */
    protected addRequestInterceptor(interceptor: (config: any) => any): void {
        this.requestInterceptors.push(interceptor)
    }

    /**
     * Add a response interceptor
     */
    protected addResponseInterceptor(interceptor: (response: any) => any): void {
        this.responseInterceptors.push(interceptor)
    }

    /**
     * Apply all request interceptors
     */
    private async applyRequestInterceptors(config: any): Promise<any> {
        let modifiedConfig = config
        for (const interceptor of this.requestInterceptors) {
            modifiedConfig = await interceptor(modifiedConfig)
        }
        return modifiedConfig
    }

    /**
     * Apply all response interceptors
     */
    private async applyResponseInterceptors(response: any): Promise<any> {
        let modifiedResponse = response
        for (const interceptor of this.responseInterceptors) {
            modifiedResponse = await interceptor(modifiedResponse)
        }
        return modifiedResponse
    }

    /**
     * Execute a request with retry logic and deduplication
     */
    protected async executeRequest<T>(
        requestFn: () => Promise<T>,
        config: RequestConfig = {}
    ): Promise<ServiceResponse<T>> {
        const {
            retries = 3,
            retryDelay = 1000,
            deduplicate = true,
        } = config

        // Generate request key for deduplication
        const requestKey = deduplicate ? this.generateRequestKey(requestFn) : null

        // Check for pending duplicate request
        if (requestKey && this.pendingRequests.has(requestKey)) {
            try {
                const data = await this.pendingRequests.get(requestKey)
                return { data, error: null }
            } catch (error) {
                return this.handleError(error)
            }
        }

        // Execute request with retry logic
        const promise = this.retryRequest(requestFn, retries, retryDelay)

        // Store pending request for deduplication
        if (requestKey) {
            this.pendingRequests.set(requestKey, promise)
        }

        try {
            const data = await promise
            return { data, error: null }
        } catch (error) {
            return this.handleError(error)
        } finally {
            // Clean up pending request
            if (requestKey) {
                this.pendingRequests.delete(requestKey)
            }
        }
    }

    /**
     * Retry a request with exponential backoff
     */
    private async retryRequest<T>(
        requestFn: () => Promise<T>,
        maxRetries: number,
        baseDelay: number
    ): Promise<T> {
        let lastError: Error | unknown

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                return await requestFn()
            } catch (error) {
                lastError = error

                // Don't retry on client errors (4xx)
                if (this.isClientError(error)) {
                    throw error
                }

                // Don't retry if this was the last attempt
                if (attempt === maxRetries) {
                    throw error
                }

                // Wait before retrying with exponential backoff
                const delay = baseDelay * Math.pow(2, attempt)
                await this.sleep(delay)
            }
        }

        throw lastError
    }

    /**
     * Check if error is a client error (4xx)
     */
    private isClientError(error: unknown): boolean {
        if (error instanceof ServiceError) {
            return error.statusCode !== undefined &&
                error.statusCode >= 400 &&
                error.statusCode < 500
        }
        return false
    }

    /**
     * Sleep for specified milliseconds
     */
    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms))
    }

    /**
     * Generate a unique key for request deduplication
     */
    private generateRequestKey(requestFn: Function): string {
        // Use function toString as a simple key
        // In production, you might want a more sophisticated approach
        return requestFn.toString()
    }

    /**
     * Handle errors and convert to ServiceResponse
     */
    protected handleError<T>(error: unknown): ServiceResponse<T> {
        console.error('Service error:', error)

        if (error instanceof ServiceError) {
            return { data: null, error }
        }

        if (error instanceof Error) {
            return {
                data: null,
                error: new ServiceError(
                    error.message,
                    undefined,
                    error
                )
            }
        }

        return {
            data: null,
            error: new ServiceError(
                'An unknown error occurred',
                undefined,
                error
            )
        }
    }

    /**
     * Get user-friendly error message
     */
    protected getUserFriendlyMessage(error: Error): string {
        const message = error.message.toLowerCase()

        if (message.includes('network')) {
            return 'Unable to connect. Please check your internet connection.'
        }

        if (message.includes('404') || message.includes('not found')) {
            return 'The requested resource was not found.'
        }

        if (message.includes('401') || message.includes('unauthorized')) {
            return 'You are not authorized to perform this action.'
        }

        if (message.includes('403') || message.includes('forbidden')) {
            return 'Access to this resource is forbidden.'
        }

        if (message.includes('500') || message.includes('server error')) {
            return 'A server error occurred. Please try again later.'
        }

        return 'An unexpected error occurred. Please try again.'
    }

    /**
     * Log request for debugging
     */
    protected logRequest(method: string, endpoint: string, data?: any): void {
        if (process.env.NODE_ENV === 'development') {
            console.log(`[${method}] ${endpoint}`, data || '')
        }
    }

    /**
     * Log response for debugging
     */
    protected logResponse(method: string, endpoint: string, response: any): void {
        if (process.env.NODE_ENV === 'development') {
            console.log(`[${method}] ${endpoint} - Response:`, response)
        }
    }
}
