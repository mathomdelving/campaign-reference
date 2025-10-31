'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthButton } from "@/components/auth/AuthButton";

const NAV_ITEMS = [
  { href: "/leaderboard", label: "Leaderboard" },
  { href: "/district", label: "By District" },
  { href: "/committee", label: "By Committee" },
  { href: "/share/party-receipts-2026", label: "Share Routes" },
];

export function AppNavigation() {
  const pathname = usePathname();

  return (
    <header className="bg-rb-brand-navy text-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
        <Link href="/leaderboard" aria-label="Campaign Reference home">
          <div className="font-display text-[26px] font-semibold uppercase leading-tight tracking-[0.35rem] text-rb-gold" style={{ color: '#FFC906' }}>
            <span className="block">Campaign</span>
            <span className="block">Reference</span>
          </div>
        </Link>

        <div className="flex items-center gap-6">
          <nav className="flex items-center gap-4">
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
          <AuthButton />
        </div>
      </div>
    </header>
  );
}
