import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "SHIELD",
  description: "Scam & Harmful Intent Email Logic Detector",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {/* Fixed HUD corner brackets — shared by every page. */}
        <div aria-hidden="true" className="pointer-events-none fixed inset-3 z-50 sm:inset-5">
          <span className="hud-corner absolute left-0 top-0 border-l border-t" />
          <span className="hud-corner absolute right-0 top-0 border-r border-t" />
          <span className="hud-corner absolute bottom-0 left-0 border-b border-l" />
          <span className="hud-corner absolute bottom-0 right-0 border-b border-r" />
        </div>
        {children}
      </body>
    </html>
  );
}
