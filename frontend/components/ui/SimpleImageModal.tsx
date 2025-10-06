'use client'

import { memo, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import Image from 'next/image'
import { X, ChevronLeft, ChevronRight, Maximize2, Minimize2, Download, Info, Grid3X3, ZoomIn, ZoomOut } from 'lucide-react'

interface ImageData {
  src: string
  alt: string
  title?: string
}

interface SimpleImageModalProps {
  isOpen: boolean
  onClose: () => void
  images: ImageData[]
  currentIndex: number
  onIndexChange?: (index: number) => void
}

export const SimpleImageModal = memo(({
  isOpen,
  onClose,
  images,
  currentIndex,
  onIndexChange
}: SimpleImageModalProps) => {
  const [mounted, setMounted] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [imageScale, setImageScale] = useState(1)
  const currentImage = images[currentIndex]

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft' && currentIndex > 0) onIndexChange?.(currentIndex - 1)
      if (e.key === 'ArrowRight' && currentIndex < images.length - 1) onIndexChange?.(currentIndex + 1)
      if (e.key === 'f' || e.key === 'F') setIsFullscreen(!isFullscreen)
      if (e.key === 'i' || e.key === 'I') setShowInfo(!showInfo)
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, currentIndex, images.length, onIndexChange, onClose, isFullscreen, showInfo])

  // Reset scale when image changes
  useEffect(() => {
    setImageScale(1)
  }, [currentIndex])

  const handleZoomIn = () => setImageScale(prev => Math.min(prev * 1.2, 3))
  const handleZoomOut = () => setImageScale(prev => Math.max(prev / 1.2, 0.5))

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = currentImage.src
    link.download = currentImage.title || `image-${currentIndex + 1}`
    link.click()
  }

  if (!mounted || !isOpen || !currentImage) return null

  return createPortal(
    <div className={`fixed inset-0 z-50 bg-black/95 backdrop-blur-sm transition-all duration-300 ${isFullscreen ? 'bg-black' : ''}`}>
      {/* Header Bar */}
      <div className={`absolute top-0 left-0 right-0 z-20 bg-gradient-to-b from-black/80 to-transparent p-4 transition-opacity duration-300 ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}>
        <div className="flex items-center justify-between">
          {/* Left: Image counter and title */}
          <div className="flex items-center gap-4 text-white">
            <div className="bg-black/50 backdrop-blur-sm rounded-lg px-3 py-1.5 text-sm font-medium">
              IMAGE • {currentIndex + 1} / {images.length}
            </div>
            {currentImage.title && (
              <div className="text-lg font-medium truncate max-w-md">
                {currentImage.title}
              </div>
            )}
          </div>

          {/* Right: Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowInfo(!showInfo)}
              className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
              title="Toggle Info (I)"
            >
              <Info className="w-5 h-5" />
            </button>
            
            <button
              onClick={handleDownload}
              className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
              title="Download"
            >
              <Download className="w-5 h-5" />
            </button>

            <div className="w-px h-6 bg-white/20" />

            <button
              onClick={handleZoomOut}
              disabled={imageScale <= 0.5}
              className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
              title="Zoom Out"
            >
              <ZoomOut className="w-5 h-5" />
            </button>

            <div className="bg-black/50 backdrop-blur-sm rounded-lg px-3 py-1 text-sm font-medium text-white min-w-[60px] text-center">
              {Math.round(imageScale * 100)}%
            </div>

            <button
              onClick={handleZoomIn}
              disabled={imageScale >= 3}
              className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
              title="Zoom In"
            >
              <ZoomIn className="w-5 h-5" />
            </button>

            <div className="w-px h-6 bg-white/20" />

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
              title={isFullscreen ? "Exit Fullscreen (F)" : "Fullscreen (F)"}
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>

            <button
              onClick={onClose}
              className="p-2 text-white hover:bg-red-500/20 rounded-lg transition-colors"
              title="Close (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Arrows */}
      {images.length > 1 && (
        <>
          <button
            onClick={() => currentIndex > 0 && onIndexChange?.(currentIndex - 1)}
            disabled={currentIndex === 0}
            className={`absolute left-6 top-1/2 -translate-y-1/2 z-10 p-3 text-white bg-black/50 backdrop-blur-sm hover:bg-black/70 rounded-full transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}
            title="Previous Image (←)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          <button
            onClick={() => currentIndex < images.length - 1 && onIndexChange?.(currentIndex + 1)}
            disabled={currentIndex === images.length - 1}
            className={`absolute right-6 top-1/2 -translate-y-1/2 z-10 p-3 text-white bg-black/50 backdrop-blur-sm hover:bg-black/70 rounded-full transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}
            title="Next Image (→)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        </>
      )}

      {/* Main Image Container */}
      <div className="absolute inset-0 flex items-center justify-center p-4 pt-20 pb-4">
        <div 
          className="relative transition-transform duration-200 ease-out cursor-grab active:cursor-grabbing"
          style={{ 
            transform: `scale(${imageScale})`,
            maxWidth: isFullscreen ? '100vw' : '90vw',
            maxHeight: isFullscreen ? '100vh' : '80vh'
          }}
        >
          <Image
            src={currentImage.src}
            alt={currentImage.alt}
            width={1200}
            height={800}
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            priority
            draggable={false}
          />
        </div>
      </div>

      {/* Info Panel */}
      {showInfo && (
        <div className={`absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-black/90 to-transparent p-6 transition-opacity duration-300 ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}>
          <div className="bg-black/50 backdrop-blur-sm rounded-lg p-4 text-white">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-white/60 mb-1">Image</div>
                <div className="font-medium">{currentImage.title || `Image ${currentIndex + 1}`}</div>
              </div>
              <div>
                <div className="text-white/60 mb-1">Alt Text</div>
                <div className="font-medium">{currentImage.alt}</div>
              </div>
              <div>
                <div className="text-white/60 mb-1">Source</div>
                <div className="font-medium truncate">{currentImage.src}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Thumbnail Strip (when multiple images) */}
      {images.length > 1 && !isFullscreen && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
          <div className="bg-black/50 backdrop-blur-sm rounded-lg p-2 flex gap-2 max-w-md overflow-x-auto">
            {images.slice(Math.max(0, currentIndex - 2), currentIndex + 3).map((img, idx) => {
              const actualIndex = Math.max(0, currentIndex - 2) + idx
              return (
                <button
                  key={actualIndex}
                  onClick={() => onIndexChange?.(actualIndex)}
                  className={`relative w-12 h-12 rounded overflow-hidden transition-all duration-200 ${
                    actualIndex === currentIndex 
                      ? 'ring-2 ring-white scale-110' 
                      : 'hover:scale-105 opacity-70 hover:opacity-100'
                  }`}
                >
                  <Image
                    src={img.src}
                    alt={img.alt}
                    width={48}
                    height={48}
                    className="w-full h-full object-cover"
                  />
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Click outside to close */}
      <div className="absolute inset-0 -z-10" onClick={onClose} />
    </div>,
    document.body
  )
})

SimpleImageModal.displayName = 'SimpleImageModal'