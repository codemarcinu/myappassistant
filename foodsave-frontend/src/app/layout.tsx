import * as React from 'react';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin', 'latin-ext'] });

export const metadata: Metadata = {
  title: 'FoodSave AI',
  description: 'Twój osobisty asystent do zarządzania zakupami i gotowaniem',
};

import { SidebarNavigation } from '@/components/navigation/SidebarNavigation';
import { BottomNavigation } from '@/components/navigation/BottomNavigation';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <body className={inter.className}>
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
      </body>
    </html>
  );
}
