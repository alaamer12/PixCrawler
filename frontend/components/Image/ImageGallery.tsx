'use client'

import {memo, useCallback, useState} from 'react'
import {NextImage} from './NextImage'
import {ImageModal} from './ImageModal'

interface ImageData {
  src: string
  alt: string
  title?: string
}

interface ImageGalleryProps {
  images: ImageData[]
  className?: string
  itemClassName?: string
  enableModal?: boolean
  onImageClick?: (index: number) => void
}

export const ImageGallery = memo(({
                                    images,
                                    className = '',
                                    itemClassName = '',
                                    enableModal = true,
                                    onImageClick
                                  }: ImageGalleryProps) => {
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
          <NextImage
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

ImageGallery.displayName = 'ImageGallery'
