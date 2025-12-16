export const metadata = {
  title: "Terms of Service | Campaign Reference",
  description: "Terms of Service for Campaign Reference",
};

export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Terms of Service</h1>

      <p className="text-sm text-gray-500 mb-8">Last updated: December 16, 2024</p>

      <div className="prose prose-gray max-w-none space-y-6">
        <section>
          <h2 className="text-xl font-semibold mb-3">1. Acceptance of Terms</h2>
          <p className="text-gray-700 leading-relaxed">
            By accessing and using Campaign Reference (&quot;the Service&quot;), you agree to be bound
            by these Terms of Service. If you do not agree to these terms, please do not use the Service.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">2. Description of Service</h2>
          <p className="text-gray-700 leading-relaxed">
            Campaign Reference is a campaign finance data visualization platform that displays
            publicly available data from the Federal Election Commission (FEC). The Service allows
            users to browse, search, and track campaign finance information for federal candidates
            and committees.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">3. User Accounts</h2>
          <p className="text-gray-700 leading-relaxed">
            To access certain features of the Service, you may need to create an account using
            Google authentication. You are responsible for:
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
            <li>Maintaining the security of your account credentials</li>
            <li>All activities that occur under your account</li>
            <li>Notifying us immediately of any unauthorized use of your account</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">4. Acceptable Use</h2>
          <p className="text-gray-700 leading-relaxed">You agree not to:</p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
            <li>Use the Service for any unlawful purpose</li>
            <li>Attempt to gain unauthorized access to any part of the Service</li>
            <li>Interfere with or disrupt the Service or servers</li>
            <li>Use automated systems to access the Service in a manner that exceeds reasonable use</li>
            <li>Misrepresent your identity or affiliation</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">5. Data and Content</h2>
          <p className="text-gray-700 leading-relaxed">
            The campaign finance data displayed on Campaign Reference is sourced from the
            Federal Election Commission and is in the public domain. We strive to keep this
            data accurate and up-to-date, but we do not guarantee its completeness or accuracy.
          </p>
          <p className="text-gray-700 leading-relaxed mt-2">
            The Service is provided for informational purposes only. Users should verify
            information with official FEC sources before relying on it for any official purpose.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">6. Intellectual Property</h2>
          <p className="text-gray-700 leading-relaxed">
            The Service&apos;s design, features, and original content (excluding public FEC data)
            are owned by Campaign Reference and protected by applicable intellectual property laws.
            You may not copy, modify, or distribute our proprietary content without permission.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">7. Disclaimer of Warranties</h2>
          <p className="text-gray-700 leading-relaxed">
            THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES
            OF ANY KIND, EITHER EXPRESS OR IMPLIED. WE DO NOT WARRANT THAT THE SERVICE WILL BE
            UNINTERRUPTED, ERROR-FREE, OR FREE OF HARMFUL COMPONENTS.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">8. Limitation of Liability</h2>
          <p className="text-gray-700 leading-relaxed">
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, CAMPAIGN REFERENCE SHALL NOT BE LIABLE FOR
            ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM
            YOUR USE OF THE SERVICE.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">9. Modifications to Service</h2>
          <p className="text-gray-700 leading-relaxed">
            We reserve the right to modify, suspend, or discontinue the Service at any time
            without notice. We may also update these Terms of Service from time to time.
            Continued use of the Service after changes constitutes acceptance of the new terms.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">10. Termination</h2>
          <p className="text-gray-700 leading-relaxed">
            We may terminate or suspend your account and access to the Service at our sole
            discretion, without notice, for conduct that we believe violates these Terms
            or is harmful to other users, us, or third parties.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">11. Governing Law</h2>
          <p className="text-gray-700 leading-relaxed">
            These Terms shall be governed by and construed in accordance with the laws of
            the United States, without regard to conflict of law principles.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">12. Contact</h2>
          <p className="text-gray-700 leading-relaxed">
            If you have questions about these Terms of Service, please contact us at:
          </p>
          <p className="text-gray-700 mt-2">
            <strong>Email:</strong> admin@campaign-reference.com
          </p>
        </section>
      </div>
    </div>
  );
}
