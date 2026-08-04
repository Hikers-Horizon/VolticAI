import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopNav } from '@/components/layout/TopNav';

export const metadata: Metadata = {
  title: 'TradeAI — Premium Intraday Trading',
  description: 'AI-powered intraday trading platform for Indian markets',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg text-white antialiased">
        <Sidebar />
        <div className="ml-[220px] min-h-screen flex flex-col">
          <TopNav />
          <main className="flex-1 p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
