import React from 'react';
import { Sidebar } from './Sidebar';

interface MainLayoutProps {
  children: any;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen flex bg-gray-100">
      <Sidebar />
      <main className="flex-grow p-6 overflow-auto">
        {children}
      </main>
    </div>
  );
}
