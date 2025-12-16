import Link from "next/link";
import { AppNavigation } from "@/components/layout/AppNavigation";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white text-gray-900 flex flex-col">
      <AppNavigation />
      <main className="mx-auto w-full max-w-7xl px-4 sm:px-6 py-6 sm:py-10 lg:px-8 space-y-6 sm:space-y-10 flex-1">
        {children}
      </main>
      <footer className="bg-gray-50 border-t border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500">
            <p>&copy; {new Date().getFullYear()} Campaign Reference</p>
            <nav className="flex gap-6">
              <Link href="/terms" className="hover:text-gray-700 transition-colors">
                Terms of Service
              </Link>
              <Link href="/privacy" className="hover:text-gray-700 transition-colors">
                Privacy Policy
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
