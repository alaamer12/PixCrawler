import {Metadata} from 'next'
import {LegalContact, LegalHeader, LegalList, LegalParagraph, LegalSection, LegalSubsection} from '@/components/legal'

export const metadata: Metadata = {
  title: 'Terms of Service - PixCrawler | DEPI Legal Agreement',
  description: 'PixCrawler Terms of Service. Read our terms and conditions for using our image dataset building platform developed under DEPI initiative.',
  keywords: ['terms of service', 'terms and conditions', 'legal', 'agreement', 'DEPI', 'user agreement', 'acceptable use'],
  openGraph: {
    title: 'Terms of Service - PixCrawler',
    description: 'Terms and conditions for using PixCrawler services.',
    type: 'website',
  },
  alternates: {
    canonical: 'https://pixcrawler.io/terms',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function TermsPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="container mx-auto px-4 lg:px-8 max-w-4xl">
        <LegalHeader title="Terms of Service" lastUpdated="January 24, 2025"/>

        <div className="prose prose-lg max-w-none">
          <div className="space-y-8">
            <LegalSection title="1. Acceptance of Terms">
              <LegalParagraph>
                By accessing or using PixCrawler&apos;s services, you agree to be bound by these Terms of Service
                (&quot;Terms&quot;). If you do not agree to these Terms, please do not use our services.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="2. Description of Service">
              <LegalParagraph>
                PixCrawler provides an AI-powered platform for building image datasets for machine learning and computer
                vision applications. Developed under the Digital Egypt Pioneers Initiative (DEPI), our services include
                image collection, validation, organization, and export capabilities. The platform is currently in active
                development and features may be updated or modified.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="3. User Accounts">
              <LegalSubsection title="3.1 Account Creation">
                <LegalParagraph>
                  You must create an account to use our services. You are responsible for maintaining the
                  confidentiality
                  of your account credentials and for all activities that occur under your account.
                </LegalParagraph>
              </LegalSubsection>

              <LegalSubsection title="3.2 Account Requirements">
                <LegalList items={[
                  'You must be at least 18 years old',
                  'You must provide accurate and complete information',
                  'You must not share your account with others',
                  'You must notify us immediately of any unauthorized use'
                ]}/>
              </LegalSubsection>
            </LegalSection>

            <LegalSection title="4. Acceptable Use">
              <LegalSubsection title="4.1 Permitted Uses">
                <LegalList items={[
                  'Creating datasets for legitimate research and development',
                  'Building training data for machine learning models',
                  'Commercial use in accordance with your subscription plan',
                  'Educational and academic purposes'
                ]}/>
              </LegalSubsection>

              <LegalSubsection title="4.2 Prohibited Uses">
                <LegalList items={[
                  'Collecting images for illegal or harmful purposes',
                  'Violating copyright, trademark, or other intellectual property rights',
                  'Creating datasets containing personal information without consent',
                  'Attempting to reverse engineer or compromise our systems',
                  'Sharing or reselling access to our services',
                  'Using our services to compete directly with PixCrawler'
                ]}/>
              </LegalSubsection>
            </LegalSection>

            <LegalSection title="5. Subscription Plans and Billing">
              <LegalSubsection title="5.1 Subscription Terms">
                <LegalParagraph>
                  Our services are offered under various subscription plans. By subscribing, you agree to pay the
                  applicable fees and charges.
                </LegalParagraph>
              </LegalSubsection>

              <LegalSubsection title="5.2 Billing and Payment">
                <LegalList items={[
                  'Subscription fees are billed in advance on a monthly or annual basis',
                  'All fees are non-refundable except as required by law',
                  'We may change our pricing with 30 days\' notice',
                  'Failure to pay may result in service suspension or termination'
                ]}/>
              </LegalSubsection>

              <LegalSubsection title="5.3 Usage Limits">
                <LegalParagraph>
                  Each subscription plan includes specific usage limits. Exceeding these limits may result in additional
                  charges or service restrictions.
                </LegalParagraph>
              </LegalSubsection>
            </LegalSection>

            <LegalSection title="6. Intellectual Property">
              <LegalSubsection title="6.1 Our Rights">
                <LegalParagraph>
                  PixCrawler retains all rights, title, and interest in our platform, technology, and services. You may
                  not copy, modify, or distribute our software or content.
                </LegalParagraph>
              </LegalSubsection>

              <LegalSubsection title="6.2 Your Content">
                <LegalParagraph>
                  You retain ownership of datasets you create using our services. However, you grant us a license to
                  process and store your data as necessary to provide our services.
                </LegalParagraph>
              </LegalSubsection>

              <LegalSubsection title="6.3 Third-Party Content">
                <LegalParagraph>
                  You are responsible for ensuring you have the right to use any images collected through our platform.
                  We
                  do not grant rights to third-party content.
                </LegalParagraph>
              </LegalSubsection>
            </LegalSection>

            <LegalSection title="7. Privacy and Data Protection">
              <LegalParagraph>
                Your privacy is important to us. Please review our Privacy Policy to understand how we collect, use, and
                protect your information.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="8. Service Availability">
              <LegalParagraph>
                We strive to maintain high service availability but do not guarantee uninterrupted access. We may
                perform maintenance, updates, or modifications that temporarily affect service availability.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="9. Limitation of Liability">
              <LegalParagraph>
                To the maximum extent permitted by law, PixCrawler shall not be liable for any indirect, incidental,
                special, consequential, or punitive damages, including but not limited to loss of profits, data, or
                business opportunities.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="10. Indemnification">
              <LegalParagraph>
                You agree to indemnify and hold PixCrawler harmless from any claims, damages, or expenses arising from
                your use of our services or violation of these Terms.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="11. Termination">
              <LegalSubsection title="11.1 Termination by You">
                <LegalParagraph>
                  You may terminate your account at any time by contacting our support team or using the account
                  deletion
                  feature.
                </LegalParagraph>
              </LegalSubsection>

              <LegalSubsection title="11.2 Termination by Us">
                <LegalParagraph>
                  We may suspend or terminate your account for violation of these Terms, non-payment, or other reasons
                  at
                  our discretion.
                </LegalParagraph>
              </LegalSubsection>

              <LegalSubsection title="11.3 Effect of Termination">
                <LegalParagraph>
                  Upon termination, your access to our services will cease, and we may delete your data after a
                  reasonable
                  period.
                </LegalParagraph>
              </LegalSubsection>
            </LegalSection>

            <LegalSection title="12. Governing Law">
              <LegalParagraph>
                These Terms shall be governed by and construed in accordance with applicable international data
                protection
                and technology laws. Any disputes arising from these Terms will be resolved through good faith
                negotiation
                or appropriate dispute resolution mechanisms.
              </LegalParagraph>
            </LegalSection>

            <LegalSection title="13. Changes to Terms">
              <LegalParagraph>
                We may modify these Terms at any time. We will notify you of material changes by email or through our
                platform. Continued use of our services constitutes acceptance of the modified Terms.
              </LegalParagraph>
            </LegalSection>

            <LegalContact
              title="14. Contact Information"
              description="If you have questions about these Terms, please contact us:"
              contacts={[
                {label: 'Email', value: 'contact@pixcrawler.io'},
                {label: 'Legal Inquiries', value: 'legal@pixcrawler.io'},
                {label: 'Project', value: 'Developed under DEPI (Digital Egypt Pioneers Initiative)'},
                {label: 'Support', value: 'Available via email during business hours'}
              ]}
            />
          </div>
        </div>
      </div>
    </main>
  )
}
