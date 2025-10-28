/**
 * Image loading utilities for HeroVisual component
 * Handles dynamic category loading and random image selection
 */

import imageManifest from '@/public/imageManifest.json'

export interface Category {
  name: string
  id: number
}

interface ImageManifest {
  [category: string]: {
    count: number
    images: string[]
  }
}

/**
 * Dynamically loaded image manifest from public/imageManifest.json
 */
const MANIFEST: ImageManifest = imageManifest as ImageManifest

/**
 * Load all available categories from the image manifest
 * @returns Array of category objects with name and id
 */
export const loadCategories = (): Category[] => {
  return Object.keys(MANIFEST).map((name, index) => ({
    name,
    id: index + 1
  }))
}

/**
 * Get a random category from available categories
 * @returns Random category object
 */
export const getRandomCategory = (): Category => {
  const categories = loadCategories()
  return categories[Math.floor(Math.random() * categories.length)]
}

/**
 * Generate random image paths for a given category
 * Selects random images from the category's available images
 * @param categoryName - Name of the category (e.g., 'animals', 'nature')
 * @param count - Number of images to select (default: 24)
 * @returns Array of image paths
 */
export const getRandomImagesForCategory = (
  categoryName: string,
  count: number = 24
): string[] => {
  const categoryData = MANIFEST[categoryName]
  
  if (!categoryData) {
    console.warn(`Category "${categoryName}" not found in manifest`)
    return []
  }

  const availableImages = categoryData.images
  
  // Shuffle and select random images
  const selectedImages = shuffleArray(availableImages).slice(0, Math.min(count, availableImages.length))
  
  return selectedImages
}

/**
 * Fisher-Yates shuffle algorithm
 * @param array - Array to shuffle
 * @returns Shuffled array
 */
const shuffleArray = <T>(array: T[]): T[] => {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

/**
 * Get color class based on source count
 * @param sources - Number of sources (0-3)
 * @returns Tailwind color class
 */
export const getSourcesColor = (sources: number): string => {
  if (sources === 1) return 'text-red-500'
  if (sources === 2) return 'text-orange-500'
  if (sources === 3) return 'text-green-500'
  return 'text-muted-foreground'
}

/**
 * Get color class based on quality percentage
 * @param quality - Quality percentage (0-100)
 * @returns Tailwind color class
 */
export const getQualityColor = (quality: number): string => {
  if (quality < 50) return 'text-red-500'
  if (quality < 70) return 'text-orange-500'
  if (quality >= 90) return 'text-green-500'
  return 'text-muted-foreground'
}
