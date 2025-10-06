# PixCrawler Authentication Setup

This document provides a complete guide for setting up authentication in the PixCrawler frontend application.

## Features Implemented

### ✅ Core Authentication

- **Email/Password Authentication**: Sign up, sign in, and password reset
- **OAuth Integration**: GitHub and Google OAuth providers
- **Session Management**: Secure session handling with Supabase Auth
- **Protected Routes**: Middleware-based route protection
- **User Profiles**: Extended user profiles with metadata

### ✅ UI Components

- **Modern Auth Forms**: Consistent design with Tailwind CSS
- **OAuth Buttons**: GitHub and Google sign-in buttons
- **User Menu**: Dropdown menu with profile and settings
- **Auth Guard**: Component-level authentication protection
- **Loading States**: Proper loading and error handling

### ✅ Pages & Routes

- `/login` - Sign in page
- `/signup` - Sign up page
- `/auth/forgot-password` - Password reset request
- `/auth/reset-password` - Password reset form
- `/auth/callback` - OAuth callback handler
- `/auth/auth-code-error` - Error handling page
- `/dashboard` - Protected dashboard
- `/dashboard/profile` - User profile page
- `/dashboard/settings` - Account settings

## Setup Instructions

### 1. Environment Variables

Copy the example environment file and configure your Supabase credentials:

```bash
cp .env.example .env.local
```

Update the following variables in `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
AUTH_SECRET=your_random_secret_key
```

### 2. Database Setup

Run the database setup script to create the necessary tables and policies:

```bash
npm run db:setup
```

This will:

- Create the `profiles` table
- Set up Row Level Security (RLS) policies
- Create triggers for automatic profile creation
- Configure proper permissions

### 3. OAuth Configuration

#### GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/applications/new)
2. Create a new OAuth App with:
  - **Application name**: PixCrawler
  - **Homepage URL**: `http://localhost:3000` (development) or your production URL
  - **Authorization callback URL**: `http://localhost:3000/auth/callback`
3. Copy the Client ID and Client Secret
4. In your Supabase dashboard, go to Authentication > Providers > GitHub
5. Enable GitHub and add your Client ID and Client Secret

#### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to Credentials > Create Credentials > OAuth 2.0 Client IDs
5. Configure the OAuth consent screen
6. Add authorized redirect URIs: `https://your-project.supabase.co/auth/v1/callback`
7. Copy the Client ID and Client Secret
8. In your Supabase dashboard, go to Authentication > Providers > Google
9. Enable Google and add your Client ID and Client Secret

### 4. Supabase Configuration

In your Supabase dashboard:

1. **Authentication Settings**:
  - Enable email confirmations (optional)
  - Set up custom SMTP (optional)
  - Configure redirect URLs for your domain

2. **URL Configuration**:
  - Add your site URL: `http://localhost:3000` (development)
  - Add redirect URLs: `http://localhost:3000/auth/callback`

## File Structure

```
frontend/
├── app/
│   ├── auth/
│   │   ├── callback/
│   │   │   └── route.ts              # OAuth callback handler
│   │   ├── forgot-password/
│   │   │   ├── page.tsx              # Password reset request page
│   │   │   └── forgot-password-form.tsx
│   │   ├── reset-password/
│   │   │   ├── page.tsx              # Password reset form page
│   │   │   └── reset-password-form.tsx
│   │   └── auth-code-error/
│   │       └── page.tsx              # Error handling page
│   ├── dashboard/
│   │   ├── layout.tsx                # Protected dashboard layout
│   │   ├── page.tsx                  # Dashboard home
│   │   ├── profile/
│   │   │   └── page.tsx              # User profile page
│   │   └── settings/
│   │       └── page.tsx              # Account settings
│   ├── login/
│   │   ├── page.tsx                  # Sign in page
│   │   └── login-form.tsx            # Sign in form component
│   ├── signup/
│   │   ├── page.tsx                  # Sign up page
│   │   └── signup-form.tsx           # Sign up form component
│   └── middleware.ts                 # Route protection middleware
├── components/
│   ├── auth/
│   │   ├── auth-guard.tsx            # Authentication guard component
│   │   ├── oauth-buttons.tsx         # OAuth provider buttons
│   │   └── user-menu.tsx             # User dropdown menu
│   ├── dashboard/
│   │   └── dashboard-nav.tsx         # Dashboard navigation
│   └── ui/
│       ├── avatar.tsx                # Avatar component
│       └── dropdown-menu.tsx         # Dropdown menu component
└── lib/
    ├── auth/
    │   ├── index.ts                  # Main auth service
    │   ├── hooks.ts                  # React hooks for auth
    │   ├── middleware.ts             # Auth middleware utilities
    │   └── session.ts                # Session management
    ├── supabase/
    │   ├── client.ts                 # Client-side Supabase client
    │   └── server.ts                 # Server-side Supabase client
    └── db/
        ├── schema.ts                 # Database schema definitions
        └── setup.ts                  # Database setup script
```

