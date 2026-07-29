import type { Metadata } from "next";

// Self-hosted Inter (via @fontsource) instead of next/font/google:
// this app must work fully offline, so nothing about it -- including
// its typography -- can depend on a network fetch to Google's font
// CDN, at build time or runtime.
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";

import "./globals.css";

export const metadata: Metadata = {
  title: "Wedding Photo Organizer",
  description: "Find and export every photo of the people who matter, offline.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
