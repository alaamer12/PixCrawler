import { createClient } from '@/lib/supabase/client'
import type { DatasetConfig, TestResult } from '@/app/welcome/welcome-flow'

export class OnboardingService {
  private supabase = createClient()

  // Run a test crawl with limited images
  async runTestCrawl(config: DatasetConfig): Promise<TestResult> {
    try {
      // TODO: Replace with actual API call to backend
      // For now, simulate the test crawl
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Simulate success/failure based on config
      const hasValidCategories = config.categories.every(cat =>
        cat.length > 2 && /^[a-zA-Z\s]+$/.test(cat)
      )

      if (!hasValidCategories) {
        return {
          success: false,
          imagesFound: 0,
          error: 'Invalid category names',
          suggestions: [
            'Use common English words for categories',
            'Avoid special characters and numbers',
            'Try broader terms like "animals" instead of specific breeds'
          ]
        }
      }

      // Simulate random success for demo
      const success = Math.random() > 0.2

      if (success) {
        return {
          success: true,
          imagesFound: 10,
          sampleImages: Array(4).fill('/api/placeholder/150/150')
        }
      } else {
        return {
          success: false,
          imagesFound: Math.floor(Math.random() * 5),
          error: "Couldn't find enough images",
          suggestions: [
            'Use more common or broader search terms',
            'Check spelling of category names',
            'Try different categories',
            'Reduce the number of images per category'
          ]
        }
      }
    } catch (error) {
      return {
        success: false,
        imagesFound: 0,
        error: 'Network error occurred',
        suggestions: ['Check your internet connection', 'Try again in a moment']
      }
    }
  }

  // Create a full dataset job using Simple Flow API
  async createDatasetJob(config: DatasetConfig): Promise<{ jobId: string }> {
    try {
      // Use Simple Flow API via Next.js proxy
      const response = await fetch('/api/v1/simple-flow/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keywords: config.categories,
          max_images: config.imagesPerCategory * config.categories.length,
          engines: ['duckduckgo'],
          output_name: config.name
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      return { jobId: result.flow_id }
    } catch (error) {
      console.error('Failed to create dataset job:', error)
      throw new Error('Failed to create dataset job')
    }
  }

  // Mark onboarding as completed
  async completeOnboarding(): Promise<void> {
    const { data: { user } } = await this.supabase.auth.getUser()

    if (!user) {
      // In development with dev_bypass, skip database update
      if (process.env.NODE_ENV === 'development') {
        console.warn('[DEV MODE] Skipping onboarding completion - user not authenticated')
        return
      }
      throw new Error('User not authenticated')
    }

    const { error } = await this.supabase
      .from('profiles')
      .upsert({
        id: user.id,
        email: user.email!,
        onboarding_completed: true,
        onboarding_completed_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      })

    if (error) {
      console.error('Error updating onboarding status:', error)
      throw new Error('Failed to update onboarding status')
    }
  }

  // Check if user has completed onboarding
  async hasCompletedOnboarding(): Promise<boolean> {
    const { data: { user } } = await this.supabase.auth.getUser()

    if (!user) {
      return false
    }

    const { data, error } = await this.supabase
      .from('profiles')
      .select('onboarding_completed')
      .eq('id', user.id)
      .single()

    if (error || !data) {
      return false
    }

    return data.onboarding_completed
  }
}

export const onboardingService = new OnboardingService()
