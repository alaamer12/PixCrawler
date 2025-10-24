/**
 * PixCrawler - Top Loading Bar Provider
 * 
 * @description Progress bar provider using @bprogress/next for Next.js 15
 * @author PixCrawler Team - DEPI Initiative
 * @license MIT
 */

'use client'

import {ProgressProvider} from '@bprogress/next/app'
import {ReactNode} from 'react'

interface TopLoadingBarProps {
  children: ReactNode
}

export function TopLoadingBar({children}: TopLoadingBarProps) {
  return (
    <ProgressProvider
      height="3px"
      color="linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%)"
      options={{showSpinner: false}}
      shallowRouting
    >
      {children}
    </ProgressProvider>
  )
}
