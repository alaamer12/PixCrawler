'use client'

import React, {memo} from 'react'
import Image from 'next/image'
import {cn} from '@/lib/utils'

export interface LogoProps {
  showIcon?: boolean
  showText?: boolean
  className?: string
  size?: 'sm' | 'md' | 'lg'
  priority?: boolean
  stacked?: boolean
  ariaLabel?: string
}

const sizeMap: Record<NonNullable<LogoProps['size']>, {icon: number; text: string}> = {
  sm: {icon: 24, text: 'text-base'},
  md: {icon: 32, text: 'text-xl'},
  lg: {icon: 40, text: 'text-2xl'},
}

export const Logo = memo(function Logo({
  showIcon = true,
  showText = true,
  className,
  size = 'md',
  priority = false,
  stacked = false,
  ariaLabel = 'PixCrawler logo'
}: LogoProps) {
  const s = sizeMap[size]
  return (
    <span className={cn('inline-flex items-center gap-2', stacked && 'flex-col gap-1', className)} aria-label={ariaLabel}>
      {showIcon && (
        <Image
          src={'/logo.png'}
          alt={'PixCrawler logo icon'}
          width={s.icon}
          height={s.icon}
          priority={priority}
          sizes={size === 'lg' ? '(max-width: 768px) 32px, 40px' : '(max-width: 768px) 24px, 32px'}
        />
      )}
      {showText && (
        <span className={cn('font-bold leading-none', s.text)}>
          <span style={{color: '#7096b7'}}>Pix</span>
          <span style={{color: '#878A8C'}}>Crawler</span>
        </span>
      )}
    </span>
  )
})

Logo.displayName = 'Logo'

export default Logo

