import {createServerClient, type CookieOptions} from '@supabase/ssr'
import {NextResponse, type NextRequest} from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  // Skip middleware for dev pages in development
  if (process.env.NODE_ENV === 'development' && request.nextUrl.pathname.startsWith('/dev')) {
    return response
  }

  // Check for dev bypass in development mode - skip ALL auth logic if enabled
  const isDevBypass = process.env.NODE_ENV === 'development' && 
    request.nextUrl.searchParams.get('dev_bypass') === 'true'

  if (isDevBypass) {
    return response
  }

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value,
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value,
            ...options,
          })
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set({
            name,
            value: '',
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value: '',
            ...options,
          })
        },
      },
    }
  )

  const {
    data: {user},
  } = await supabase.auth.getUser()

  // Protected routes that require authentication
  const protectedPaths = ['/dashboard', '/welcome']
  const isProtectedPath = protectedPaths.some(path =>
    request.nextUrl.pathname.startsWith(path)
  )

  // Auth routes that should redirect if user is already logged in
  const authPaths = ['/login', '/signup', '/auth/forgot-password']
  const isAuthPath = authPaths.some(path =>
    request.nextUrl.pathname.startsWith(path)
  )

  // Welcome page - only for authenticated users
  const isWelcomePage = request.nextUrl.pathname === '/welcome'

  // Redirect to login if accessing protected route without authentication
  if (isProtectedPath && !user) {
    const redirectUrl = new URL('/login', request.url)
    redirectUrl.searchParams.set('redirectTo', request.nextUrl.pathname)
    return NextResponse.redirect(redirectUrl)
  }

  // Check onboarding status for authenticated users
  if (user && !isWelcomePage && !isAuthPath) {
    const {data: profile} = await supabase
      .from('profiles')
      .select('onboarding_completed')
      .eq('id', user.id)
      .single()

    // Redirect to welcome if onboarding not completed
    if (profile && !profile.onboarding_completed) {
      return NextResponse.redirect(new URL('/welcome', request.url))
    }
  }

  // Redirect to dashboard if accessing auth routes while authenticated
  if (isAuthPath && user) {
    // Check if user needs onboarding
    const {data: profile} = await supabase
      .from('profiles')
      .select('onboarding_completed')
      .eq('id', user.id)
      .single()

    if (profile && !profile.onboarding_completed) {
      return NextResponse.redirect(new URL('/welcome', request.url))
    }

    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
