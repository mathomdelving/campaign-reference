'use client';

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthButton } from "@/components/auth/AuthButton";

const NAV_ITEMS = [
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/district", label: "By District" },
  { href: "/committee", label: "By Committee" },
];

export function AppNavigation() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="bg-rb-brand-navy text-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 py-4 lg:px-8">
        <Link href="/leaderboard" aria-label="Campaign Reference home">
          <div className="font-display text-[20px] sm:text-[26px] font-semibold uppercase leading-tight tracking-[0.2rem] sm:tracking-[0.35rem] text-rb-gold" style={{ color: '#FFC906' }}>
            <span className="block">Campaign</span>
            <span className="block">Reference</span>
          </div>
        </Link>

        <div className="flex items-center gap-4 sm:gap-6">
          {/* Desktop navigation - hidden on mobile */}
          <nav className="hidden md:flex items-center gap-4">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/leaderboard"
                  ? pathname === "/" || pathname.startsWith(item.href)
                  : pathname.startsWith(item.href);

              const baseClasses =
                "px-4 py-2 text-sm font-medium uppercase tracking-[0.2rem] transition-colors duration-200";
              const stateClasses = isActive
                ? "text-rb-gold"
                : "text-rb-grey hover:text-white";

              return (
                <Link key={item.href} href={item.href} className={`${baseClasses} ${stateClasses}`}>
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Mobile hamburger button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-white hover:text-rb-gold transition-colors"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>

          <AuthButton />
        </div>
      </div>

      {/* Mobile menu overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile menu panel */}
      <div
        className={`fixed top-0 right-0 bottom-0 w-64 bg-rb-brand-navy z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          mobileMenuOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex flex-col p-6 space-y-6">
          <div className="flex justify-end">
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-2 text-white hover:text-rb-gold transition-colors"
              aria-label="Close menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <nav className="flex flex-col space-y-4">
            {NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/leaderboard"
                  ? pathname === "/" || pathname.startsWith(item.href)
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`px-4 py-3 text-base font-medium uppercase tracking-[0.15rem] transition-colors ${
                    isActive
                      ? "text-rb-gold bg-rb-blue/30"
                      : "text-rb-grey hover:text-white hover:bg-rb-blue/20"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
