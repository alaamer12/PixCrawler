'use client'

import {memo, useEffect, useState} from 'react'
import {createPortal} from 'react-dom'
import Image from 'next/image'
import {ChevronLeft, ChevronRight, Download, Info, Maximize2, Minimize2, X, ZoomIn, ZoomOut} from 'lucide-react'

// Types
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

// Header Component
const ModalHeader = memo(({
                            currentIndex,
                            totalImages,
                            title,
                            isFullscreen,
                            showInfo,
                            imageScale,
                            onToggleInfo,
                            onDownload,
                            onZoomIn,
                            onZoomOut,
                            onToggleFullscreen,
                            onClose
                          }: {
  currentIndex: number
  totalImages: number
  title?: string
  isFullscreen: boolean
  showInfo: boolean
  imageScale: number
  onToggleInfo: () => void
  onDownload: () => void
  onZoomIn: () => void
  onZoomOut: () => void
  onToggleFullscreen: () => void
  onClose: () => void
}) => (
  <div
    className={`absolute top-0 left-0 right-0 z-20 bg-gradient-to-b from-black/80 to-transparent p-4 transition-opacity duration-300 ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}>
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4 text-white">
        <div className="bg-black/50 backdrop-blur-sm rounded-lg px-3 py-1.5 text-sm font-medium">
          IMAGE • {currentIndex + 1} / {totalImages}
        </div>
        {title && (
          <div className="text-lg font-medium truncate max-w-md">
            {title}
          </div>
        )}
      </div>

      <HeaderActions
        showInfo={showInfo}
        imageScale={imageScale}
        isFullscreen={isFullscreen}
        onToggleInfo={onToggleInfo}
        onDownload={onDownload}
        onZoomIn={onZoomIn}
        onZoomOut={onZoomOut}
        onToggleFullscreen={onToggleFullscreen}
        onClose={onClose}
      />
    </div>
  </div>
))

ModalHeader.displayName = 'ModalHeader'

// Header Actions Component
const HeaderActions = memo(({
                              showInfo,
                              imageScale,
                              isFullscreen,
                              onToggleInfo,
                              onDownload,
                              onZoomIn,
                              onZoomOut,
                              onToggleFullscreen,
                              onClose
                            }: {
  showInfo: boolean
  imageScale: number
  isFullscreen: boolean
  onToggleInfo: () => void
  onDownload: () => void
  onZoomIn: () => void
  onZoomOut: () => void
  onToggleFullscreen: () => void
  onClose: () => void
}) => (
  <div className="flex items-center gap-2">
    <button
      onClick={onToggleInfo}
      className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
      title="Toggle Info (I)"
    >
      <Info className="w-5 h-5"/>
    </button>

    <button
      onClick={onDownload}
      className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
      title="Download"
    >
      <Download className="w-5 h-5"/>
    </button>

    <div className="w-px h-6 bg-white/20"/>

    <ZoomControls
      scale={imageScale}
      onZoomIn={onZoomIn}
      onZoomOut={onZoomOut}
    />

    <div className="w-px h-6 bg-white/20"/>

    <button
      onClick={onToggleFullscreen}
      className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
      title={isFullscreen ? "Exit Fullscreen (F)" : "Fullscreen (F)"}
    >
      {isFullscreen ? <Minimize2 className="w-5 h-5"/> : <Maximize2 className="w-5 h-5"/>}
    </button>

    <button
      onClick={onClose}
      className="p-2 text-white hover:bg-red-500/20 rounded-lg transition-colors"
      title="Close (Esc)"
    >
      <X className="w-5 h-5"/>
    </button>
  </div>
))

HeaderActions.displayName = 'HeaderActions'

// Zoom Controls Component
const ZoomControls = memo(({
                             scale,
                             onZoomIn,
                             onZoomOut
                           }: {
  scale: number
  onZoomIn: () => void
  onZoomOut: () => void
}) => (
  <>
    <button
      onClick={onZoomOut}
      disabled={scale <= 0.5}
      className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
      title="Zoom Out"
    >
      <ZoomOut className="w-5 h-5"/>
    </button>

    <div
      className="bg-black/50 backdrop-blur-sm rounded-lg px-3 py-1 text-sm font-medium text-white min-w-[60px] text-center">
      {Math.round(scale * 100)}%
    </div>

    <button
      onClick={onZoomIn}
      disabled={scale >= 3}
      className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors disabled:opacity-50"
      title="Zoom In"
    >
      <ZoomIn className="w-5 h-5"/>
    </button>
  </>
))

ZoomControls.displayName = 'ZoomControls'

// Navigation Arrows Component
const NavigationArrows = memo(({
                                 currentIndex,
                                 totalImages,
                                 isFullscreen,
                                 onPrevious,
                                 onNext
                               }: {
  currentIndex: number
  totalImages: number
  isFullscreen: boolean
  onPrevious: () => void
  onNext: () => void
}) => {
  if (totalImages <= 1) return null

  return (
    <>
      <button
        onClick={onPrevious}
        disabled={currentIndex === 0}
        className={`absolute left-6 top-1/2 -translate-y-1/2 z-10 p-3 text-white bg-black/50 backdrop-blur-sm hover:bg-black/70 rounded-full transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}
        title="Previous Image (←)"
      >
        <ChevronLeft className="w-6 h-6"/>
      </button>
      <button
        onClick={onNext}
        disabled={currentIndex === totalImages - 1}
        className={`absolute right-6 top-1/2 -translate-y-1/2 z-10 p-3 text-white bg-black/50 backdrop-blur-sm hover:bg-black/70 rounded-full transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}
        title="Next Image (→)"
      >
        <ChevronRight className="w-6 h-6"/>
      </button>
    </>
  )
})

NavigationArrows.displayName = 'NavigationArrows'

// Image Display Component
const ImageDisplay = memo(({
                             image,
                             scale,
                             isFullscreen
                           }: {
  image: ImageData
  scale: number
  isFullscreen: boolean
}) => (
  <div className="absolute inset-0 flex items-center justify-center p-4 pt-20 pb-4">
    <div
      className="relative transition-transform duration-200 ease-out cursor-grab active:cursor-grabbing"
      style={{
        transform: `scale(${scale})`,
        maxWidth: isFullscreen ? '100vw' : '90vw',
        maxHeight: isFullscreen ? '100vh' : '80vh'
      }}
    >
      <Image
        src={image.src}
        alt={image.alt}
        width={1200}
        height={800}
        className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
        priority
        draggable={false}
      />
    </div>
  </div>
))

ImageDisplay.displayName = 'ImageDisplay'

// Info Panel Component
const InfoPanel = memo(({
                          image,
                          currentIndex,
                          isVisible,
                          isFullscreen
                        }: {
  image: ImageData
  currentIndex: number
  isVisible: boolean
  isFullscreen: boolean
}) => {
  if (!isVisible) return null

  return (
    <div
      className={`absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-black/90 to-transparent p-6 transition-opacity duration-300 ${isFullscreen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}>
      <div className="bg-black/50 backdrop-blur-sm rounded-lg p-4 text-white">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-white/60 mb-1">Image</div>
            <div className="font-medium">{image.title || `Image ${currentIndex + 1}`}</div>
          </div>
          <div>
            <div className="text-white/60 mb-1">Alt Text</div>
            <div className="font-medium">{image.alt}</div>
          </div>
          <div>
            <div className="text-white/60 mb-1">Source</div>
            <div className="font-medium truncate">{image.src}</div>
          </div>
        </div>
      </div>
    </div>
  )
})

