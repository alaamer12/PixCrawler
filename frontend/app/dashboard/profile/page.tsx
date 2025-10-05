'use client'

import { useAuth } from '@/lib/auth/hooks'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { User, Mail, Calendar, Shield } from 'lucide-react'

export default function ProfilePage() {
  const { user } = useAuth()

  if (!user) return null

  const initials = user.profile?.fullName
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase() || user.email?.charAt(0).toUpperCase() || 'U'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
        <p className="text-muted-foreground">
          Manage your account information and preferences
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Profile Information</h3>
          
          <div className="flex items-center space-x-4 mb-6">
            <Avatar className="h-16 w-16">
              <AvatarImage 
                src={user.profile?.avatarUrl || user.user_metadata?.avatar_url} 
                alt={user.profile?.fullName || user.email || 'User'} 
              />
              <AvatarFallback className="text-lg">{initials}</AvatarFallback>
            </Avatar>
            <div>
              <h4 className="text-xl font-semibold">
                {user.profile?.fullName || user.user_metadata?.full_name || 'User'}
              </h4>
              <p className="text-muted-foreground">{user.email}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <User className="size-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Full Name</p>
                <p className="text-sm text-muted-foreground">
                  {user.profile?.fullName || user.user_metadata?.full_name || 'Not set'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Mail className="size-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Email</p>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Calendar className="size-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Member Since</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(user.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Shield className="size-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Role</p>
                <p className="text-sm text-muted-foreground">
                  {user.profile?.role || 'User'}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Account Statistics</h3>
          
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Projects Created</span>
              <span className="text-sm text-muted-foreground">0</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Images Collected</span>
              <span className="text-sm text-muted-foreground">0</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Storage Used</span>
              <span className="text-sm text-muted-foreground">0 MB</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Last Login</span>
              <span className="text-sm text-muted-foreground">
                {new Date(user.last_sign_in_at || user.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}