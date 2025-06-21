'use client';

import React, { useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import { Spinner } from './ui/Spinner';

// Loading component for lazy-loaded components
const LoadingFallback = ({ message = 'Loading...' }: { message?: string }) => (
  <div className="flex items-center justify-center p-8">
    <div className="flex flex-col items-center gap-2">
      <Spinner size="lg" />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  </div>
);

// Error fallback for lazy-loaded components
const ErrorFallback = ({ error, retry }: { error: Error; retry: () => void }) => (
  <div className="flex flex-col items-center justify-center p-8 text-center">
    <div className="text-red-500 mb-4">
      <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    </div>
    <h3 className="text-lg font-semibold mb-2">Failed to load component</h3>
    <p className="text-gray-600 mb-4">{error.message}</p>
    <button
      onClick={retry}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
    >
      Try Again
    </button>
  </div>
);

// Dynamic imports for heavy components
export const LazyBackupManager = dynamic(
  () => import('./backup/BackupManager').then(mod => ({ default: mod.BackupManager })),
  {
    loading: () => <LoadingFallback message="Loading backup manager..." />,
    ssr: false, // Disable SSR for this component as it's heavy
  }
);

export const LazyRAGManager = dynamic(
  () => import('./rag/RAGManager').then(mod => ({ default: mod.RAGManager })),
  {
    loading: () => <LoadingFallback message="Loading RAG manager..." />,
    ssr: false,
  }
);

export const LazyRAGUpload = dynamic(
  () => import('./rag/RAGUpload').then(mod => ({ default: mod.default })),
  {
    loading: () => <LoadingFallback message="Loading RAG upload..." />,
    ssr: false,
  }
);

export const LazyChatInterface = dynamic(
  () => import('./chat/ChatInterface').then(mod => ({ default: mod.ChatInterface })),
  {
    loading: () => <LoadingFallback message="Loading chat interface..." />,
    ssr: true, // Enable SSR for chat as it's core functionality
  }
);

export const LazyCookingChat = dynamic(
  () => import('./cooking/CookingChat').then(mod => ({ default: mod.CookingChat })),
  {
    loading: () => <LoadingFallback message="Loading cooking assistant..." />,
    ssr: true,
  }
);

export const LazyProductTable = dynamic(
  () => import('./shopping/ProductTable').then(mod => ({ default: mod.ProductTable })),
  {
    loading: () => <LoadingFallback message="Loading product table..." />,
    ssr: true,
  }
);

export const LazyReceiptUploader = dynamic(
  () => import('./shopping/ReceiptUploader').then(mod => ({ default: mod.ReceiptUploader })),
  {
    loading: () => <LoadingFallback message="Loading receipt uploader..." />,
    ssr: false,
  }
);

export const LazyPantryList = dynamic(
  () => import('./cooking/PantryList').then(mod => ({ default: mod.PantryList })),
  {
    loading: () => <LoadingFallback message="Loading pantry list..." />,
    ssr: true,
  }
);

// Wrapper component for lazy-loaded components with error boundary
interface LazyComponentWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function LazyComponentWrapper({ children, fallback }: LazyComponentWrapperProps) {
  return (
    <Suspense fallback={fallback || <LoadingFallback />}>
      {children}
    </Suspense>
  );
}

// Utility function to preload components
export const preloadComponent = {
  backupManager: () => import('./backup/BackupManager'),
  ragManager: () => import('./rag/RAGManager'),
  ragUpload: () => import('./rag/RAGUpload'),
  chatInterface: () => import('./chat/ChatInterface'),
  cookingChat: () => import('./cooking/CookingChat'),
  productTable: () => import('./shopping/ProductTable'),
  receiptUploader: () => import('./shopping/ReceiptUploader'),
  pantryList: () => import('./cooking/PantryList'),
};

// Hook for component preloading
export function useComponentPreloader() {
  const preload = useCallback((componentName: keyof typeof preloadComponent) => {
    // Preload component when user hovers over navigation or similar
    preloadComponent[componentName]();
  }, []);

  return { preload };
}

// Bundle size monitoring utility
export const bundleSizeMonitor = {
  // Track component load times
  trackLoadTime: (componentName: string, loadTime: number) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`Component ${componentName} loaded in ${loadTime}ms`);
    }

    // TODO: Send to analytics service in production
    if (process.env.NODE_ENV === 'production') {
      // Send to monitoring service
      console.log('Bundle size metric:', { componentName, loadTime });
    }
  },

  // Track component load failures
  trackLoadFailure: (componentName: string, error: Error) => {
    console.error(`Failed to load component ${componentName}:`, error);

    // TODO: Send to error tracking service in production
    if (process.env.NODE_ENV === 'production') {
      console.error('Component load failure:', { componentName, error: error.message });
    }
  },
};

export default LazyComponentWrapper;
