import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service - PixCrawler',
  description: 'PixCrawler Terms of Service. Read our terms and conditions for using our image dataset building platform.',
  keywords: ['terms of service', 'terms and conditions', 'legal', 'agreement'],
}

export default function TermsPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="container mx-auto px-4 lg:px-8 max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Terms of Service
          </h1>
          <p className="text-muted-foreground">
            Last updated: January 1, 2025
          </p>
        </div>

        <div className="prose prose-lg max-w-none">
          <div className="space-y-8">
            <section>
              <h2 className="text-2xl font-bold mb-4">1. Acceptance of Terms</h2>
              <p className="text-muted-foreground leading-relaxed">
                By accessing or using PixCrawler&apos;s services, you agree to be bound by these Terms of Service (&quot;Terms&quot;). If you do not agree to these Terms, please do not use our services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">2. Description of Service</h2>
              <p className="text-muted-foreground leading-relaxed">
                PixCrawler provides an AI-powered platform for building image datasets for machine learning and computer vision applications. Our services include image collection, validation, organization, and export capabilities.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">3. User Accounts</h2>
              
              <h3 className="text-xl font-semibold mb-3">3.1 Account Creation</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                You must create an account to use our services. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.
              </p>

              <h3 className="text-xl font-semibold mb-3">3.2 Account Requirements</h3>
              <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                <li>You must be at least 18 years old</li>
                <li>You must provide accurate and complete information</li>
                <li>You must not share your account with others</li>
                <li>You must notify us immediately of any unauthorized use</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">4. Acceptable Use</h2>
              
              <h3 className="text-xl font-semibold mb-3">4.1 Permitted Uses</h3>
              <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                <li>Creating datasets for legitimate research and development</li>
                <li>Building training data for machine learning models</li>
                <li>Commercial use in accordance with your subscription plan</li>
                <li>Educational and academic purposes</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6">4.2 Prohibited Uses</h3>
              <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                <li>Collecting images for illegal or harmful purposes</li>
                <li>Violating copyright, trademark, or other intellectual property rights</li>
                <li>Creating datasets containing personal information without consent</li>
                <li>Attempting to reverse engineer or compromise our systems</li>
                <li>Sharing or reselling access to our services</li>
                <li>Using our services to compete directly with PixCrawler</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">5. Subscription Plans and Billing</h2>
              
              <h3 className="text-xl font-semibold mb-3">5.1 Subscription Terms</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                Our services are offered under various subscription plans. By subscribing, you agree to pay the applicable fees and charges.
              </p>

              <h3 className="text-xl font-semibold mb-3">5.2 Billing and Payment</h3>
              <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
                <li>Subscription fees are billed in advance on a monthly or annual basis</li>
                <li>All fees are non-refundable except as required by law</li>
                <li>We may change our pricing with 30 days&apos; notice</li>
                <li>Failure to pay may result in service suspension or termination</li>
              </ul>

              <h3 className="text-xl font-semibold mb-3 mt-6">5.3 Usage Limits</h3>
              <p className="text-muted-foreground leading-relaxed">
                Each subscription plan includes specific usage limits. Exceeding these limits may result in additional charges or service restrictions.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">6. Intellectual Property</h2>
              
              <h3 className="text-xl font-semibold mb-3">6.1 Our Rights</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                PixCrawler retains all rights, title, and interest in our platform, technology, and services. You may not copy, modify, or distribute our software or content.
              </p>

              <h3 className="text-xl font-semibold mb-3">6.2 Your Content</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                You retain ownership of datasets you create using our services. However, you grant us a license to process and store your data as necessary to provide our services.
              </p>

              <h3 className="text-xl font-semibold mb-3">6.3 Third-Party Content</h3>
              <p className="text-muted-foreground leading-relaxed">
                You are responsible for ensuring you have the right to use any images collected through our platform. We do not grant rights to third-party content.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">7. Privacy and Data Protection</h2>
              <p className="text-muted-foreground leading-relaxed">
                Your privacy is important to us. Please review our Privacy Policy to understand how we collect, use, and protect your information.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">8. Service Availability</h2>
              <p className="text-muted-foreground leading-relaxed">
                We strive to maintain high service availability but do not guarantee uninterrupted access. We may perform maintenance, updates, or modifications that temporarily affect service availability.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">9. Limitation of Liability</h2>
              <p className="text-muted-foreground leading-relaxed">
                To the maximum extent permitted by law, PixCrawler shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including but not limited to loss of profits, data, or business opportunities.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">10. Indemnification</h2>
              <p className="text-muted-foreground leading-relaxed">
                You agree to indemnify and hold PixCrawler harmless from any claims, damages, or expenses arising from your use of our services or violation of these Terms.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">11. Termination</h2>
              
              <h3 className="text-xl font-semibold mb-3">11.1 Termination by You</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                You may terminate your account at any time by contacting our support team or using the account deletion feature.
              </p>

              <h3 className="text-xl font-semibold mb-3">11.2 Termination by Us</h3>
              <p className="text-muted-foreground leading-relaxed mb-4">
                We may suspend or terminate your account for violation of these Terms, non-payment, or other reasons at our discretion.
              </p>

              <h3 className="text-xl font-semibold mb-3">11.3 Effect of Termination</h3>
              <p className="text-muted-foreground leading-relaxed">
                Upon termination, your access to our services will cease, and we may delete your data after a reasonable period.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">12. Governing Law</h2>
              <p className="text-muted-foreground leading-relaxed">
                These Terms are governed by the laws of the State of California, United States, without regard to conflict of law principles.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">13. Changes to Terms</h2>
              <p className="text-muted-foreground leading-relaxed">
                We may modify these Terms at any time. We will notify you of material changes by email or through our platform. Continued use of our services constitutes acceptance of the modified Terms.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4">14. Contact Information</h2>
              <p className="text-muted-foreground leading-relaxed">
                If you have questions about these Terms, please contact us:
              </p>
              <div className="mt-4 p-4 bg-muted/30 rounded-lg">
                <p className="text-muted-foreground">
                  <strong>Email:</strong> legal@pixcrawler.com<br />
                  <strong>Address:</strong> PixCrawler Inc., 123 Tech Street, San Francisco, CA 94105<br />
                  <strong>Phone:</strong> +1 (555) 123-4567
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  )
}