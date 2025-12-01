import './globals.css';
import type { Metadata, Viewport } from 'next';
import { Manrope } from 'next/font/google';
import { Toaster } from 'sonner';

import { ThemeProvider } from '@/components/theme-provider';
import { Navigation } from '@/components/LandingPage/Navigation';
import { Footer } from '@/components/LandingPage/Footer';
import { HeroBackground } from '@/components/LandingPage/HeroBackground';
import { TopLoadingBar } from '@/components/TopLoadingBar';
import { ErrorBoundaryProvider } from '@/components/providers/error-boundary-provider';
import { AuthProvider } from '@/components/providers/auth-provider';

export const metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  title: 'PixCrawler - AI-Powered Image Dataset Builder for ML & Research',
  description: 'Build production-ready image datasets in minutes with AI-powered crawling, validation, and organization. Multi-source scraping from Google, Bing, and more. Perfect for ML researchers and developers.',
  keywords: ['image dataset', 'machine learning', 'AI dataset builder', 'image scraping', 'ML training data', 'computer vision', 'dataset generation'],
  authors: [{ name: 'PixCrawler' }],
  creator: 'PixCrawler',
  publisher: 'PixCrawler',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://pixcrawler.io',
    title: 'PixCrawler - AI-Powered Image Dataset Builder',
    description: 'Build production-ready image datasets in minutes with AI-powered crawling, validation, and organization.',
    siteName: 'PixCrawler',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'PixCrawler',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PixCrawler - AI-Powered Image Dataset Builder',
    description: 'Build production-ready image datasets in minutes with AI-powered crawling, validation, and organization.',
    creator: '@pixcrawler',
    images: ['/twitter-card.png'],
  },
  alternates: {
    canonical: 'https://pixcrawler.io',
  },
  manifest: '/site.webmanifest',
};

export const viewport: Viewport = {
  maximumScale: 1
};

const manrope = Manrope({
  subsets: ['latin'],
  variable: '--font-manrope',
  display: 'swap'
});

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={manrope.variable}
      suppressHydrationWarning
    >
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
      </head>
      <body className="min-h-screen bg-background text-foreground antialiased" suppressHydrationWarning>
        <ErrorBoundaryProvider>
          <AuthProvider>
            <ThemeProvider
              attribute="class"
              defaultTheme="system"
              enableSystem
              disableTransitionOnChange
            >
              <TopLoadingBar>
                <div className="relative min-h-screen overflow-hidden">
                  <HeroBackground />
                  <div className="relative z-10 flex flex-col min-h-screen">
                    <Navigation />
                    <main className="flex-1">{children}</main>
                    <Footer />
                  </div>
                </div>
              </TopLoadingBar>
              <Toaster richColors position="top-right" />
            </ThemeProvider>
          </AuthProvider>
        </ErrorBoundaryProvider>
      </body>
    </html>
  );
}
