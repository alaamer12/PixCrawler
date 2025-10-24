import {memo} from 'react'

interface LegalHeaderProps {
  title: string
  lastUpdated: string
}

export const LegalHeader = memo(({title, lastUpdated}: LegalHeaderProps) => {
  return (
    <div className="text-center mb-12">
      <h1 className="text-4xl md:text-5xl font-bold mb-4">
        {title}
      </h1>
      <p className="text-muted-foreground">
        Last updated: {lastUpdated}
      </p>
    </div>
  )
})

LegalHeader.displayName = 'LegalHeader'
