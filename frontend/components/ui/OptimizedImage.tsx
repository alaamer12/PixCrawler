'use client'

import { memo, useState, useCallback } from 'react'
import Image from 'next/image'
import { ImageSkeleton } from './ImageSkeleton'
import { Eye, AlertCircle } from 'lucide-react'

interface OptimizedImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape'
  priority?: boolean
  quality?: number
  placeholder?: 'blur' | 'empty'
  blurDataURL?: string
  onClick?: () => void
  showOverlay?: boolean
  overlayContent?: React.ReactNode
  sizes?: string
  fill?: boolean
}

export const OptimizedImage = memo(({
  src,
  alt,
  width,
  height,
  className = '',
  aspectRatio = 'landscape',
  priority = false,
  quality = 75,
  placeholder = 'empty',
  blurDataURL,
  onClick,
  showOverlay = false,
  overlayContent,
  sizes,
  fill = false
}: OptimizedImageProps) => {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  const handleLoad = useCallback(() => {
    setIsLoading(false)
  }, [])

  const handleError = useCallback(() => {
    setIsLoading(false)
    setHasError(true)
  }, [])

  const handleClick = useCallback(() => {
    if (onClick && !hasError) {
      onClick()
    }
  }, [onClick, hasError])

  const aspectClasses = {
    square: 'aspect-square',
    video: 'aspect-video',
    portrait: 'aspect-[3/4]',
    landscape: 'aspect-[4/3]'
  }

  const containerClasses = `
    relative overflow-hidden rounded-lg bg-muted group
    ${fill ? '' : aspectClasses[aspectRatio]}
    ${onClick ? 'cursor-pointer' : ''}
    ${className}
  `

  if (hasError) {
    return (
      <div className={containerClasses}>
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-muted text-muted-foreground">
          <AlertCircle className="w-8 h-8 mb-2" />
          <span className="text-sm">Failed to load image</span>
        </div>
      </div>
    )
  }

  return (
    <div className={containerClasses} onClick={handleClick}>
      {/* Loading skeleton */}
      {isLoading && (
        <div className="absolute inset-0">
          <ImageSkeleton aspectRatio={aspectRatio} />
        </div>
      )}

      {/* Next.js Image */}
      <Image
        src={src}
        alt={alt}
        width={fill ? undefined : width}
        height={fill ? undefined : height}
        fill={fill}
        priority={priority}
        quality={quality}
        placeholder={placeholder}
        blurDataURL={blurDataURL}
        sizes={sizes}
        className={`
          object-cover transition-all duration-300
          ${isLoading ? 'opacity-0' : 'opacity-100'}
          ${onClick ? 'group-hover:scale-105' : ''}
        `}
        onLoad={handleLoad}
        onError={handleError}
      />

      {/* Overlay */}
      {showOverlay && !isLoading && !hasError && (
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors duration-300">
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            {overlayContent || (
              <div className="flex items-center gap-2 text-white">
                <Eye className="w-5 h-5" />
                <span className="text-sm font-medium">View Image</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
})

OptimizedImage.displayName = 'OptimizedImage'