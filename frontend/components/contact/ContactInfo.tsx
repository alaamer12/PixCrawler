import {memo} from 'react'
import {Mail} from 'lucide-react'

export const ContactInfo = memo(() => {
  return (
    <div>
      <h2 className="text-2xl md:text-3xl font-bold mb-6">
        Contact Information
      </h2>

      <div className="bg-card border border-border rounded-lg p-6">
        <h3 className="font-semibold mb-2 flex items-center gap-2">
          <Mail className="w-5 h-5 text-primary"/>
          Email Support
        </h3>
        <p className="text-muted-foreground mb-4">
          Get help with technical issues, general inquiries, or discuss enterprise solutions.
        </p>
        <a
          href="mailto:contact@pixcrawler.io"
          className="text-primary hover:underline text-lg font-medium"
        >
          contact@pixcrawler.io
        </a>
        <p className="text-sm text-muted-foreground mt-4">
          We typically respond within 24 hours during business days.
        </p>
      </div>
    </div>
  )
})

ContactInfo.displayName = 'ContactInfo'
