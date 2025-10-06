'use client'

import {useCallback, useRef, useState} from 'react'
import {globalImageBuffer} from '@/lib/ImageBuffer'

interface UseImageLoaderReturn {
  loadedImages: Set<number>
  failedImages: Set<number>
  loadingImages: Set<number>
  loadImage: (url: string, index: number) => Promise<HTMLImageElement | null>
  updateImageStatus: (index: number, loaded: boolean) => void
  preloadImage: (url: string) => Promise<HTMLImageElement | null>
  clearCache: () => void
}

export const useImageLoader = (): UseImageLoaderReturn => {
  const [loadedImages, setLoadedImages] = useState<Set<number>>(new Set())
  const [failedImages, setFailedImages] = useState<Set<number>>(new Set())
  const [loadingImages, setLoadingImages] = useState<Set<number>>(new Set())
  const loadingPromises = useRef<Map<string, Promise<HTMLImageElement | null>>>(new Map())

  const loadImage = useCallback(async (url: string, index: number): Promise<HTMLImageElement | null> => {
    // Check if already in buffer
    const bufferedImage = globalImageBuffer.get(url)
    if (bufferedImage) {
      setLoadedImages(prev => new Set(prev).add(index))
      return bufferedImage as HTMLImageElement
    }

    // Check if already loading
    const existingPromise = loadingPromises.current.get(url)
    if (existingPromise) {
      return existingPromise
    }

    // Start loading
    setLoadingImages(prev => new Set(prev).add(index))

    const loadPromise = new Promise<HTMLImageElement | null>((resolve) => {
      const img = new Image()

      img.onload = () => {
        globalImageBuffer.put(url, img)
        setLoadedImages(prev => new Set(prev).add(index))
        setLoadingImages(prev => {
          const newSet = new Set(prev)
          newSet.delete(index)
          return newSet
        })
        loadingPromises.current.delete(url)
        resolve(img)
      }

      img.onerror = () => {
        setFailedImages(prev => new Set(prev).add(index))
        setLoadingImages(prev => {
          const newSet = new Set(prev)
          newSet.delete(index)
          return newSet
        })
        loadingPromises.current.delete(url)
        resolve(null)
      }

      // Set crossOrigin before src to avoid CORS issues
      img.crossOrigin = 'anonymous'
      img.src = url
    })

    loadingPromises.current.set(url, loadPromise)
    return loadPromise
  }, [])

  const preloadImage = useCallback(async (url: string): Promise<HTMLImageElement | null> => {
    // Check buffer first
    const bufferedImage = globalImageBuffer.get(url)
    if (bufferedImage) {
      return bufferedImage as HTMLImageElement
    }

    // Check if already loading
    const existingPromise = loadingPromises.current.get(url)
    if (existingPromise) {
      return existingPromise
    }

    // Start preloading
    const loadPromise = new Promise<HTMLImageElement | null>((resolve) => {
      const img = new Image()

      img.onload = () => {
        globalImageBuffer.put(url, img)
        loadingPromises.current.delete(url)
        resolve(img)
      }

      img.onerror = () => {
        loadingPromises.current.delete(url)
        resolve(null)
      }

      img.crossOrigin = 'anonymous'
      img.src = url
    })

    loadingPromises.current.set(url, loadPromise)
    return loadPromise
  }, [])

  const updateImageStatus = useCallback((index: number, loaded: boolean) => {
    if (loaded) {
      setLoadedImages(prev => new Set(prev).add(index))
      setFailedImages(prev => {
        const newSet = new Set(prev)
        newSet.delete(index)
        return newSet
      })
    } else {
      setFailedImages(prev => new Set(prev).add(index))
      setLoadedImages(prev => {
        const newSet = new Set(prev)
        newSet.delete(index)
        return newSet
      })
    }
    setLoadingImages(prev => {
      const newSet = new Set(prev)
      newSet.delete(index)
      return newSet
    })
  }, [])

  const clearCache = useCallback(() => {
    globalImageBuffer.clear()
    setLoadedImages(new Set())
    setFailedImages(new Set())
    setLoadingImages(new Set())
    loadingPromises.current.clear()
  }, [])

  return {
    loadedImages,
    failedImages,
    loadingImages,
    loadImage,
    updateImageStatus,
    preloadImage,
    clearCache
  }
}
