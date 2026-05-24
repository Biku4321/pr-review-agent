import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PR Review Agent",
  description: "AI-powered multi-agent code review",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#0a0e17] text-gray-100 font-sans antialiased min-h-screen">
        <nav className="border-b border-gray-900 bg-[#0d1117]/90 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-12 flex items-center gap-6">
            <a href="/dashboard" className="font-mono text-cyan-400 font-semibold tracking-tight hover:text-cyan-300 transition-colors">
              ⬡ pr-review-agent
            </a>
            <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-200 transition-colors font-mono">
              dashboard
            </a>
            <a href="/review" className="text-sm text-gray-600 hover:text-gray-200 transition-colors font-mono">
              new review
            </a>
            <a href="/analytics" className="text-sm text-gray-600 hover:text-gray-200 transition-colors font-mono">
              analytics
            </a>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
