import * as React from 'react';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import dynamic from 'next/dynamic';

const Providers = dynamic(() => import('@/components/Providers').then(mod => mod.Providers), { ssr: false });

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'FoodSave AI - Your Smart Kitchen Assistant',
  description: 'AI-powered kitchen assistant for meal planning, recipe management, and smart shopping',
  keywords: 'AI, kitchen, recipes, meal planning, food management',
  authors: [{ name: 'FoodSave AI Team' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
  openGraph: {
    title: 'FoodSave AI - Your Smart Kitchen Assistant',
    description: 'AI-powered kitchen assistant for meal planning, recipe management, and smart shopping',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'FoodSave AI - Your Smart Kitchen Assistant',
    description: 'AI-powered kitchen assistant for meal planning, recipe management, and smart shopping',
  },
};

import { SidebarNavigation } from '@/components/navigation/SidebarNavigation';
import { BottomNavigation } from '@/components/navigation/BottomNavigation';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Security Headers */}
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-Frame-Options" content="DENY" />
        <meta httpEquiv="X-XSS-Protection" content="1; mode=block" />
        <meta httpEquiv="Referrer-Policy" content="strict-origin-when-cross-origin" />

        {/* Performance optimizations */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={inter.className}>
        <Providers>
          <div className="flex">
            {/* Desktop Sidebar */}
            <div className="hidden md:block">
              <SidebarNavigation />
            </div>

            {/* Main Content */}
            <main className="flex-1">
              <div className="p-4">
                {children}
              </div>
            </main>
          </div>

          {/* Mobile Bottom Navigation */}
          <div className="md:hidden">
            <BottomNavigation />
          </div>
        </Providers>
      </body>
    </html>
  );
}
