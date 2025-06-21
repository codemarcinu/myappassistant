'use client';
import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Home, MessageCircle, ShoppingCart, ChefHat, Menu, FileText } from 'lucide-react';

const navigationItems = [
  { path: '/dashboard', icon: Home, label: 'Dashboard' },
  { path: '/chat', icon: MessageCircle, label: 'Czat' },
  { path: '/shopping', icon: ShoppingCart, label: 'Zakupy' },
  { path: '/cooking', icon: ChefHat, label: 'Gotowanie' },
  { path: '/rag', icon: FileText, label: 'RAG' },
];

export function SidebarNavigation() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className={cn("relative h-screen bg-card border-r transition-all duration-300", isCollapsed ? "w-20" : "w-64")} data-testid="sidebar-navigation">
      <div className="flex items-center justify-between p-4 h-16 border-b">
        {!isCollapsed && (
          <h1 className="text-xl font-bold text-foreground">FoodSave AI</h1>
        )}
        <button onClick={() => setIsCollapsed(!isCollapsed)} className="p-2 rounded-full hover:bg-accent">
          <Menu className="text-foreground" />
        </button>
      </div>
      <nav className="mt-4 px-2">
        {navigationItems.map(({ path, icon: Icon, label }) => {
          const isActive = pathname === path;
          return (
            <a
              key={path}
              href={path}
              onClick={(e) => {
                e.preventDefault();
                router.push(path);
              }}
              className={cn(
                "flex items-center p-3 my-1 text-base font-medium rounded-full transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                isActive ? "bg-primary/10 text-primary" : "text-muted-foreground",
                isCollapsed ? "justify-center" : ""
              )}
            >
              <div className={cn(
                "flex items-center",
                isActive && !isCollapsed ? "bg-primary/20 rounded-full" : ""
              )}>
                <Icon className={cn("h-6 w-6", !isCollapsed && "mr-3 ml-1")} />
              </div>
              {!isCollapsed && <span className="ml-1">{label}</span>}
            </a>
          );
        })}
      </nav>
    </div>
  );
}
