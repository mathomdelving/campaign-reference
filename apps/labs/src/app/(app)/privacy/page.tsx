export const metadata = {
  title: "Privacy Policy | Campaign Reference",
  description: "Privacy Policy for Campaign Reference",
};

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>

      <p className="text-sm text-gray-500 mb-8">Last updated: December 16, 2024</p>

      <div className="prose prose-gray max-w-none space-y-6">
        <section>
          <h2 className="text-xl font-semibold mb-3">Overview</h2>
          <p className="text-gray-700 leading-relaxed">
            Campaign Reference (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is committed to protecting your privacy.
            This Privacy Policy explains how we collect, use, and safeguard your information when you
            use our campaign finance data visualization service at campaign-reference.com.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Information We Collect</h2>

          <h3 className="text-lg font-medium mt-4 mb-2">Account Information</h3>
          <p className="text-gray-700 leading-relaxed">
            When you sign in using Google OAuth, we receive and store:
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
            <li>Your email address</li>
            <li>Your name (as provided by Google)</li>
            <li>Your Google profile identifier</li>
          </ul>

          <h3 className="text-lg font-medium mt-4 mb-2">Usage Data</h3>
          <p className="text-gray-700 leading-relaxed">
            We collect information about how you interact with our service, including:
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
            <li>Candidates and committees you choose to follow</li>
            <li>Your notification preferences</li>
            <li>General usage patterns to improve our service</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">How We Use Your Information</h2>
          <p className="text-gray-700 leading-relaxed">We use your information to:</p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
            <li>Provide and maintain your account</li>
            <li>Save your followed candidates and committees</li>
            <li>Send you notifications about FEC filings for candidates you follow (if enabled)</li>
            <li>Improve and optimize our service</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Data Sources</h2>
          <p className="text-gray-700 leading-relaxed">
            Campaign Reference displays publicly available campaign finance data from the
            Federal Election Commission (FEC). We do not collect or store any non-public
            campaign finance information.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Data Sharing</h2>
          <p className="text-gray-700 leading-relaxed">
            We do not sell, trade, or otherwise transfer your personal information to third parties.
            Your data is only shared with:
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
            <li><strong>Service Providers:</strong> We use Supabase for authentication and data storage,
            and Vercel for hosting. These providers have access to your data only to perform
            services on our behalf.</li>
            <li><strong>Legal Requirements:</strong> We may disclose your information if required by law.</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Data Security</h2>
          <p className="text-gray-700 leading-relaxed">
            We implement appropriate security measures to protect your personal information.
            Your data is stored securely using industry-standard encryption and access controls.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Your Rights</h2>
          <p className="text-gray-700 leading-relaxed">You have the right to:</p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1 mt-2">
            <li>Access the personal data we hold about you</li>
            <li>Request correction of inaccurate data</li>
            <li>Request deletion of your account and associated data</li>
            <li>Opt out of email notifications at any time</li>
          </ul>
          <p className="text-gray-700 leading-relaxed mt-2">
            To exercise these rights, please contact us at the email address below.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Cookies</h2>
          <p className="text-gray-700 leading-relaxed">
            We use essential cookies to maintain your authentication session. We do not use
            tracking cookies or third-party advertising cookies.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Changes to This Policy</h2>
          <p className="text-gray-700 leading-relaxed">
            We may update this Privacy Policy from time to time. We will notify you of any
            significant changes by posting the new policy on this page and updating the
            &quot;Last updated&quot; date.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3">Contact Us</h2>
          <p className="text-gray-700 leading-relaxed">
            If you have questions about this Privacy Policy or our data practices, please
            contact us at:
          </p>
          <p className="text-gray-700 mt-2">
            <strong>Email:</strong> admin@campaign-reference.com
          </p>
        </section>
      </div>
    </div>
  );
}
