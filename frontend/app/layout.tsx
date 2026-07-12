import type { Metadata } from "next";
import { Source_Serif_4, Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
});

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Ask My Docs",
  description: "Domain-specific document Q&A with enforced citations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sourceSerif.variable} ${inter.variable} ${ibmPlexMono.variable}`}>
      <body className="min-h-screen bg-paper font-sans text-ink antialiased">{children}</body>
    </html>
  );
}
