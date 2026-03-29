import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OmniSales — The Autonomous Revenue Department',
  description: 'AI-powered multi-agent sales platform with real-time deal management, churn prevention, and competitive intelligence.',
  keywords: 'AI sales, autonomous agents, revenue operations, LangGraph, MCP, A2A',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
