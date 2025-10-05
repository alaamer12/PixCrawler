'use client'

import { useAuth } from '@/lib/auth/hooks'
import { Settings, User, Shield, Bell, Palette } from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="grid gap-6">
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="size-5 text-primary" />
            <h3 className="text-lg font-semibold">Profile Settings</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Full Name</label>
              <input
                type="text"
                className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                defaultValue={user?.profile?.fullName || user?.user_metadata?.full_name || ''}
                placeholder="Enter your full name"
              />
            </div>
            
            <div>
              <label className="text-sm font-medium">Email</label>
              <input
                type="email"
                className="w-full mt-1 px-3 py-2 bg-muted border border-border rounded-lg text-sm"
                value={user?.email || ''}
                disabled
              />
              <p className="text-xs text-muted-foreground mt-1">
                Email cannot be changed. Contact support if needed.
              </p>
            </div>
            
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
              Save Changes
            </button>
          </div>
        </div>

        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="size-5 text-primary" />
            <h3 className="text-lg font-semibold">Security</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <h4 className="font-medium">Password</h4>
              <p className="text-sm text-muted-foreground mb-2">
                Change your password to keep your account secure
              </p>
              <button className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors">
                Change Password
              </button>
            </div>
            
            <div>
              <h4 className="font-medium">Two-Factor Authentication</h4>
              <p className="text-sm text-muted-foreground mb-2">
                Add an extra layer of security to your account
              </p>
              <button className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors">
                Enable 2FA
              </button>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <Bell className="size-5 text-primary" />
            <h3 className="text-lg font-semibold">Notifications</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">Email Notifications</h4>
                <p className="text-sm text-muted-foreground">
                  Receive email updates about your projects
                </p>
              </div>
              <input type="checkbox" className="rounded" defaultChecked />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">Job Completion</h4>
                <p className="text-sm text-muted-foreground">
                  Get notified when crawl jobs complete
                </p>
              </div>
              <input type="checkbox" className="rounded" defaultChecked />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">Weekly Reports</h4>
                <p className="text-sm text-muted-foreground">
                  Receive weekly activity summaries
                </p>
              </div>
              <input type="checkbox" className="rounded" />
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-card text-card-foreground shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <Palette className="size-5 text-primary" />
            <h3 className="text-lg font-semibold">Appearance</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <h4 className="font-medium">Theme</h4>
              <p className="text-sm text-muted-foreground mb-2">
                Choose your preferred theme
              </p>
              <select className="px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50">
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}