'use client'

import {memo, useState} from 'react'
import Image from 'next/image'
import {AlertCircle, Loader2} from 'lucide-react'

interface NextImageProps {
  src: string
  alt: string
  className?: string
  width?: number
  height?: number
  priority?: boolean
  onClick?: () => void
  onLoad?: () => void
  onError?: () => void
}

export const NextImage = memo(({
                                 src,
                                 alt,
                                 className = '',
                                 width = 200,
                                 height = 200,
                                 priority = false,
                                 onClick,
                                 onLoad,
                                 onError
                               }: NextImageProps) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  const handleClick = (e: React.MouseEvent) => {
    console.log('NextImage clicked:', {src, hasError, hasOnClick: !!onClick})
    e.stopPropagation()
    if (!hasError && onClick) {
      onClick()
    }
  }

  if (hasError) {
    return (
      <div className={`flex items-center justify-center bg-muted ${className}`} onClick={handleClick}>
        <AlertCircle className="w-4 h-4 text-muted-foreground"/>
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      {/* Loading state */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted">
          <Loader2 className="w-4 h-4 text-muted-foreground animate-spin"/>
        </div>
      )}

      {/* Next.js Image */}
      <Image
        src={src}
        alt={alt}
        width={width}
        height={height}
        className={`transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'} ${onClick ? 'cursor-pointer' : ''}`}
        onLoad={handleLoad}
        onError={handleError}
        onClick={handleClick}
        priority={priority}
        style={{width: '100%', height: '100%', objectFit: 'cover'}}
      />

      {/* Clickable overlay for better click handling */}
      {onClick && (
        <div
          className="absolute inset-0 cursor-pointer"
          onClick={handleClick}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              handleClick(e as any)
            }
          }}
        />
      )}
    </div>
  )
})

NextImage.displayName = 'NextImage'
