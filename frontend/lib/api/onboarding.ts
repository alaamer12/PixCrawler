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

  // Create a full dataset job
  async createDatasetJob(config: DatasetConfig): Promise<{ jobId: string }> {
    try {
      // TODO: Replace with actual API call to backend
      // For now, simulate job creation
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Generate a mock job ID
      const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      
      return { jobId }
    } catch (error) {
      throw new Error('Failed to create dataset job')
    }
  }

  // Mark onboarding as completed
  async completeOnboarding(): Promise<void> {
    const { data: { user } } = await this.supabase.auth.getUser()
    
    if (!user) {
      throw new Error('User not authenticated')
    }

    const { error } = await this.supabase
      .from('profiles')
      .update({
        onboarding_completed: true,
        onboarding_completed_at: new Date().toISOString()
      })
      .eq('id', user.id)

    if (error) {
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