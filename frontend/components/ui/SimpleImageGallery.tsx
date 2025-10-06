'use client'

import { memo, useState, useCallback } from 'react'
import { OptimizedNextImage } from './OptimizedNextImage'
import { SimpleImageModal } from './SimpleImageModal'

interface ImageData {
  src: string
  alt: string
  title?: string
}

interface SimpleImageGalleryProps {
  images: ImageData[]
  className?: string
  itemClassName?: string
  enableModal?: boolean
  onImageClick?: (index: number) => void
}

export const SimpleImageGallery = memo(({
  images,
  className = '',
  itemClassName = '',
  enableModal = true,
  onImageClick
}: SimpleImageGalleryProps) => {
  const [modalOpen, setModalOpen] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)

  const handleImageClick = useCallback((index: number) => {
    if (onImageClick) {
      onImageClick(index)
    } else if (enableModal) {
      setCurrentIndex(index)
      setModalOpen(true)
    }
  }, [enableModal, onImageClick])

  const handleCloseModal = useCallback(() => {
    setModalOpen(false)
  }, [])

  const handleIndexChange = useCallback((index: number) => {
    setCurrentIndex(index)
  }, [])

  return (
    <>
      <div className={className}>
        {images.map((image, index) => (
          <OptimizedNextImage
            key={`${image.src}-${index}`}
            src={image.src}
            alt={image.alt}
            className={itemClassName}
            onClick={() => handleImageClick(index)}
            priority={index < 6}
          />
        ))}
      </div>

      {enableModal && (
        <SimpleImageModal
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

SimpleImageGallery.displayName = 'SimpleImageGallery'