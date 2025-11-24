import { notFound } from 'next/navigation'

export default function DevLayout({
  children,
}: {
  children: React.ReactNode
}) {
  if (process.env.NODE_ENV === 'production') {
    notFound()
  }

  return (
    <div className="min-h-screen bg-background">
      {children}
    </div>
  )
}
