import { AppNavigation } from "@/components/layout/AppNavigation";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      <AppNavigation />
      <main className="mx-auto w-full max-w-7xl px-4 sm:px-6 py-6 sm:py-10 lg:px-8 space-y-6 sm:space-y-10">
        {children}
      </main>
    </div>
  );
}
