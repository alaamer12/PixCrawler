import {AuthGuard} from '@/components/auth/auth-guard'
import {DashboardNav} from '@/components/dashboard/dashboard-nav'

export default function DashboardLayout({
                                          children,
                                        }: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        {children}
      </div>
    </AuthGuard>
  )
}
