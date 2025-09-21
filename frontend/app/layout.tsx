import './globals.css';
import type { Metadata, Viewport } from 'next';
import { Manrope } from 'next/font/google';

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
      className={`bg-white dark:bg-gray-950 text-black dark:text-white ${manrope.variable}`}
    >
      <body className="min-h-[100dvh] bg-gray-50 font-sans">
        {children}
      </body>
    </html>
  );
}
