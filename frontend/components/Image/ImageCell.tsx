'use client'

import {memo, useEffect, useState} from 'react'
import {Image as UnpicImage} from '@unpic/react'
import {useInView} from 'react-intersection-observer'
import {motion} from 'framer-motion'
import {AlertCircle, Eye} from 'lucide-react'
import {globalImageBuffer} from '@/lib/ImageBuffer'

// Types
interface ImageData {
  src: string
  alt: string
  title?: string
  description?: string
}

interface ImageCellProps {
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

// Constants
const ASPECT_CLASSES = {
  square: 'aspect-square',
  video: 'aspect-video',
  portrait: 'aspect-[3/4]',
  landscape: 'aspect-[4/3]'
} as const

const PRIORITY_THRESHOLD = 16
const IN_VIEW_CONFIG = {
  threshold: 0,
  rootMargin: '100% 0px 100% 0px',
  triggerOnce: false
}

const ANIMATION_CONFIG = {
  initial: {opacity: 0, scale: 0.9},
  animate: {opacity: 1, scale: 1},
  transition: {duration: 0.3},
  hover: {scale: 1.02},
  tap: {scale: 0.98}
}

// Sub-components
const LoadingSkeleton = memo(() => (
  <div className="absolute inset-0 bg-muted animate-pulse">
    <div
      className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent"/>
    <div className="absolute inset-0 flex items-center justify-center">
      <svg
        className="w-8 h-8 text-muted-foreground/50"
        fill="currentColor"
        viewBox="0 0 20 20"
        aria-hidden="true"
      >
        <path
          fillRule="evenodd"
          d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
          clipRule="evenodd"
        />
      </svg>
    </div>
  </div>
))
LoadingSkeleton.displayName = 'LoadingSkeleton'

const ErrorState = memo(({aspectRatio, className}: { aspectRatio: string; className: string }) => (
  <div
    className={`${aspectRatio} ${className} relative overflow-hidden rounded-lg bg-muted flex items-center justify-center`}
    role="alert"
    aria-live="polite"
  >
    <div className="flex flex-col items-center text-muted-foreground">
      <AlertCircle className="w-8 h-8 mb-2" aria-hidden="true"/>
      <span className="text-sm">Failed to load</span>
    </div>
  </div>
))
ErrorState.displayName = 'ErrorState'

const ImageOverlay = memo(({title}: { title?: string }) => (
  <>
    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors duration-300">
      <div
        className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="flex items-center gap-2 text-white">
          <Eye className="w-5 h-5" aria-hidden="true"/>
          <span className="text-sm font-medium">View</span>
        </div>
      </div>
    </div>

    {title && (
      <div
        className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <p className="text-white text-sm font-medium truncate" title={title}>
          {title}
        </p>
      </div>
    )}
  </>
))
ImageOverlay.displayName = 'ImageOverlay'

const OptimizedImage = memo(({
                               image,
                               isPriority,
                               imageLoaded,
                               onLoad,
                               onError
                             }: {
  image: ImageData
  isPriority: boolean
  imageLoaded: boolean
  onLoad: () => void
  onError: () => void
}) => (
  <UnpicImage
    src={image.src}
    alt={image.alt}
    layout="fullWidth"
    priority={isPriority}
    loading={isPriority ? "eager" : "lazy"}
    className={`w-full h-full object-cover transition-all duration-300 ${
      imageLoaded ? 'opacity-100' : 'opacity-0'
    }`}
    onLoad={onLoad}
    onError={onError}
  />
))
OptimizedImage.displayName = 'OptimizedImage'

// Custom hooks
const useImageLoading = (
  image: ImageData,
  index: number,
  inView: boolean,
  isLoaded: boolean,
  hasFailed: boolean,
  loadImage: (url: string, index: number) => Promise<HTMLImageElement | null>,
  updateImageStatus: (index: number, loaded: boolean) => void
) => {
  const [imageLoaded, setImageLoaded] = useState(false)

  useEffect(() => {
    if (!inView || isLoaded || hasFailed) return

    const bufferedImage = globalImageBuffer.get(image.src)
    if (bufferedImage) {
      updateImageStatus(index, true)
      setImageLoaded(true)
      return
    }

    loadImage(image.src, index).then((loadedImg) => {
      if (loadedImg) {
        setImageLoaded(true)
      }
    })
  }, [inView, isLoaded, hasFailed, image.src, index, loadImage, updateImageStatus])

  return {imageLoaded, setImageLoaded}
}

const useImageHandlers = (
  index: number,
  loadedImages: Set<number>,
  updateImageStatus: (index: number, loaded: boolean) => void,
  onImageClick: (index: number) => void,
  hasFailed: boolean,
  setImageLoaded: (loaded: boolean) => void
) => {
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

  return {handleImageLoad, handleImageError, handleClick}
}

// Main component
export const ImageCell = memo(({
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
                               }: ImageCellProps) => {
  const isLoaded = loadedImages.has(index)
  const hasFailed = failedImages.has(index)
  const isPriority = index < PRIORITY_THRESHOLD
  const aspectClass = ASPECT_CLASSES[aspectRatio]

  const {ref, inView} = useInView(IN_VIEW_CONFIG)

  const {imageLoaded, setImageLoaded} = useImageLoading(
    image,
    index,
    inView,
    isLoaded,
    hasFailed,
    loadImage,
    updateImageStatus
  )

  const {handleImageLoad, handleImageError, handleClick} = useImageHandlers(
    index,
    loadedImages,
    updateImageStatus,
    onImageClick,
    hasFailed,
    setImageLoaded
  )

  if (hasFailed) {
    return <ErrorState aspectRatio={aspectClass} className={className}/>
  }

  return (
    <motion.div
      ref={ref}
      className={`${aspectClass} ${className} relative overflow-hidden rounded-lg bg-muted cursor-pointer group`}
      onClick={handleClick}
      initial={ANIMATION_CONFIG.initial}
      animate={ANIMATION_CONFIG.animate}
      transition={ANIMATION_CONFIG.transition}
      whileHover={ANIMATION_CONFIG.hover}
      whileTap={ANIMATION_CONFIG.tap}
      role="button"
      tabIndex={0}
      aria-label={`View ${image.alt}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleClick()
        }
      }}
    >
      {!imageLoaded && <LoadingSkeleton/>}

      {inView && (
        <OptimizedImage
          image={image}
          isPriority={isPriority}
          imageLoaded={imageLoaded}
          onLoad={handleImageLoad}
          onError={handleImageError}
        />
      )}

      {showOverlay && imageLoaded && <ImageOverlay title={image.title}/>}
    </motion.div>
  )
})

ImageCell.displayName = 'ImageCell'
