import { env } from '@/lib/env'

/**
 * API Client Configuration
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
const DEFAULT_TIMEOUT = 30000 // 30 seconds

/**
 * Custom API Error class for better error handling
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * API Response type
 */
export interface ApiResponse<T = unknown> {
  data?: T
  error?: {
    message: string
    code?: string
    details?: unknown
  }
  meta?: {
    page?: number
    limit?: number
    total?: number
  }
}

/**
 * Request options interface
 */
interface RequestOptions extends RequestInit {
  timeout?: number
  params?: Record<string, string | number | boolean>
}

/**
 * Creates a timeout promise for fetch requests
 */
function createTimeoutPromise(timeout: number): Promise<never> {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject(new ApiError('Request timeout', 408, 'TIMEOUT'))
    }, timeout)
  })
}

/**
 * Builds URL with query parameters
 */
function buildUrl(endpoint: string, params?: Record<string, string | number | boolean>): string {
  const url = new URL(endpoint, API_BASE_URL)
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, String(value))
    })
  }
  
  return url.toString()
}

/**
 * Centralized API client with error handling, timeouts, and interceptors
 */
class ApiClient {
  private baseUrl: string
  private defaultHeaders: HeadersInit

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    }
  }

  /**
   * Get authentication token from storage or session
   */
  private async getAuthToken(): Promise<string | null> {
    // In browser environment, get token from localStorage or session
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token')
    }
    return null
  }

  /**
   * Request interceptor - adds auth headers and other common headers
   */
  private async interceptRequest(options: RequestOptions): Promise<RequestOptions> {
    const token = await this.getAuthToken()
    
    const headers = new Headers(options.headers || this.defaultHeaders)
    
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
    
    return {
      ...options,
      headers,
    }
  }

  /**
   * Response interceptor - handles errors and transforms responses
   */
  private async interceptResponse<T>(response: Response): Promise<ApiResponse<T>> {
    // Handle non-JSON responses
    const contentType = response.headers.get('content-type')
    const isJson = contentType?.includes('application/json')

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      let errorCode = 'HTTP_ERROR'
      let errorDetails: unknown = undefined

      if (isJson) {
        try {
          const errorData = await response.json()
          errorMessage = errorData.message || errorData.error || errorMessage
          errorCode = errorData.code || errorCode
          errorDetails = errorData.details
        } catch {
          // Failed to parse error JSON, use default message
        }
      }

      throw new ApiError(errorMessage, response.status, errorCode, errorDetails)
    }

    if (isJson) {
      return await response.json()
    }

    // For non-JSON responses, return raw text
    const text = await response.text()
    return { data: text as T }
  }

  /**
   * Generic request method
   */
  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { timeout = DEFAULT_TIMEOUT, params, ...fetchOptions } = options

    try {
      const url = buildUrl(endpoint, params)
      const interceptedOptions = await this.interceptRequest(fetchOptions)

      const fetchPromise = fetch(url, interceptedOptions)
      const timeoutPromise = createTimeoutPromise(timeout)

      const response = await Promise.race([fetchPromise, timeoutPromise])
      const result = await this.interceptResponse<T>(response)

      return result.data as T
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }

      if (error instanceof Error) {
        throw new ApiError(error.message, undefined, 'NETWORK_ERROR')
      }

      throw new ApiError('An unknown error occurred', undefined, 'UNKNOWN_ERROR')
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'GET',
    })
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'DELETE',
    })
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export class for custom instances
export { ApiClient }
