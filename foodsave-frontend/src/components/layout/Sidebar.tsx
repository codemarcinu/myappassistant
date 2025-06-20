'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { name: 'Panel', href: '/dashboard', icon: '🏠' },
  { name: 'Czat', href: '/chat', icon: '💬' },
  { name: 'Zakupy', href: '/shopping', icon: '🛒' },
  { name: 'Gotowanie', href: '/cooking', icon: '👨‍🍳' },
  { name: 'RAG System', href: '/rag', icon: '📚' },
  { name: 'Backup', href: '/backup', icon: '💾' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-800 text-white flex flex-col">
      <div className="h-16 flex items-center justify-center text-2xl font-bold border-b border-gray-700">
        FoodSave AI
      </div>
      <nav className="flex-grow p-4">
        <ul>
          {navItems.map((item) => (
            <li key={item.name} className="mb-2">
              <Link
                href={item.href}
                className={`flex items-center p-3 rounded-lg transition-colors ${
                  pathname === item.href
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <span className="mr-3 text-2xl">{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
