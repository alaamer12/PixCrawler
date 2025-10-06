'use client'

import { memo, useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { Image as UnpicImage } from '@unpic/react'
import { motion, AnimatePresence } from 'framer-motion'
import { useKeyPress } from 'react-use'
import {
  X,
  Maximize2,
  Minimize2,
  Download,
  Share2,
  Info,
  ZoomIn,
  ZoomOut,
  RotateCw,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Button } from './button'

interface ImageData {
  src: string
  alt: string
  title?: string
  description?: string
  metadata?: {
    size?: string
    dimensions?: string
    format?: string
    created?: string
    [key: string]: any
  }
}

interface ImageModalProps {
  isOpen: boolean
  onClose: () => void
  images: ImageData[]
  currentIndex?: number
  onIndexChange?: (index: number) => void
}

export const ImageModal = memo(({
  isOpen,
  onClose,
  images,
  currentIndex = 0,
  onIndexChange
}: ImageModalProps) => {
  const [mounted, setMounted] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  const currentImage = images[currentIndex]

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  // Reset transformations when image changes
  useEffect(() => {
    setZoom(1)
    setRotation(0)
    setPosition({ x: 0, y: 0 })
  }, [currentIndex])

  // Keyboard navigation with react-use hooks
  useKeyPress('Escape', () => isOpen && onClose())
  useKeyPress('ArrowLeft', () => {
    if (isOpen && images.length > 1 && currentIndex > 0) {
      onIndexChange?.(currentIndex - 1)
    }
  })
  useKeyPress('ArrowRight', () => {
    if (isOpen && images.length > 1 && currentIndex < images.length - 1) {
      onIndexChange?.(currentIndex + 1)
    }
  })
  useKeyPress('f', () => isOpen && toggleFullscreen())
  useKeyPress('i', () => isOpen && setShowInfo(prev => !prev))
  useKeyPress('+', () => isOpen && handleZoomIn())
  useKeyPress('-', () => isOpen && handleZoomOut())
  useKeyPress('r', () => isOpen && handleRotate())

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }, [])

  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev * 1.2, 5))
  }, [])

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev / 1.2, 0.1))
  }, [])

  const handleRotate = useCallback(() => {
    setRotation(prev => (prev + 90) % 360)
  }, [])

  const handleReset = useCallback(() => {
    setZoom(1)
    setRotation(0)
    setPosition({ x: 0, y: 0 })
  }, [])

  const handleDownload = useCallback(async () => {
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
  }, [currentImage])

  const handleShare = useCallback(async () => {
    if (!currentImage) return

    if (navigator.share) {
      try {
        await navigator.share({
          title: currentImage.title || 'Image',
          text: currentImage.description || '',
          url: currentImage.src
        })
      } catch (error) {
        console.error('Share failed:', error)
      }
    } else {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(currentImage.src)
        // You could show a toast notification here
      } catch (error) {
        console.error('Copy failed:', error)
      }
    }
  }, [currentImage])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (zoom > 1) {
      setIsDragging(true)
      setDragStart({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      })
    }
  }, [zoom, position])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging && zoom > 1) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    }
  }, [isDragging, dragStart, zoom])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handlePrevious = useCallback(() => {
    if (currentIndex > 0) {
      onIndexChange?.(currentIndex - 1)
    }
  }, [currentIndex, onIndexChange])

  const handleNext = useCallback(() => {
    if (currentIndex < images.length - 1) {
      onIndexChange?.(currentIndex + 1)
    }
  }, [currentIndex, images.length, onIndexChange])

  if (!mounted || !currentImage) return null

  const modal = (
    <AnimatePresence>
      {isOpen && (
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
                  onClick={() => setShowInfo(!showInfo)}
                  className="text-white hover:bg-white/20"
                >
                  <Info className="w-5 h-5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleShare}
                  className="text-white hover:bg-white/20"
                >
                  <Share2 className="w-5 h-5" />
                </Button>
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
                  onClick={toggleFullscreen}
                  className="text-white hover:bg-white/20"
                >
                  {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
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
              className="relative max-w-full max-h-full overflow-hidden cursor-grab active:cursor-grabbing"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.3, type: "spring" }}
            >
              <UnpicImage
                src={currentImage.src}
                alt={currentImage.alt}
                layout="constrained"
                width={1200}
                height={800}
                className="max-w-full max-h-full object-contain transition-transform duration-200"
                style={{
                  transform: `scale(${zoom}) rotate(${rotation}deg) translate(${position.x}px, ${position.y}px)`,
                }}
                priority
              />
            </motion.div>
          </div>

          {/* Bottom controls */}
          <div className="absolute bottom-0 left-0 right-0 z-10 bg-gradient-to-t from-black/50 to-transparent">
            <div className="flex items-center justify-center gap-2 p-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomOut}
                className="text-white hover:bg-white/20"
              >
                <ZoomOut className="w-4 h-4" />
              </Button>
              <span className="text-white text-sm min-w-[60px] text-center">
                {Math.round(zoom * 100)}%
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomIn}
                className="text-white hover:bg-white/20"
              >
                <ZoomIn className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRotate}
                className="text-white hover:bg-white/20"
              >
                <RotateCw className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="text-white hover:bg-white/20"
              >
                Reset
              </Button>
            </div>
          </div>

          {/* Info panel */}
          {showInfo && currentImage.metadata && (
            <div className="absolute top-20 right-4 w-80 bg-black/80 backdrop-blur-sm rounded-lg p-4 text-white">
              <h3 className="font-semibold mb-3">Image Details</h3>
              <div className="space-y-2 text-sm">
                {currentImage.description && (
                  <div>
                    <span className="text-white/70">Description:</span>
                    <p className="mt-1">{currentImage.description}</p>
                  </div>
                )}
                {Object.entries(currentImage.metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-white/70 capitalize">{key}:</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Click outside to close */}
          <div
            className="absolute inset-0 -z-10"
            onClick={onClose}
          />
        </motion.div>
      )}
    </AnimatePresence>
  )

  return createPortal(modal, document.body)
})

ImageModal.displayName = 'ImageModal'