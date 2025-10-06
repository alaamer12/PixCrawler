'use client'

import { memo, useEffect, useRef, useState } from 'react'
import { Image as UnpicImage } from '@unpic/react'
import { useInView } from 'react-intersection-observer'
import { motion } from 'framer-motion'
import { Eye, AlertCircle } from 'lucide-react'
import { globalImageBuffer } from '@/lib/ImageBuffer'

interface ImageData {
  src: string
  alt: string
  title?: string
  description?: string
}

interface OptimizedImageCellProps {
  image: ImageData
  index: number
  loadedImages: Set<number>
  failedImages: Set<number>
  loadImage: (url: string, index: number) => Promise<HTMLImageElement | null>
  updateImageStatus: (index: number, loaded: boolean) => void
  onImageClick: (index: number) => void
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape'
  showOverlay?: boolean
  className?: string
}

const aspectClasses = {
  square: 'aspect-square',
  video: 'aspect-video',
  portrait: 'aspect-[3/4]',
  landscape: 'aspect-[4/3]'
}

export const OptimizedImageCell = memo(({
  image,
  index,
  loadedImages,
  failedImages,
  loadImage,
  updateImageStatus,
  onImageClick,
  aspectRatio = 'square',
  showOverlay = true,
  className = ''
}: OptimizedImageCellProps) => {
  const [imageLoaded, setImageLoaded] = useState(false)
  const isLoaded = loadedImages.has(index)
  const hasFailed = failedImages.has(index)
  const isPriority = index < 16 // First 16 images get priority

  const { ref, inView } = useInView({
    threshold: 0,
    rootMargin: '100% 0px 100% 0px',
    triggerOnce: false
  })

  // Load image when in view
  useEffect(() => {
    if (inView && !isLoaded && !hasFailed) {
      const bufferedImage = globalImageBuffer.get(image.src)
      if (bufferedImage) {
        updateImageStatus(index, true)
        setImageLoaded(true)
      } else {
        loadImage(image.src, index).then((loadedImg) => {
          if (loadedImg) {
            setImageLoaded(true)
          }
        })
      }
    }
  }, [inView, isLoaded, hasFailed, image.src, index, loadImage, updateImageStatus])

  const handleImageLoad = () => {
    if (!loadedImages.has(index)) {
      updateImageStatus(index, true)
    }
    setImageLoaded(true)
  }

  const handleImageError = () => {
    updateImageStatus(index, false)
    setImageLoaded(false)
  }

  const handleClick = () => {
    if (!hasFailed) {
      onImageClick(index)
    }
  }

  if (hasFailed) {
    return (
      <div 
        ref={ref}
        className={`${aspectClasses[aspectRatio]} ${className} relative overflow-hidden rounded-lg bg-muted flex items-center justify-center`}
      >
        <div className="flex flex-col items-center text-muted-foreground">
          <AlertCircle className="w-8 h-8 mb-2" />
          <span className="text-sm">Failed to load</span>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      ref={ref}
      className={`${aspectClasses[aspectRatio]} ${className} relative overflow-hidden rounded-lg bg-muted cursor-pointer group`}
      onClick={handleClick}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Loading skeleton */}
      {!imageLoaded && (
        <div className="absolute inset-0 bg-muted animate-pulse">
          <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg 
              className="w-8 h-8 text-muted-foreground/50" 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path 
                fillRule="evenodd" 
                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" 
                clipRule="evenodd" 
              />
            </svg>
          </div>
        </div>
      )}

      {/* Image */}
      {inView && (
        <UnpicImage
          src={image.src}
          alt={image.alt}
          layout="fullWidth"
          priority={isPriority}
          loading={isPriority ? "eager" : "lazy"}
          className={`w-full h-full object-cover transition-all duration-300 ${
            imageLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onLoad={handleImageLoad}
          onError={handleImageError}
        />
      )}

      {/* Overlay */}
      {showOverlay && imageLoaded && (
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors duration-300">
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="flex items-center gap-2 text-white">
              <Eye className="w-5 h-5" />
              <span className="text-sm font-medium">View</span>
            </div>
          </div>
        </div>
      )}

      {/* Image title overlay */}
      {image.title && imageLoaded && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <p className="text-white text-sm font-medium truncate">{image.title}</p>
        </div>
      )}
    </motion.div>
  )
})

OptimizedImageCell.displayName = 'OptimizedImageCell'