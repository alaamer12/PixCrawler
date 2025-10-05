import './globals.css';
import type { Metadata, Viewport } from 'next';
import { Manrope } from 'next/font/google';
import { ThemeProvider } from '@/components/theme-provider';
import { Navigation } from '@/components/LandingPage/Navigation';
import { Footer } from '@/components/LandingPage/Footer';
import { HeroBackground } from '@/components/LandingPage/HeroBackground';

export const metadata: Metadata = {
  title: 'PixCrawler - AI-Powered Image Dataset Builder',
  description: 'Build high-quality image datasets with AI-powered crawling, labeling, and validation.'
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
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <div className="relative min-h-screen overflow-hidden">
            <HeroBackground />
            <div className="relative z-10 flex flex-col min-h-screen">
              <Navigation />
              <main className="flex-1">{children}</main>
              <Footer />
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
