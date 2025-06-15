import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin', 'latin-ext'] });

export const metadata: Metadata = {
  title: 'FoodSave AI',
  description: 'Twój osobisty asystent do zarządzania zakupami i gotowaniem',
};

export default function RootLayout({
  children,
}: {
  children: any;
}) {
  return (
    <html lang="pl">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          {children}
        </div>
      </body>
    </html>
  );
}
