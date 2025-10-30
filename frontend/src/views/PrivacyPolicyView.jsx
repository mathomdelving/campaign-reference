export default function PrivacyPolicyView() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-sm p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
        <p className="text-sm text-gray-600 mb-8">Last updated: October 30, 2025</p>

        <div className="space-y-6 text-gray-700">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Introduction</h2>
            <p>
              Welcome to Campaign Reference ("we," "our," or "us"). We are committed to protecting your personal
              information and your right to privacy. This Privacy Policy explains how we collect, use, and share
              information when you use our website at campaign-reference.com (the "Service").
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Information We Collect</h2>
            <h3 className="text-lg font-medium text-gray-800 mb-2">2.1 Information You Provide</h3>
            <ul className="list-disc pl-6 space-y-2 mb-4">
              <li><strong>Account Information:</strong> When you create an account, we collect your email address and password (encrypted).</li>
              <li><strong>OAuth Information:</strong> If you sign in with Google, we collect your name, email address, and profile picture from your Google account.</li>
              <li><strong>Preferences:</strong> We store your candidate watch list and email notification preferences.</li>
            </ul>

            <h3 className="text-lg font-medium text-gray-800 mb-2">2.2 Automatically Collected Information</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Usage Data:</strong> We collect information about how you interact with our Service, including pages viewed and features used.</li>
              <li><strong>Device Information:</strong> We collect information about the device you use to access our Service, including browser type and IP address.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">3. How We Use Your Information</h2>
            <p className="mb-2">We use the information we collect to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide, maintain, and improve our Service</li>
              <li>Create and manage your account</li>
              <li>Send you email notifications about campaign finance filings for candidates you follow</li>
              <li>Respond to your comments, questions, and requests</li>
              <li>Monitor and analyze usage patterns to improve user experience</li>
              <li>Detect, prevent, and address technical issues or fraudulent activity</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">4. How We Share Your Information</h2>
            <p className="mb-2">We do not sell your personal information. We may share your information in the following circumstances:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Service Providers:</strong> We use third-party services including Supabase (database and authentication), SendGrid (email delivery), and Google OAuth (authentication).</li>
              <li><strong>Legal Requirements:</strong> We may disclose your information if required by law or in response to valid legal requests.</li>
              <li><strong>Business Transfers:</strong> If we are involved in a merger, acquisition, or sale of assets, your information may be transferred.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Third-Party Services</h2>
            <p className="mb-2">Our Service uses the following third-party services:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Google OAuth:</strong> For authentication. See <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" className="text-rb-blue hover:underline">Google's Privacy Policy</a></li>
              <li><strong>Supabase:</strong> For database and authentication services. See <a href="https://supabase.com/privacy" target="_blank" rel="noopener noreferrer" className="text-rb-blue hover:underline">Supabase's Privacy Policy</a></li>
              <li><strong>SendGrid:</strong> For sending email notifications. See <a href="https://www.twilio.com/legal/privacy" target="_blank" rel="noopener noreferrer" className="text-rb-blue hover:underline">SendGrid's Privacy Policy</a></li>
              <li><strong>FEC OpenFEC API:</strong> For campaign finance data. See <a href="https://www.fec.gov/about/privacy-and-security-policy/" target="_blank" rel="noopener noreferrer" className="text-rb-blue hover:underline">FEC's Privacy Policy</a></li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Data Security</h2>
            <p>
              We implement appropriate technical and organizational security measures to protect your personal information.
              However, no method of transmission over the internet or electronic storage is 100% secure, and we cannot
              guarantee absolute security.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Your Rights and Choices</h2>
            <p className="mb-2">You have the following rights regarding your personal information:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Access and Update:</strong> You can access and update your account information through your account settings.</li>
              <li><strong>Email Preferences:</strong> You can manage your email notification preferences or unsubscribe from emails at any time.</li>
              <li><strong>Delete Account:</strong> You can request deletion of your account by contacting us at the email below.</li>
              <li><strong>Data Portability:</strong> You can request a copy of your personal data in a portable format.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Data Retention</h2>
            <p>
              We retain your personal information for as long as your account is active or as needed to provide you services.
              If you request deletion of your account, we will delete your personal information within 30 days, except where
              we are required to retain it for legal purposes.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">9. Children's Privacy</h2>
            <p>
              Our Service is not intended for children under 13 years of age. We do not knowingly collect personal
              information from children under 13. If you believe we have collected information from a child under 13,
              please contact us immediately.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">10. Changes to This Privacy Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new
              Privacy Policy on this page and updating the "Last updated" date. You are advised to review this Privacy
              Policy periodically for any changes.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">11. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy or our privacy practices, please contact us at:
            </p>
            <p className="mt-2">
              Email: <a href="mailto:admin@campaign-reference.com" className="text-rb-blue hover:underline">admin@campaign-reference.com</a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
