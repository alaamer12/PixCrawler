/**
 * Services Index
 * 
 * Central export point for all service classes
 */

export * from './base.service'
export * from './supabase.service'
export * from './api.service'

// Re-export singleton instances for convenience
export { supabaseService } from './supabase.service'
export { apiService } from './api.service'
