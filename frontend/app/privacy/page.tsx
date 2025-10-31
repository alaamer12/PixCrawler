import {Metadata} from 'next'
import {LegalContact, LegalHeader, LegalList, LegalParagraph, LegalSection, LegalSubsection} from '@/components/legal'

export const metadata: Metadata = {
  title: 'Privacy Policy - PixCrawler | DEPI Data Protection',
  description: 'PixCrawler Privacy Policy. Learn how we collect, use, and protect your personal information in compliance with international data protection standards.',
  keywords: ['privacy policy', 'data protection', 'personal data', 'privacy', 'DEPI', 'data security', 'GDPR compliance'],
  openGraph: {
    title: 'Privacy Policy - PixCrawler',
    description: 'Learn how we protect your data and privacy.',
    type: 'website',
  },
  alternates: {
    canonical: 'https://pixcrawler.io/privacy',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function PrivacyPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="container mx-auto px-4 lg:px-8 max-w-4xl">
        <LegalHeader title="Privacy Policy" lastUpdated="January 24, 2025"/>

        <div className="prose prose-lg max-w-none">
          <div className="space-y-8">
            <LegalSection title="1. Introduction">
              <LegalParagraph>
                PixCrawler (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is committed to protecting your privacy.
                This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use
                our image dataset building platform and related services. As a project developed under the Digital Egypt
                Pioneers Initiative (DEPI), we adhere to international data protection standards and best practices.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="2. Information We Collect">
              <LegalSubsection title="2.1 Personal Information">
                <LegalList items={[
                  'Account information (name, email address, password)',
                  'Billing information (payment details, billing address)',
                  'Profile information (company name, job title, preferences)',
                  'Communication data (support tickets, feedback)'
                ]}/>
              </LegalSubsection>

              <LegalSubsection title="2.2 Usage Information">
                <LegalList items={[
                  'Dataset creation and management activities',
                  'API usage and access patterns',
                  'Feature usage and performance metrics',
                  'Error logs and diagnostic information'
                ]}/>
              </LegalSubsection>

              <LegalSubsection title="2.3 Technical Information">
                <LegalList items={[
                  'IP address and location data',
                  'Browser type and version',
                  'Device information and operating system',
                  'Cookies and similar tracking technologies'
                ]}/>
              </LegalSubsection>
            </LegalSection>

            <LegalSection title="3. How We Use Your Information">
              <LegalList items={[
                'Provide and maintain our services',
                'Process payments and manage subscriptions',
                'Communicate with you about your account and services',
                'Improve our platform and develop new features',
                'Ensure security and prevent fraud',
                'Comply with legal obligations',
                'Send marketing communications (with your consent)'
              ]}/>
            </LegalSection>

            <LegalSection title="4. Information Sharing and Disclosure">
              <LegalParagraph className="mb-4">
                We do not sell, trade, or rent your personal information to third parties. We may share your information
                in the following circumstances:
              </LegalParagraph>
              <LegalList items={[
                'Service Providers: Third-party vendors who assist in providing our services',
                'Legal Requirements: When required by law or to protect our rights',
                'Business Transfers: In connection with mergers, acquisitions, or asset sales',
                'Consent: When you have given explicit consent'
              ]}/>
            </LegalSection>

            <LegalSection title="5. Data Security">
              <LegalParagraph>
                We implement industry-standard security measures to protect your information, including:
              </LegalParagraph>
              <div className="mt-4">
                <LegalList items={[
                  'AES-256 encryption for data at rest and in transit',
                  'Regular security audits and penetration testing',
                  'Access controls and authentication mechanisms',
                  'Secure data centers with physical security measures',
                  'Employee training on data protection practices'
                ]}/>
              </div>
            </LegalSection>

            <LegalSection title="6. Data Retention">
              <LegalParagraph>
                We retain your personal information for as long as necessary to provide our services and fulfill the
                purposes outlined in this policy. Account information is retained until you delete your account. Usage
                data may be retained for up to 2 years for analytics and improvement purposes.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="7. Your Rights">
              <LegalParagraph className="mb-4">
                Depending on your location, you may have the following rights regarding your personal information:
              </LegalParagraph>
              <LegalList items={[
                'Access and receive a copy of your personal data',
                'Rectify inaccurate or incomplete information',
                'Delete your personal information',
                'Restrict or object to processing',
                'Data portability',
                'Withdraw consent at any time'
              ]}/>
            </LegalSection>

            <LegalSection title="8. Cookies and Tracking">
              <LegalParagraph>
                We use cookies and similar technologies to enhance your experience, analyze usage patterns, and provide
                personalized content. You can control cookie settings through your browser preferences.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="9. International Data Transfers">
              <LegalParagraph>
                Your information may be transferred to and processed in countries other than your own. We ensure
                appropriate safeguards are in place to protect your data in accordance with applicable data protection
                laws.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="10. Children's Privacy">
              <LegalParagraph>
                Our services are not intended for children under 13 years of age. We do not knowingly collect personal
                information from children under 13.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="11. Changes to This Policy">
              <LegalParagraph>
                We may update this Privacy Policy from time to time. We will notify you of any material changes by
                posting the new policy on this page and updating the &quot;Last updated&quot; date.
              </LegalParagraph>
            </LegalSection>

            <LegalContact
              title="12. Contact Us"
              description="If you have any questions about this Privacy Policy or our data practices, please contact us:"
              contacts={[
                {label: 'Email', value: 'contact@pixcrawler.io'},
                {label: 'Privacy Inquiries', value: 'privacy@pixcrawler.io'},
                {label: 'Project', value: 'Developed under DEPI (Digital Egypt Pioneers Initiative)'}
              ]}
            />
          </div>
        </div>
      </div>
    </main>
  )
}
