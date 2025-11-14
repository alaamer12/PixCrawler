import {AuthGuard} from '@/components/auth/auth-guard'

export default function DashboardLayout({
                                          children,
                                        }: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-gradient-to-br from-background/50 via-background/30 to-background/50">
        <div className="min-h-screen backdrop-blur-xl">
          {children}
        </div>
      </div>
    </AuthGuard>
  )
}