InfoPanel.displayName = 'InfoPanel'

// Thumbnail Strip Component
const ThumbnailStrip = memo(({
                               images,
                               currentIndex,
                               isFullscreen,
                               onSelectImage
                             }: {
  images: ImageData[]
  currentIndex: number
  isFullscreen: boolean
  onSelectImage: (index: number) => void
}) => {
  if (images.length <= 1 || isFullscreen) return null

  const visibleImages = images.slice(Math.max(0, currentIndex - 2), currentIndex + 3)
  const startIndex = Math.max(0, currentIndex - 2)

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20">
      <div className="bg-black/50 backdrop-blur-sm rounded-lg p-2 flex gap-2 max-w-md overflow-x-auto">
        {visibleImages.map((img, idx) => {
          const actualIndex = startIndex + idx
          return (
            <button
              key={actualIndex}
              onClick={() => onSelectImage(actualIndex)}
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
  )
})

ThumbnailStrip.displayName = 'ThumbnailStrip'

// Custom Hook for Keyboard Navigation
const useKeyboardNavigation = (
  isOpen: boolean,
  currentIndex: number,
  totalImages: number,
  isFullscreen: boolean,
  showInfo: boolean,
  onClose: () => void,
  onIndexChange?: (index: number) => void,
  onToggleFullscreen?: () => void,
  onToggleInfo?: () => void
) => {
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft' && currentIndex > 0) onIndexChange?.(currentIndex - 1)
      if (e.key === 'ArrowRight' && currentIndex < totalImages - 1) onIndexChange?.(currentIndex + 1)
      if (e.key === 'f' || e.key === 'F') onToggleFullscreen?.()
      if (e.key === 'i' || e.key === 'I') onToggleInfo?.()
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, currentIndex, totalImages, onIndexChange, onClose, isFullscreen, showInfo, onToggleFullscreen, onToggleInfo])
}

// Custom Hook for Zoom
const useZoom = (currentIndex: number) => {
  const [imageScale, setImageScale] = useState(1)

  useEffect(() => {
    setImageScale(1)
  }, [currentIndex])

  const handleZoomIn = () => setImageScale(prev => Math.min(prev * 1.2, 3))
  const handleZoomOut = () => setImageScale(prev => Math.max(prev / 1.2, 0.5))

  return {imageScale, handleZoomIn, handleZoomOut}
}

// Main Modal Component
export const ImageModal = memo(({
                                  isOpen,
                                  onClose,
                                  images,
                                  currentIndex,
                                  onIndexChange
                                }: SimpleImageModalProps) => {
  const [mounted, setMounted] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const {imageScale, handleZoomIn, handleZoomOut} = useZoom(currentIndex)
  const currentImage = images[currentIndex]

  useEffect(() => {
    setMounted(true)
    return () => setMounted(false)
  }, [])

  const toggleFullscreen = () => setIsFullscreen(prev => !prev)
  const toggleInfo = () => setShowInfo(prev => !prev)

  useKeyboardNavigation(
    isOpen,
    currentIndex,
    images.length,
    isFullscreen,
    showInfo,
    onClose,
    onIndexChange,
    toggleFullscreen,
    toggleInfo
  )

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = currentImage.src
    link.download = currentImage.title || `image-${currentIndex + 1}`
    link.click()
  }

  const handlePrevious = () => {
    if (currentIndex > 0) onIndexChange?.(currentIndex - 1)
  }

  const handleNext = () => {
    if (currentIndex < images.length - 1) onIndexChange?.(currentIndex + 1)
  }

  if (!mounted || !isOpen || !currentImage) return null

  return createPortal(
    <div
      className={`fixed inset-0 z-50 bg-black/95 backdrop-blur-sm transition-all duration-300 ${isFullscreen ? 'bg-black' : ''}`}>
      <ModalHeader
        currentIndex={currentIndex}
        totalImages={images.length}
        title={currentImage.title}
        isFullscreen={isFullscreen}
        showInfo={showInfo}
        imageScale={imageScale}
        onToggleInfo={toggleInfo}
        onDownload={handleDownload}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onToggleFullscreen={toggleFullscreen}
        onClose={onClose}
      />

      <NavigationArrows
        currentIndex={currentIndex}
        totalImages={images.length}
        isFullscreen={isFullscreen}
        onPrevious={handlePrevious}
        onNext={handleNext}
      />

      <ImageDisplay
        image={currentImage}
        scale={imageScale}
        isFullscreen={isFullscreen}
      />

      <InfoPanel
        image={currentImage}
        currentIndex={currentIndex}
        isVisible={showInfo}
        isFullscreen={isFullscreen}
      />

      <ThumbnailStrip
        images={images}
        currentIndex={currentIndex}
        isFullscreen={isFullscreen}
        onSelectImage={onIndexChange || (() => {
        })}
      />

      <div className="absolute inset-0 -z-10" onClick={onClose}/>
    </div>,
    document.body
  )
})

ImageModal.displayName = 'ImageModal'
