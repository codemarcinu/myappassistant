'use client';
import { useRouter, usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Home, MessageCircle, ShoppingCart, ChefHat } from 'lucide-react';

const navigationItems = [
  { path: '/dashboard', icon: Home, label: 'Dashboard' },
  { path: '/chat', icon: MessageCircle, label: 'Czat' },
  { path: '/shopping', icon: ShoppingCart, label: 'Zakupy' },
  { path: '/cooking', icon: ChefHat, label: 'Gotowanie' },
];

export function BottomNavigation() {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="fixed bottom-0 left-0 z-50 w-full h-16 bg-background border-t">
      <div className="grid h-full max-w-lg grid-cols-4 mx-auto font-medium">
        {navigationItems.map(({ path, icon: Icon, label }) => {
          const isActive = pathname === path;

          return (
            <button
              key={path}
              onClick={() => router.push(path)}
              className={cn(
                "inline-flex flex-col items-center justify-center px-5 hover:bg-gray-50 dark:hover:bg-gray-800 group",
                isActive ? "text-primary" : "text-gray-500 dark:text-gray-400"
              )}
            >
              <Icon className="w-5 h-5 mb-2" />
              <span className="text-sm">{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
