'use client'

import {memo, useState} from 'react'
import {Button} from '@/components/ui/button'
import {Send} from 'lucide-react'
import {FormField} from './FormField'
import {FormSelect} from './FormSelect'
import {FormTextarea} from './FormTextarea'
import {ContactInfo} from './ContactInfo'

const SUBJECT_OPTIONS = [
  {value: 'general', label: 'General Inquiry'},
  {value: 'support', label: 'Technical Support'},
  {value: 'billing', label: 'Billing Question'},
  {value: 'enterprise', label: 'Enterprise Sales'},
  {value: 'partnership', label: 'Partnership'},
  {value: 'feedback', label: 'Feedback'}
]

export const ContactForm = memo(() => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    subject: '',
    message: ''
  })

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<{
    type: 'success' | 'error' | null
    message: string
  }>({type: null, message: ''})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setSubmitStatus({type: null, message: ''})

    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setSubmitStatus({
          type: 'success',
          message: 'Thank you! Your message has been sent successfully. We\'ll get back to you soon.',
        })
        // Reset form
        setFormData({
          name: '',
          email: '',
          company: '',
          subject: '',
          message: '',
        })
      } else {
        setSubmitStatus({
          type: 'error',
          message: data.error || 'Failed to send message. Please try again.',
        })
      }
    } catch (error) {
      setSubmitStatus({
        type: 'error',
        message: 'An error occurred. Please try again later.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <section className="py-16">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact Form */}
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-6">
                Send us a message
              </h2>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid md:grid-cols-2 gap-4">
                  <FormField
                    id="name"
                    name="name"
                    label="Full Name"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Enter your full name"
                  />
                  <FormField
                    id="email"
                    name="email"
                    label="Email Address"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="Enter your email"
                  />
                </div>

                <FormField
                  id="company"
                  name="company"
                  label="Company (Optional)"
                  value={formData.company}
                  onChange={handleChange}
                  placeholder="Enter your company name"
                />

                <FormSelect
                  id="subject"
                  name="subject"
                  label="Subject"
                  required
                  value={formData.subject}
                  onChange={handleChange}
                  options={SUBJECT_OPTIONS}
                  placeholder="Select a subject"
                />

                <FormTextarea
                  id="message"
                  name="message"
                  label="Message"
                  required
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Tell us how we can help you..."
                />

                {submitStatus.type && (
                  <div
                    className={`p-4 rounded-lg ${
                      submitStatus.type === 'success'
                        ? 'bg-green-50 text-green-800 border border-green-200'
                        : 'bg-red-50 text-red-800 border border-red-200'
                    }`}
                  >
                    {submitStatus.message}
                  </div>
                )}

                <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
                  <Send className="w-4 h-4 mr-2"/>
                  {isSubmitting ? 'Sending...' : 'Send Message'}
                </Button>
              </form>
            </div>

            <ContactInfo />
          </div>
        </div>
      </div>
    </section>
  )
})

ContactForm.displayName = 'ContactForm'
