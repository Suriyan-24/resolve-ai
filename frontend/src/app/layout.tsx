import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'ResolveAI — Dispute Risk Management',
  description: 'AI Risk Manager platform for automated chargeback defense and dispute triage',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
