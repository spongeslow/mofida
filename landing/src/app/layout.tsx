import type { Metadata, Viewport } from "next";
import { Playfair_Display, Plus_Jakarta_Sans, Press_Start_2P } from "next/font/google";
import "./globals.css";
import { Analytics } from "@/components/Analytics";
import { Guide } from "@/components/Guide";
import { ScrollProgress } from "@/components/ScrollProgress";

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "600", "700", "900"],
  variable: "--font-playfair",
  display: "swap",
});
const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-jakarta",
  display: "swap",
});
const pixel = Press_Start_2P({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-pixel",
  display: "swap",
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://moufida.ai";
const TITLE = "Moufida — Your 24/7 AI Co-Founder";
const DESCRIPTION =
  "Moufida diagnoses, scores and roadmaps your startup across 10 expert axes — and runs a full AI due-diligence report (market, product, legal, financial, competitors). 100% local. Your data never leaves your machine.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: DESCRIPTION,
  applicationName: "Moufida",
  keywords: [
    "AI co-founder",
    "startup due diligence",
    "AI startup advisor",
    "competitor analysis AI",
    "startup roadmap",
    "business model canvas AI",
    "founder tools",
    "local-first AI",
  ],
  authors: [{ name: "Team Makrouna Kadheba" }],
  alternates: { canonical: SITE_URL },
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: "Moufida",
    title: TITLE,
    description: DESCRIPTION,
    // OG image is generated dynamically by src/app/opengraph-image.tsx
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
  icons: { icon: "/favicon.svg" },
};

export const viewport: Viewport = {
  themeColor: "#F5EBDD",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${playfair.variable} ${jakarta.variable} ${pixel.variable}`}>
      <body>
        <ScrollProgress />
        {children}
        <Guide />
        <Analytics />
      </body>
    </html>
  );
}