## Usage Examples

### Using the Auth Hook

```tsx
'use client'

import { useAuth } from '@/lib/auth/hooks'

export function MyComponent() {
  const { user, loading, signOut, isAuthenticated } = useAuth()

  if (loading) return <div>Loading...</div>
  if (!isAuthenticated) return <div>Please sign in</div>

  return (
    <div>
      <p>Welcome, {user?.profile?.fullName}!</p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}
```

### Protecting Pages

```tsx
import { AuthGuard } from '@/components/auth/auth-guard'

export default function ProtectedPage() {
  return (
    <AuthGuard>
      <div>This content is only visible to authenticated users</div>
    </AuthGuard>
  )
}
```

### Using the Auth Service

```tsx
import { authService } from '@/lib/auth'

// Sign up
await authService.signUp('user@example.com', 'password', 'Full Name')

// Sign in
await authService.signIn('user@example.com', 'password')

// OAuth sign in
await authService.signInWithOAuth('github')

// Sign out
await authService.signOut()

// Reset password
await authService.resetPassword('user@example.com')
```

## Security Features

### Row Level Security (RLS)

- All database tables have RLS enabled
- Users can only access their own data
- Policies enforce proper authorization

### Session Management

- Secure HTTP-only cookies
- Automatic session refresh
- Proper session cleanup on logout

### Route Protection

- Middleware-based route protection
- Automatic redirects for unauthenticated users
- Protected API routes

### Input Validation

- Client-side form validation
- Server-side validation with Supabase
- Proper error handling and user feedback

## Customization

### Styling

The authentication components use Tailwind CSS and can be customized by:

- Modifying the component classes
- Updating the design system tokens
- Creating custom variants

### Providers

To add more OAuth providers:

1. Enable the provider in Supabase dashboard
2. Add the provider to the `OAuthButtons` component
3. Update the `AuthService` to handle the new provider

### Database Schema

The user profile schema can be extended by:

1. Updating the `profiles` table in Supabase
2. Modifying the TypeScript types in `schema.ts`
3. Updating the profile forms and displays

## Troubleshooting

### Common Issues

1. **OAuth redirect errors**:
  - Check redirect URLs in provider settings
  - Ensure callback URL matches exactly
  - Verify environment variables

2. **Database permission errors**:
  - Run the database setup script
  - Check RLS policies in Supabase
  - Verify service role key permissions

3. **Session issues**:
  - Clear browser cookies
  - Check middleware configuration
  - Verify Supabase client setup

### Debug Mode

Enable debug logging by setting:

```env
NODE_ENV=development
```

This will provide detailed logs for authentication flows and database operations.

## Next Steps

1. **Email Templates**: Customize email templates in Supabase
2. **Multi-factor Authentication**: Implement TOTP/SMS 2FA
3. **Social Providers**: Add more OAuth providers (Twitter, LinkedIn, etc.)
4. **Advanced Security**: Implement rate limiting and suspicious activity detection
5. **User Management**: Add admin panel for user management

## Support

For issues or questions:

1. Check the Supabase documentation
2. Review the component source code
3. Check browser console for errors
4. Verify environment variables and configuration
