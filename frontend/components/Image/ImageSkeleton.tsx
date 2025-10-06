'use client'

import {memo} from 'react'

interface ImageSkeletonProps {
  className?: string
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape'
}

export const ImageSkeleton = memo(({
                                     className = '',
                                     aspectRatio = 'landscape'
                                   }: ImageSkeletonProps) => {
  const aspectClasses = {
    square: 'aspect-square',
    video: 'aspect-video',
    portrait: 'aspect-[3/4]',
    landscape: 'aspect-[4/3]'
  }

  return (
    <div className={`${aspectClasses[aspectRatio]} ${className}`}>
      <div className="w-full h-full bg-muted rounded-lg animate-pulse relative overflow-hidden">
        {/* Shimmer effect */}
        <div
          className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/20 to-transparent"/>

        {/* Placeholder icon */}
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
    </div>
  )
})

ImageSkeleton.displayName = 'ImageSkeleton'
