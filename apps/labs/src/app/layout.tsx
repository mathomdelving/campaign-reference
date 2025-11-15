import type { Metadata } from "next";
import { Inter, Libre_Baskerville } from "next/font/google";
import { AuthProvider } from "@/contexts/AuthContext";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const libreBaskerville = Libre_Baskerville({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "700"],
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Campaign Reference",
  description:
    "Campaign Reference visualization workspace for premium charts and export tooling.",
  openGraph: {
    title: "Campaign Reference",
    description:
      "Campaign finance dashboards for 2026 House and Senate races with watchlists and alerts.",
    url: "https://campaign-reference.com",
    siteName: "Campaign Reference",
    images: [
      {
        url: "/campaign-reference-thumbnail.png",
        width: 1200,
        height: 630,
        alt: "Campaign Reference thumbnail",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Campaign Reference",
    description:
      "Campaign finance dashboards for 2026 House and Senate races with watchlists and alerts.",
    images: ["/campaign-reference-thumbnail.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${libreBaskerville.variable} bg-rb-canvas text-rb-axis antialiased`}
      >
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
