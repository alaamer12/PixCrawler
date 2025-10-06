'use client'

import { memo, useState, useCallback, useRef, useEffect } from 'react'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { Eye, AlertCircle, X, ChevronLeft, ChevronRight, Download, Share2, Maximize2 } from 'lucide-react'
import { Button } from './button'

interface ImageData {
  src: string
  alt: string
  title?: string
  description?: string
  width?: number
  height?: number
}

interface NextImageGalleryProps {
  images: ImageData[]
  className?: string
  columns?: 2 | 3 | 4 | 5 | 6
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape'
  showOverlay?: boolean
  gap?: 'sm' | 'md' | 'lg'
  enableModal?: boolean
}

interface ImageCellProps {
  image: ImageData
  index: number
  aspectRatio: string
  showOverlay: boolean
  onClick: (index: number) => void
}

const ImageCell = memo(({ image, index, aspectRatio, showOverlay, onClick }: ImageCellProps) => {
  const [isLoaded, setIsLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)

  const aspectClasses = {
    square: 'aspect-square',
    video: 'aspect-video',
    portrait: 'aspect-[3/4]',
    landscape: 'aspect-[4/3]'
  }

  const handleLoad = () => setIsLoaded(true)
  const handleError = () => setHasError(true)
  const handleClick = () => !hasError && onClick(index)

  if (hasError) {
    return (
      <div className={`${aspectClasses[aspectRatio as keyof typeof aspectClasses]} relative overflow-hidden rounded-lg bg-muted flex items-center justify-center`}>
        <div className="flex flex-col items-center text-muted-foreground">
          <AlertCircle className="w-8 h-8 mb-2" />
          <span className="text-sm">Failed to load</span>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      className={`${aspectClasses[aspectRatio as keyof typeof aspectClasses]} relative overflow-hidden rounded-lg bg-muted cursor-pointer group`}
      onClick={handleClick}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Loading skeleton */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-muted animate-pulse">
          <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent" />
        </div>
      )}

      {/* Next.js Image */}
      <Image
        src={image.src}
        alt={image.alt}
        fill
        className={`object-cover transition-all duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
        onLoad={handleLoad}
        onError={handleError}
        priority={index < 6} // First 6 images get priority
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      />

      {/* Overlay */}
      {showOverlay && isLoaded && (
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors duration-300">
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="flex items-center gap-2 text-white">
              <Eye className="w-5 h-5" />
              <span className="text-sm font-medium">View</span>
            </div>
          </div>
        </div>
      )}

      {/* Title overlay */}
      {image.title && isLoaded && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <p className="text-white text-sm font-medium truncate">{image.title}</p>
        </div>
      )}
    </motion.div>
  )
})

ImageCell.displayName = 'ImageCell'

interface ImageModalProps {
  isOpen: boolean
  onClose: () => void
  images: ImageData[]
  currentIndex: number
  onIndexChange: (index: number) => void
}

const ImageModal = memo(({ isOpen, onClose, images, currentIndex, onIndexChange }: ImageModalProps) => {
  const [mounted, setMounted] = useState(false)
  const currentImage = images[currentIndex]

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          onClose()
          break
        case 'ArrowLeft':
          if (currentIndex > 0) onIndexChange(currentIndex - 1)
          break
        case 'ArrowRight':
          if (currentIndex < images.length - 1) onIndexChange(currentIndex + 1)
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, currentIndex, images.length, onIndexChange, onClose])

  const handlePrevious = () => {
    if (currentIndex > 0) onIndexChange(currentIndex - 1)
  }

  const handleNext = () => {
    if (currentIndex < images.length - 1) onIndexChange(currentIndex + 1)
  }

  const handleDownload = async () => {
    if (!currentImage) return
    try {
      const response = await fetch(currentImage.src)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = currentImage.title || 'image'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  if (!mounted || !isOpen || !currentImage) return null

  return (
    <AnimatePresence>
      <motion.div 
        className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/50 to-transparent">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-2 text-white">
              <h2 className="text-lg font-semibold truncate max-w-md">
                {currentImage.title || currentImage.alt}
              </h2>
              {images.length > 1 && (
                <span className="text-sm text-white/70">
                  {currentIndex + 1} of {images.length}
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleDownload}
                className="text-white hover:bg-white/20"
              >
                <Download className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="text-white hover:bg-white/20"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="absolute inset-0 flex items-center justify-center p-4 pt-20 pb-20">
          {/* Navigation arrows */}
          {images.length > 1 && (
            <>
              <Button
                variant="ghost"
                size="icon"
                onClick={handlePrevious}
                disabled={currentIndex === 0}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 disabled:opacity-50"
              >
                <ChevronLeft className="w-6 h-6" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleNext}
                disabled={currentIndex === images.length - 1}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 disabled:opacity-50"
              >
                <ChevronRight className="w-6 h-6" />
              </Button>
            </>
          )}

          {/* Image container */}
          <motion.div 
            className="relative max-w-full max-h-full"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3, type: "spring" }}
          >
            <Image
              src={currentImage.src}
              alt={currentImage.alt}
              width={currentImage.width || 1200}
              height={currentImage.height || 800}
              className="max-w-full max-h-full object-contain"
              priority
            />
          </motion.div>
        </div>

        {/* Click outside to close */}
        <div 
          className="absolute inset-0 -z-10" 
          onClick={onClose}
        />
      </motion.div>
    </AnimatePresence>
  )
})

ImageModal.displayName = 'ImageModal'

export const NextImageGallery = memo(({
  images,
  className = '',
  columns = 3,
  aspectRatio = 'square',
  showOverlay = true,
  gap = 'md',
  enableModal = true
}: NextImageGalleryProps) => {
  const [modalOpen, setModalOpen] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)

  const handleImageClick = useCallback((index: number) => {
    if (enableModal) {
      setCurrentIndex(index)
      setModalOpen(true)
    }
  }, [enableModal])

  const handleCloseModal = useCallback(() => {
    setModalOpen(false)
  }, [])

  const handleIndexChange = useCallback((index: number) => {
    setCurrentIndex(index)
  }, [])

  const gridClasses = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
    5: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5',
    6: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6'
  }

  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6'
  }

  return (
    <>
      <motion.div 
        className={`grid ${gridClasses[columns]} ${gapClasses[gap]} ${className}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {images.map((image, index) => (
          <ImageCell
            key={`${image.src}-${index}`}
            image={image}
            index={index}
            aspectRatio={aspectRatio}
            showOverlay={showOverlay}
            onClick={handleImageClick}
          />
        ))}
      </motion.div>

      {enableModal && (
        <ImageModal
          isOpen={modalOpen}
          onClose={handleCloseModal}
          images={images}
          currentIndex={currentIndex}
          onIndexChange={handleIndexChange}
        />
      )}
    </>
  )
})

NextImageGallery.displayName = 'NextImageGallery'