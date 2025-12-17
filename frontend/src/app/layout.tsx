import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Money Flow",
  description: "Track all your recurring payments - subscriptions, utilities, debts, savings, and more with AI-powered natural language commands",
  icons: {
    icon: "/favicon.svg",
  },
};

// Script to run before React hydrates to prevent flash of wrong theme
const themeScript = `
  (function() {
    const STORAGE_KEY = 'money-flow-theme';
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="font-sans antialiased">
        {/* Skip link for keyboard navigation */}
        <a
          href="#main-content"
          className="skip-link"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
        {/* Live region for screen reader announcements */}
        <div
          id="announcer"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        />
      </body>
    </html>
  );
}
