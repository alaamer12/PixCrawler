import {memo} from 'react'

interface ContactInfo {
  label: string
  value: string
}

interface LegalContactProps {
  title: string
  description: string
  contacts: ContactInfo[]
}

export const LegalContact = memo(({title, description, contacts}: LegalContactProps) => {
  return (
    <section>
      <h2 className="text-2xl font-bold mb-4">{title}</h2>
      <p className="text-muted-foreground leading-relaxed">
        {description}
      </p>
      <div className="mt-4 p-4 bg-muted/30 rounded-lg">
        <div className="text-muted-foreground space-y-1">
          {contacts.map((contact, index) => (
            <div key={index}>
              <strong>{contact.label}:</strong> {contact.value}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
})

LegalContact.displayName = 'LegalContact'
