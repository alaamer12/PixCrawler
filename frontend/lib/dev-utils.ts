import {NextRequest} from 'next/server'

/**
 * Check if dev bypass is enabled for server-side pages
 */
export function isDevBypassEnabled(request?: NextRequest | { searchParams: URLSearchParams }): boolean {
  if (process.env.NODE_ENV !== 'development') {
    return false
  }

  // For server components, check searchParams
  if (request && 'searchParams' in request) {
    return request.searchParams.get('dev_bypass') === 'true'
  }

  // For middleware, check URL searchParams
  if (request && 'nextUrl' in request) {
    return request.nextUrl.searchParams.get('dev_bypass') === 'true'
  }

  return false
}

/**
 * Mock user data for development
 */
export const DEV_MOCK_USER = {
  id: 'dev-user-123',
  email: 'dev@pixcrawler.dev',
  user_metadata: {
    full_name: 'Dev User'
  },
  app_metadata: {},
  aud: 'authenticated',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
}

/**
 * Get dev bypass status from search params (for server components)
 */
export function getDevBypassFromSearchParams(searchParams: URLSearchParams) {
  return {
    isEnabled: process.env.NODE_ENV === 'development' && searchParams.get('dev_bypass') === 'true',
    mockUser: DEV_MOCK_USER
  }
}
