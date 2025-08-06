import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { SidebarProvider } from '@/components/ui/sidebar';
import { Toaster } from 'sonner';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Commission Calculator Pro',
  description: 'Enterprise-grade commission management system with pay period automation',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SidebarProvider>
          <Providers>
            {children}
            <Toaster 
              position="top-right"
              expand={false}
              richColors
            />
          </Providers>
        </SidebarProvider>
      </body>
    </html>
  );
}