'use client'

import { memo, useState, useCallback, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useImageLoader } from '@/hooks/useImageLoader'
import { useImagePreloader } from '@/hooks/useImagePreloader'
import { OptimizedImage } from './OptimizedImage'
import { ImageModal } from './ImageModal'
import { OptimizedImageCell } from './OptimizedImageCell'
import { OptimizedImageCell } from './OptimizedImageCell'

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

interface ImageGalleryProps {
  images: ImageData[]
  className?: string
  minColumns?: number
  maxColumns?: number
  minItemSize?: number
  gap?: number
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape'
  showOverlay?: boolean
  virtualized?: boolean
  height?: number
}

const MIN_ITEM_SIZE = 200

export const ImageGallery = memo(({
  images,
  className = '',
  minColumns = 2,
  maxColumns = 6,
  minItemSize = MIN_ITEM_SIZE,
  gap = 8,
  aspectRatio = 'square',
  showOverlay = true,
  virtualized = true,
  height = 600
}: ImageGalleryProps) => {
  const [modalOpen, setModalOpen] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const gridDataRef = useRef({ columnCount: minColumns, itemSize: minItemSize })
  const lastScrollPosRef = useRef(0)
  const cleanupTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const { loadedImages, failedImages, loadImage, updateImageStatus, preloadImage } = useImageLoader()
  const { preloadImages } = useImagePreloader({ preloadImage })

  const handleImageClick = useCallback((index: number) => {
    setCurrentIndex(index)
    setModalOpen(true)
  }, [])

  const handleCloseModal = useCallback(() => {
    setModalOpen(false)
  }, [])

  const handleIndexChange = useCallback((index: number) => {
    setCurrentIndex(index)
  }, [])

  const handleScroll = useCallback(({ scrollTop }: { scrollTop: number }) => {
    if (cleanupTimeoutRef.current) {
      clearTimeout(cleanupTimeoutRef.current)
    }

    const scrollDirection = scrollTop > lastScrollPosRef.current ? 'down' : 'up'
    lastScrollPosRef.current = scrollTop

    cleanupTimeoutRef.current = setTimeout(() => {
      const { columnCount, itemSize } = gridDataRef.current
      const visibleStartIndex = Math.floor(scrollTop / itemSize) * columnCount
      preloadImages(images, visibleStartIndex, scrollDirection)
    }, 100)
  }, [images, preloadImages])

  useEffect(() => {
    return () => {
      if (cleanupTimeoutRef.current) {
        clearTimeout(cleanupTimeoutRef.current)
      }
    }
  }, [])

  const calculateGrid = useCallback((width: number) => {
    // Calculate optimal column count based on minimum item size
    const optimalCols = Math.floor(width / minItemSize)
    
    // Responsive column calculation
    let columnCount: number
    if (width <= 600) {
      columnCount = minColumns
    } else if (width <= 1024) {
      columnCount = Math.min(Math.max(minColumns + 1, optimalCols), maxColumns - 1)
    } else {
      columnCount = Math.min(Math.max(minColumns + 2, optimalCols), maxColumns)
    }
    
    // Calculate item size based on column count and gap
    const totalGapWidth = (columnCount - 1) * gap
    const itemSize = Math.floor((width - totalGapWidth) / columnCount)
    
    // Calculate row count
    const rowCount = Math.ceil(images.length / columnCount)

    // Store current grid data for scroll handler
    gridDataRef.current = { columnCount, itemSize }
    
    return { columnCount, rowCount, itemSize }
  }, [images.length, minColumns, maxColumns, minItemSize, gap])

  const Cell = useCallback(({ columnIndex, rowIndex, style }: any) => {
    const { columnCount } = gridDataRef.current
    const index = rowIndex * columnCount + columnIndex
    const image = images[index]

    if (!image) return null

    return (
      <div style={{ ...style, padding: gap / 2 }}>
        <OptimizedImageCell
          image={image}
          index={index}
          loadedImages={loadedImages}
          failedImages={failedImages}
          loadImage={loadImage}
          updateImageStatus={updateImageStatus}
          onImageClick={handleImageClick}
          aspectRatio={aspectRatio}
          showOverlay={showOverlay}
        />
      </div>
    )
  }, [images, loadedImages, failedImages, loadImage, updateImageStatus, handleImageClick, aspectRatio, showOverlay, gap])

  // Non-virtualized grid for smaller datasets
  if (!virtualized || images.length < 50) {
    const gridClasses = {
      2: 'grid-cols-1 md:grid-cols-2',
      3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
      4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
      5: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5',
      6: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-6'
    }

    const columns = Math.min(maxColumns, 6) as keyof typeof gridClasses

    return (
      <>
        <motion.div 
          className={`grid ${gridClasses[columns]} gap-${gap / 4} ${className}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {images.map((image, index) => (
            <OptimizedImageCell
              key={`${image.src}-${index}`}
              image={image}
              index={index}
              loadedImages={loadedImages}
              failedImages={failedImages}
              loadImage={loadImage}
              updateImageStatus={updateImageStatus}
              onImageClick={handleImageClick}
              aspectRatio={aspectRatio}
              showOverlay={showOverlay}
            />
          ))}
        </motion.div>

        <ImageModal
          isOpen={modalOpen}
          onClose={handleCloseModal}
          images={images}
          currentIndex={currentIndex}
          onIndexChange={handleIndexChange}
        />
      </>
    )
  }

  // Virtualized grid for large datasets
  return (
    <>
      <div className={`${className}`} style={{ height }}>
        <AutoSizer>
          {({ height: autoHeight, width }) => {
            const { columnCount, rowCount, itemSize } = calculateGrid(width)
            
            return (
              <FixedSizeGrid
                columnCount={columnCount}
                columnWidth={itemSize}
                height={autoHeight}
                rowCount={rowCount}
                rowHeight={itemSize}
                width={width}
                onScroll={handleScroll}
                overscanRowCount={2}
                overscanColumnCount={1}
                className="gallery-grid"
              >
                {Cell}
              </FixedSizeGrid>
            )
          }}
        </AutoSizer>
      </div>

      <ImageModal
        isOpen={modalOpen}
        onClose={handleCloseModal}
        images={images}
        currentIndex={currentIndex}
        onIndexChange={handleIndexChange}
      />
    </>
  )
})

ImageGallery.displayName = 'ImageGallery'