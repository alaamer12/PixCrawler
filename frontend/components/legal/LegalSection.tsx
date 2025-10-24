import {memo, ReactNode} from 'react'

interface LegalSectionProps {
  title: string
  children: ReactNode
  id?: string
}

export const LegalSection = memo(({title, children, id}: LegalSectionProps) => {
  return (
    <section id={id}>
      <h2 className="text-2xl font-bold mb-4">{title}</h2>
      {children}
    </section>
  )
})

LegalSection.displayName = 'LegalSection'

interface LegalSubsectionProps {
  title: string
  children: ReactNode
}

export const LegalSubsection = memo(({title, children}: LegalSubsectionProps) => {
  return (
    <div className="mt-6">
      <h3 className="text-xl font-semibold mb-3">{title}</h3>
      {children}
    </div>
  )
})

LegalSubsection.displayName = 'LegalSubsection'

interface LegalListProps {
  items: string[]
}

export const LegalList = memo(({items}: LegalListProps) => {
  return (
    <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
      {items.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  )
})

LegalList.displayName = 'LegalList'

interface LegalParagraphProps {
  children: ReactNode
  className?: string
}

export const LegalParagraph = memo(({children, className = ''}: LegalParagraphProps) => {
  return (
    <p className={`text-muted-foreground leading-relaxed ${className}`}>
      {children}
    </p>
  )
})

LegalParagraph.displayName = 'LegalParagraph'
