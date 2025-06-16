import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin', 'latin-ext'] });

export const metadata: Metadata = {
  title: 'FoodSave AI',
  description: 'Twój osobisty asystent do zarządzania zakupami i gotowaniem',
};

import { MainLayout } from '@/components/layout/MainLayout';

export default function RootLayout({
  children,
}: {
  children: any;
}) {
  return (
    <html lang="pl">
      <body className={inter.className}>
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
}
