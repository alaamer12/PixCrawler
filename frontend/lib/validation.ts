/**
 * Form validation utilities for PixCrawler
 * Enterprise-grade validation with detailed error messages
 */

export interface ValidationResult {
  valid: boolean
  errors: Record<string, string>
  warnings?: Record<string, string>
}

export interface ProjectFormData {
  name: string
  description?: string
}

export interface DatasetFormData {
  name: string
  keywords: string
  imageCount: number
  sources: string[]
  aiExpansion?: boolean
  deduplicationLevel?: string
  minImageSize?: number
  imageFormat?: string
  safeSearch?: boolean
}

/**
 * Validate project creation form
 */
export function validateProjectForm(data: ProjectFormData): ValidationResult {
  const errors: Record<string, string> = {}
  const warnings: Record<string, string> = {}

  // Project name validation
  if (!data.name || data.name.trim().length === 0) {
    errors.name = 'Project name is required'
  } else if (data.name.trim().length < 3) {
    errors.name = 'Project name must be at least 3 characters'
  } else if (data.name.trim().length > 100) {
    errors.name = 'Project name must not exceed 100 characters'
  } else if (!/^[a-zA-Z0-9\s\-_]+$/.test(data.name)) {
    errors.name = 'Project name can only contain letters, numbers, spaces, hyphens, and underscores'
  }

  // Description validation (optional but with limits)
  if (data.description && data.description.length > 500) {
    errors.description = 'Description must not exceed 500 characters'
  }

  // Warnings
  if (data.name && data.name.trim().length < 5) {
    warnings.name = 'Consider using a more descriptive name'
  }

  if (!data.description || data.description.trim().length === 0) {
    warnings.description = 'Adding a description helps organize your projects'
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
    warnings
  }
}

/**
 * Validate dataset creation form
 */
export function validateDatasetForm(data: DatasetFormData): ValidationResult {
  const errors: Record<string, string> = {}
  const warnings: Record<string, string> = {}

  // Dataset name validation
  if (!data.name || data.name.trim().length === 0) {
    errors.name = 'Dataset name is required'
  } else if (data.name.trim().length < 3) {
    errors.name = 'Dataset name must be at least 3 characters'
  } else if (data.name.trim().length > 100) {
    errors.name = 'Dataset name must not exceed 100 characters'
  }

  // Keywords validation
  if (!data.keywords || data.keywords.trim().length === 0) {
    errors.keywords = 'At least one keyword is required'
  } else {
    const keywordList = data.keywords.split(',').map(k => k.trim()).filter(k => k.length > 0)
    
    if (keywordList.length === 0) {
      errors.keywords = 'At least one valid keyword is required'
    } else if (keywordList.length > 50) {
      errors.keywords = 'Maximum 50 keywords allowed'
    } else if (keywordList.some(k => k.length > 100)) {
      errors.keywords = 'Each keyword must not exceed 100 characters'
    }

    // Warnings for keywords
    if (keywordList.length === 1) {
      warnings.keywords = 'Consider adding more keywords for better dataset variety'
    } else if (keywordList.length > 20) {
      warnings.keywords = 'Large number of keywords may increase processing time significantly'
    }
  }

  // Image count validation
  if (data.imageCount < 10) {
    errors.imageCount = 'Minimum 10 images per keyword required'
  } else if (data.imageCount > 500) {
    errors.imageCount = 'Maximum 500 images per keyword allowed'
  }

  if (data.imageCount > 200) {
    warnings.imageCount = 'High image count may result in longer processing times'
  }

  // Sources validation
  if (!data.sources || data.sources.length === 0) {
    errors.sources = 'At least one image source must be selected'
  } else if (data.sources.length > 5) {
    warnings.sources = 'Using many sources may increase processing time'
  }

  // Image size validation
  if (data.minImageSize && (data.minImageSize < 256 || data.minImageSize > 2048)) {
    errors.minImageSize = 'Image size must be between 256px and 2048px'
  }

  // Calculate estimated totals for warnings
  if (data.imageCount && data.sources && data.keywords) {
    const keywordCount = data.keywords.split(',').filter(k => k.trim()).length
    const estimatedTotal = data.imageCount * keywordCount * data.sources.length
    
    if (estimatedTotal > 10000) {
      warnings.general = `This configuration will download ~${estimatedTotal.toLocaleString()} images. Consider reducing image count or keywords.`
    }
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors,
    warnings
  }
}

/**
 * Validate configuration values
 */
export function validateConfigValue(
  id: string,
  value: any,
  type: 'switch' | 'slider' | 'select' | 'input' | 'multi-select'
): ValidationResult {
  const errors: Record<string, string> = {}

  switch (type) {
    case 'slider':
      if (typeof value !== 'number') {
        errors[id] = 'Value must be a number'
      }
      break
    
    case 'input':
      if (typeof value !== 'string') {
        errors[id] = 'Value must be a string'
      } else if (value.trim().length === 0) {
        errors[id] = 'Value cannot be empty'
      }
      break
    
    case 'multi-select':
      if (!Array.isArray(value)) {
        errors[id] = 'Value must be an array'
      } else if (value.length === 0) {
        errors[id] = 'At least one option must be selected'
      }
      break
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors
  }
}

/**
 * Sanitize input to prevent XSS
 */
export function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove angle brackets
    .trim()
}

/**
 * Format keywords for display
 */
export function formatKeywords(keywords: string): string[] {
  return keywords
    .split(',')
    .map(k => sanitizeInput(k))
    .filter(k => k.length > 0)
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate URL format
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Check if string contains only alphanumeric characters
 */
export function isAlphanumeric(str: string): boolean {
  return /^[a-zA-Z0-9]+$/.test(str)
}

/**
 * Debounce validation for real-time feedback
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}
