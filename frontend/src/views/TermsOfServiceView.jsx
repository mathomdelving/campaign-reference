export default function TermsOfServiceView() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-lg shadow-sm p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Terms of Service</h1>
        <p className="text-sm text-gray-600 mb-8">Last updated: October 30, 2025</p>

        <div className="space-y-6 text-gray-700">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Agreement to Terms</h2>
            <p>
              By accessing or using Campaign Reference ("Service"), you agree to be bound by these Terms of Service
              ("Terms"). If you disagree with any part of these terms, you may not access the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Description of Service</h2>
            <p>
              Campaign Reference is a web-based platform that provides visualization and analysis of campaign finance
              data for U.S. House and Senate races. The Service allows users to:
            </p>
            <ul className="list-disc pl-6 space-y-2 mt-2">
              <li>View campaign finance data from the Federal Election Commission (FEC)</li>
              <li>Track and compare candidates across races</li>
              <li>Follow specific candidates and receive email notifications about new campaign finance filings</li>
              <li>Export data for personal analysis</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">3. User Accounts</h2>
            <h3 className="text-lg font-medium text-gray-800 mb-2">3.1 Account Creation</h3>
            <p className="mb-4">
              To access certain features, you must create an account. You may register using email/password or through
              Google OAuth. You agree to provide accurate, current, and complete information during registration.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mb-2">3.2 Account Security</h3>
            <p className="mb-4">
              You are responsible for maintaining the confidentiality of your account credentials and for all activities
              that occur under your account. You agree to notify us immediately of any unauthorized access or use of your account.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mb-2">3.3 Account Termination</h3>
            <p>
              We reserve the right to suspend or terminate your account at any time for violation of these Terms or for
              any other reason. You may delete your account at any time by contacting us.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Acceptable Use</h2>
            <p className="mb-2">You agree not to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Use the Service for any illegal purpose or in violation of any local, state, national, or international law</li>
              <li>Violate or encourage others to violate the rights of third parties, including intellectual property rights</li>
              <li>Attempt to gain unauthorized access to the Service or its related systems or networks</li>
              <li>Use any automated system (bots, scrapers, etc.) to access the Service without our prior written permission</li>
              <li>Interfere with or disrupt the Service or servers or networks connected to the Service</li>
              <li>Transmit any viruses, malware, or other malicious code</li>
              <li>Impersonate any person or entity or misrepresent your affiliation with any person or entity</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Data and Content</h2>
            <h3 className="text-lg font-medium text-gray-800 mb-2">5.1 Campaign Finance Data</h3>
            <p className="mb-4">
              All campaign finance data displayed on the Service is sourced from the Federal Election Commission (FEC)
              OpenFEC API. We do not guarantee the accuracy, completeness, or timeliness of this data. The data is
              provided "as is" from the FEC.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mb-2">5.2 Data Accuracy Disclaimer</h3>
            <p className="mb-4">
              While we strive to provide accurate and up-to-date information, we make no warranties or representations
              about the accuracy, reliability, completeness, or timeliness of the campaign finance data. You should verify
              any critical information directly with the FEC at{' '}
              <a href="https://www.fec.gov" target="_blank" rel="noopener noreferrer" className="text-rb-blue hover:underline">
                www.fec.gov
              </a>.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mb-2">5.3 Intellectual Property</h3>
            <p>
              The Service and its original content (excluding public FEC data), features, and functionality are owned by
              Campaign Reference and are protected by international copyright, trademark, and other intellectual property laws.
              FEC data is in the public domain.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Email Notifications</h2>
            <p>
              If you choose to follow candidates, you will receive email notifications when new campaign finance filings
              are reported for those candidates. You can manage your notification preferences or unsubscribe from emails
              at any time through your account settings or via the unsubscribe link in any email.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Disclaimers and Limitations of Liability</h2>
            <h3 className="text-lg font-medium text-gray-800 mb-2">7.1 No Warranty</h3>
            <p className="mb-4">
              THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
              INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
              NON-INFRINGEMENT.
            </p>

            <h3 className="text-lg font-medium text-gray-800 mb-2">7.2 Limitation of Liability</h3>
            <p>
              TO THE FULLEST EXTENT PERMITTED BY LAW, CAMPAIGN REFERENCE SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL,
              SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY
              OR INDIRECTLY, OR ANY LOSS OF DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES RESULTING FROM YOUR USE OF
              THE SERVICE.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Political Neutrality</h2>
            <p>
              Campaign Reference is a non-partisan platform that provides campaign finance data for all candidates
              regardless of political affiliation. We do not endorse, support, or oppose any political candidate, party,
              or viewpoint. The inclusion of any candidate's data does not imply endorsement.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">9. Third-Party Links and Services</h2>
            <p>
              The Service may contain links to third-party websites or services (including the FEC website, Google OAuth,
              and others). We are not responsible for the content, privacy policies, or practices of any third-party
              websites or services.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">10. Changes to Terms</h2>
            <p>
              We reserve the right to modify these Terms at any time. We will notify users of any material changes by
              posting the new Terms on this page and updating the "Last updated" date. Your continued use of the Service
              after any changes constitutes acceptance of the new Terms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">11. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of the United States and the
              State of California, without regard to its conflict of law provisions.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">12. Contact Information</h2>
            <p>
              If you have any questions about these Terms, please contact us at:
            </p>
            <p className="mt-2">
              Email: <a href="mailto:admin@campaign-reference.com" className="text-rb-blue hover:underline">admin@campaign-reference.com</a>
            </p>
          </section>

          <section className="border-t pt-6 mt-8">
            <p className="text-sm text-gray-600">
              By using Campaign Reference, you acknowledge that you have read, understood, and agree to be bound by these
              Terms of Service and our{' '}
              <a href="/privacy" className="text-rb-blue hover:underline">Privacy Policy</a>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
