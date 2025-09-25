import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'

export default async function HomePage() {
  const supabase = await createClient()
  
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (user) {
    redirect('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            PixCrawler
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            AI-Powered Image Dataset Builder. Crawl, validate, and label images with intelligent automation.
          </p>
          
          <div className="flex gap-4 justify-center mb-12">
            <Link
              href="/login"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              Get Started
            </Link>
            <Link
              href="/signup"
              className="bg-white hover:bg-gray-50 text-blue-600 px-8 py-3 rounded-lg font-semibold border border-blue-600 transition-colors"
            >
              Sign Up
            </Link>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="text-blue-600 text-3xl mb-4">🔍</div>
              <h3 className="text-lg font-semibold mb-2">Smart Crawling</h3>
              <p className="text-gray-600">
                Intelligent image discovery using multiple search engines and AI-powered keyword generation.
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="text-blue-600 text-3xl mb-4">✅</div>
              <h3 className="text-lg font-semibold mb-2">Auto Validation</h3>
              <p className="text-gray-600">
                Automatic duplicate detection, quality assessment, and integrity validation.
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md">
              <div className="text-blue-600 text-3xl mb-4">🏷️</div>
              <h3 className="text-lg font-semibold mb-2">AI Labeling</h3>
              <p className="text-gray-600">
                Generate accurate labels and metadata using advanced AI models.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
