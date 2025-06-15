# FoodSave AI Frontend Refactoring Plan: Streamlit to Next.js/TypeScript

## 1. Introduction & Executive Summary

This document outlines a comprehensive plan for refactoring the FoodSave AI frontend from Streamlit to Next.js with TypeScript. The current prototype uses Streamlit, which is suitable for quick prototyping but lacks the flexibility and user experience capabilities needed for a modern, responsive web application. The refactoring will maintain all existing functionality while significantly improving user experience, performance, and maintainability.

The migration will focus on:
- Converting the existing Streamlit UI components to React components
- Implementing a TypeScript-based type system for improved developer experience and code quality
- Creating a modular architecture with clear separation of concerns
- Ensuring seamless integration with the existing FastAPI backend
- Implementing responsive design and accessibility features
- Optimizing performance for both desktop and mobile users

## 2. Recommended Architecture Overview

### Technology Stack Rationale

**Next.js (App Router)**: Next.js provides server-side rendering, static site generation, and API routes, making it ideal for building fast, SEO-friendly web applications. The App Router offers an intuitive file-based routing system and built-in data fetching capabilities.

**React**: The most popular JavaScript library for building user interfaces, offering a component-based architecture that promotes code reusability and maintainability.

**TypeScript**: Adds static typing to JavaScript, enhancing developer experience through better tooling, code completion, and early error detection.

**CSS Modules + Tailwind CSS**: Combines the benefits of scoped CSS with the utility-first approach of Tailwind, allowing for rapid UI development while maintaining style encapsulation.

### Detailed Project Structure

```
foodsave-frontend/
├── public/                  # Static assets (images, fonts, etc.)
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── layout.tsx       # Root layout component
│   │   ├── page.tsx         # Home page (dashboard)
│   │   ├── dashboard/       # Dashboard module
│   │   │   └── page.tsx     # Dashboard page
│   │   ├── chat/            # Chat module
│   │   │   └── page.tsx     # Chat page
│   │   ├── shopping/        # Shopping module
│   │   │   └── page.tsx     # Shopping page
│   │   └── cooking/         # Cooking module
│   │       └── page.tsx     # Cooking page
│   ├── components/          # Reusable React components
│   │   ├── ui/              # UI components (Button, Card, etc.)
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── Modal/
│   │   │   ├── Input/
│   │   │   └── Badge/
│   │   ├── dashboard/       # Dashboard-specific components
│   │   ├── chat/            # Chat-specific components
│   │   ├── shopping/        # Shopping-specific components
│   │   ├── cooking/         # Cooking-specific components
│   │   └── common/          # Shared components (Header, Footer, etc.)
│   ├── hooks/               # Custom React hooks
│   │   ├── useChat.ts       # Chat hook for state management
│   │   ├── useShopping.ts   # Shopping hook
│   │   └── useCooking.ts    # Cooking hook
│   ├── lib/                 # Utility functions and libraries
│   │   ├── utils.ts         # General utility functions
│   │   └── helpers/         # Helper functions
│   ├── services/            # API services
│   │   ├── ApiService.ts    # Base API service
│   │   ├── ChatService.ts   # Chat module API service
│   │   ├── ShoppingService.ts # Shopping module API service
│   │   └── CookingService.ts # Cooking module API service
│   └── types/               # TypeScript type definitions
│       ├── api.ts           # API-related types
│       ├── chat.ts          # Chat module types
│       ├── shopping.ts      # Shopping module types
│       └── cooking.ts       # Cooking module types
├── tailwind.config.js       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
├── package.json             # Project dependencies
└── next.config.js           # Next.js configuration
```

## 3. Core Module Implementation Details

### Dashboard Module

The dashboard serves as the central hub, displaying weather information for Ząbki and Warsaw, and providing navigation to the three main modules: Chat, Shopping, and Cooking.

#### Dashboard Components

```typescript
// src/components/dashboard/WeatherWidget.tsx
import React from 'react';
import { Card } from '../ui/Card';
import { WeatherData } from '@/types/api';

interface WeatherWidgetProps {
  data: WeatherData;
  isLoading?: boolean;
}

export const WeatherWidget: React.FC<WeatherWidgetProps> = ({
  data,
  isLoading = false
}) => {
  if (isLoading) {
    return <Card className="p-4 h-40 animate-pulse" />;
  }

  return (
    <Card className="p-4 mb-4">
      <h2 className="text-xl font-semibold">{data.location}</h2>
      <div className="flex items-center mt-2">
        <div className="text-4xl font-bold mr-2">{data.temperature}°C</div>
        <div>
          <div>{data.condition}</div>
          <div className="text-sm text-gray-500">
            H: {data.highTemp}° L: {data.lowTemp}°
          </div>
        </div>
      </div>
    </Card>
  );
};

// src/components/dashboard/NavigationCard.tsx
import Link from 'next/link';
import { Card } from '../ui/Card';
import { Icon } from '../ui/Icon';

interface NavigationCardProps {
  title: string;
  href: string;
  icon: string;
  color: string;
  description?: string;
}

export const NavigationCard: React.FC<NavigationCardProps> = ({
  title,
  href,
  icon,
  color,
  description
}) => {
  return (
    <Link href={href} className="block">
      <Card className={`p-6 text-white ${color} hover:opacity-90 transition-all`}>
        <div className="flex flex-col items-center">
          <Icon name={icon} className="text-4xl mb-2" />
          <h3 className="text-xl font-semibold">{title}</h3>
          {description && <p className="mt-2 text-sm opacity-90">{description}</p>}
        </div>
      </Card>
    </Link>
  );
};

// src/app/dashboard/page.tsx
import { Suspense } from 'react';
import { WeatherWidget } from '@/components/dashboard/WeatherWidget';
import { NavigationCard } from '@/components/dashboard/NavigationCard';
import { fetchWeatherData } from '@/services/ApiService';

async function Dashboard() {
  // Data fetching using Next.js Server Components
  const zabkiWeather = await fetchWeatherData('Ząbki');
  const warsawWeather = await fetchWeatherData('Warsaw');

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">FoodSave AI Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <Suspense fallback={<WeatherWidget data={{}} isLoading={true} />}>
          <WeatherWidget data={zabkiWeather} />
        </Suspense>
        <Suspense fallback={<WeatherWidget data={{}} isLoading={true} />}>
          <WeatherWidget data={warsawWeather} />
        </Suspense>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NavigationCard
          title="Chat"
          href="/chat"
          icon="MessageCircle"
          color="bg-blue-600"
          description="Porozmawiaj z asystentem AI"
        />
        <NavigationCard
          title="Shopping"
          href="/shopping"
          icon="ShoppingCart"
          color="bg-green-600"
          description="Zarządzaj swoimi zakupami"
        />
        <NavigationCard
          title="Cooking"
          href="/cooking"
          icon="ChefHat"
          color="bg-orange-600"
          description="Znajdź przepisy i zarządzaj spiżarnią"
        />
      </div>
    </div>
  );
}

export default Dashboard;
```

### Chat Module

The Chat module provides a standard conversational interface with a local LLM agent for free-form conversation.

#### Chat Components

```typescript
// src/components/chat/MessageItem.tsx
import { Avatar } from '../ui/Avatar';
import { Card } from '../ui/Card';
import { Message } from '@/types/chat';

interface MessageItemProps {
  message: Message;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} max-w-[80%]`}>
        <Avatar
          src={isUser ? '/images/user-avatar.png' : '/images/assistant-avatar.png'}
          alt={isUser ? 'User' : 'Assistant'}
          className="h-8 w-8"
        />
        <Card className={`p-3 mx-2 ${isUser ? 'bg-blue-100' : 'bg-gray-100'}`}>
          <div className="text-sm">{message.content}</div>
          {message.data && (
            <div className="mt-2 text-xs p-2 bg-white rounded">
              <pre>{JSON.stringify(message.data, null, 2)}</pre>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

// src/components/chat/MessageInput.tsx
import { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  isLoading = false
}) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center mt-4">
      <Input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Wpisz wiadomość..."
        className="flex-grow mr-2"
        disabled={isLoading}
      />
      <Button
        type="submit"
        disabled={isLoading || !message.trim()}
        isLoading={isLoading}
      >
        Wyślij
      </Button>
    </form>
  );
};
```

#### Chat Hook

```typescript
// src/hooks/useChat.ts
import { useState } from 'react';
import { Message } from '@/types/chat';
import { ApiService } from '@/services/ApiService';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Cześć! Jestem Twoim asystentem FoodSave. W czym mogę dziś pomóc?'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationState, setConversationState] = useState({});

  const sendMessage = async (content: string) => {
    try {
      setError(null);
      setIsLoading(true);

      // Add user message to the chat
      const userMessage: Message = { role: 'user', content };
      setMessages(prev => [...prev, userMessage]);

      // Send message to the API
      const response = await ApiService.sendChatMessage({
        task: content,
        conversation_state: conversationState,
        agent_states: {
          weather: true,
          search: true,
          shopping: false,
          cooking: false,
        }
      });

      // Update conversation state
      if (response.conversation_state) {
        setConversationState(response.conversation_state);
      }

      // Add assistant response to the chat
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response || 'Przepraszam, wystąpił błąd w przetwarzaniu.',
        data: response.data
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
  };
}
```

### Shopping Module

The Shopping module provides a specialized chat interface for the Shopping Agent, with functionalities for receipt upload, data normalization, and product management.

#### Shopping Components

```typescript
// src/components/shopping/ReceiptUploader.tsx
import { useState } from 'react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

interface ReceiptUploaderProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

export const ReceiptUploader: React.FC<ReceiptUploaderProps> = ({
  onUpload,
  isUploading
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      await onUpload(selectedFile);
      setSelectedFile(null);
    }
  };

  return (
    <Card className="p-4 mb-6">
      <h3 className="text-lg font-semibold mb-3">Wgraj paragon</h3>
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={handleFileChange}
          className="flex-grow"
          disabled={isUploading}
        />
        <Button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          isLoading={isUploading}
        >
          {isUploading ? 'Przetwarzanie...' : 'Wgraj'}
        </Button>
      </div>
      {selectedFile && (
        <div className="mt-2 text-sm">
          Wybrany plik: {selectedFile.name}
        </div>
      )}
    </Card>
  );
};

// src/components/shopping/ProductTable.tsx
import { Table } from '../ui/Table';
import { Product } from '@/types/shopping';

interface ProductTableProps {
  products: Product[];
  isLoading?: boolean;
}

export const ProductTable: React.FC<ProductTableProps> = ({
  products,
  isLoading = false
}) => {
  if (isLoading) {
    return <div className="h-40 animate-pulse bg-gray-100 rounded" />;
  }

  if (products.length === 0) {
    return <div className="text-center p-4">Brak produktów do wyświetlenia</div>;
  }

  return (
    <Table>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell>Nazwa</Table.HeaderCell>
          <Table.HeaderCell>Ilość</Table.HeaderCell>
          <Table.HeaderCell>Cena</Table.HeaderCell>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {products.map((product) => (
          <Table.Row key={product.id}>
            <Table.Cell>{product.name}</Table.Cell>
            <Table.Cell>{product.quantity} {product.unit}</Table.Cell>
            <Table.Cell>{product.price} zł</Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
};
```

### Cooking (Pantry) Module

The Cooking module features a split-screen layout displaying pantry items on one side and a chat interface on the other, allowing for meal planning and pantry management.

#### Cooking Components

```typescript
// src/components/cooking/PantryList.tsx
import { useState } from 'react';
import { Card } from '../ui/Card';
import { List } from '../ui/List';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { PantryItem } from '@/types/cooking';

interface PantryListProps {
  items: PantryItem[];
  isLoading?: boolean;
  onAddItem?: (item: Omit<PantryItem, 'id'>) => Promise<void>;
}

export const PantryList: React.FC<PantryListProps> = ({
  items,
  isLoading = false,
  onAddItem
}) => {
  const [newItem, setNewItem] = useState('');

  const handleAddItem = async () => {
    if (newItem.trim() && onAddItem) {
      await onAddItem({ name: newItem, unified_category: 'Nieskategoryzowane' });
      setNewItem('');
    }
  };

  if (isLoading) {
    return <Card className="h-[calc(100vh-200px)] animate-pulse" />;
  }

  return (
    <Card className="h-[calc(100vh-200px)] overflow-auto">
      <div className="p-4 border-b">
        <h2 className="text-xl font-semibold mb-4">Moja Spiżarnia</h2>
        <div className="flex gap-2">
          <Input
            type="text"
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            placeholder="Dodaj nowy produkt..."
            className="flex-grow"
          />
          <Button onClick={handleAddItem} disabled={!newItem.trim()}>
            Dodaj
          </Button>
        </div>
      </div>

      <List>
        {items.map((item) => (
          <List.Item key={item.id} className="p-3 border-b">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium">{item.name}</div>
                <div className="text-sm text-gray-500">{item.unified_category}</div>
              </div>
            </div>
          </List.Item>
        ))}
        {items.length === 0 && (
          <div className="p-4 text-center text-gray-500">
            Twoja spiżarnia jest pusta
          </div>
        )}
      </List>
    </Card>
  );
};

// src/components/cooking/CookingChat.tsx
import { useState } from 'react';
import { Card } from '../ui/Card';
import { MessageList } from '../chat/MessageList';
import { MessageInput } from '../chat/MessageInput';
import { Message } from '@/types/chat';

interface CookingChatProps {
  pantryItems: any[];
  onSendMessage: (message: string) => Promise<void>;
  messages: Message[];
  isLoading?: boolean;
}

export const CookingChat: React.FC<CookingChatProps> = ({
  pantryItems,
  onSendMessage,
  messages,
  isLoading = false
}) => {
  return (
    <Card className="h-[calc(100vh-200px)] flex flex-col">
      <div className="p-4 border-b">
        <h2 className="text-xl font-semibold">Asystent kulinarny</h2>
      </div>

      <div className="flex-grow overflow-auto p-4">
        <MessageList messages={messages} />
      </div>

      <div className="p-4 border-t">
        <MessageInput
          onSendMessage={onSendMessage}
          isLoading={isLoading}
        />
      </div>
    </Card>
  );
};
```

## 4. UI Component System

### Design Principles

The UI component system follows these key principles:
- **Composability**: Components should be easily composable to build complex UIs
- **Reusability**: Components should be designed for reuse across the application
- **Consistency**: Components should maintain consistent styling and behavior
- **Accessibility**: Components should be accessible to all users
- **Flexibility**: Components should be flexible enough to adapt to different contexts

### Key Components & Examples

```typescript
// src/components/ui/Button/Button.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { Spinner } from '../Spinner';

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "underline-offset-4 hover:underline text-primary",
      },
      size: {
        default: "h-10 py-2 px-4",
        sm: "h-9 px-3 rounded-md",
        lg: "h-11 px-8 rounded-md",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, ...props }, ref) => {
    return (
      <button
        className={buttonVariants({ variant, size, className })}
        ref={ref}
        disabled={isLoading || props.disabled}
        {...props}
      >
        {isLoading ? (
          <>
            <Spinner className="mr-2" />
            {children}
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

// src/components/ui/Card/Card.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const cardVariants = cva(
  "rounded-lg border bg-card text-card-foreground shadow-sm",
  {
    variants: {
      variant: {
        default: "",
        destructive: "border-destructive",
        outline: "border",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cardVariants({ variant, className })}
        {...props}
      />
    );
  }
);

Card.displayName = "Card";
```

## 5. State Management Strategy

### Local State Management

For local state management within components, we'll use React's built-in hooks such as `useState` and `useReducer`. For more complex state management needs, we'll create custom hooks for each module that encapsulate the state logic and provide a clean API for components to interact with.

```typescript
// src/hooks/useShopping.ts
import { useState, useCallback, useEffect } from 'react';
import { Product, Receipt } from '@/types/shopping';
import { ShoppingService } from '@/services/ShoppingService';

export function useShopping() {
  const [products, setProducts] = useState<Product[]>([]);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch products
  const fetchProducts = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await ShoppingService.getProducts();
      setProducts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch products');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Upload receipt
  const uploadReceipt = useCallback(async (file: File) => {
    try {
      setIsLoading(true);
      const result = await ShoppingService.uploadReceipt(file);

      // Refresh products after upload
      await fetchProducts();

      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload receipt');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchProducts]);

  // Load initial data
  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return {
    products,
    receipts,
    isLoading,
    error,
    fetchProducts,
    uploadReceipt,
  };
}
```

### Global State Management

For global state that needs to be shared across multiple components, we'll use React Context API to provide a lightweight state management solution without adding external dependencies.

```typescript
// src/lib/contexts/AppContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/types/user';
import { ApiService } from '@/services/ApiService';

interface AppContextType {
  user: User | null;
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Load user data
  useEffect(() => {
    const loadUser = async () => {
      try {
        const userData = await ApiService.getCurrentUser();
        setUser(userData);
      } catch (error) {
        console.error('Failed to load user data:', error);
      }
    };

    loadUser();
  }, []);

  // Function to add a notification
  const addNotification = (notification: Omit<Notification, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    setNotifications(prev => [...prev, { ...notification, id }]);

    // Auto-remove notifications after 5 seconds
    setTimeout(() => {
      removeNotification(id);
    }, 5000);
  };

  // Function to remove a notification
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  };

  return (
    <AppContext.Provider
      value={{
        user,
        theme,
        setTheme,
        notifications,
        addNotification,
        removeNotification,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
```

## 6. API Integration

### ApiService Design

The `ApiService` will be a centralized service for communicating with the backend API. It will handle common tasks such as making HTTP requests, handling errors, and formatting responses.

```typescript
// src/services/ApiService.ts
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

class ApiServiceClass {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      // Add authentication token if available
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle common errors (e.g., 401 Unauthorized, 500 Server Error)
        if (error.response) {
          const { status } = error.response;

          if (status === 401) {
            // Handle unauthorized error
            localStorage.removeItem('authToken');
            window.location.href = '/login';
          }

          // Return error message from response if available
          const errorMessage = error.response.data?.detail || error.response.data?.error || 'An error occurred';
          return Promise.reject(new Error(errorMessage));
        }

        // Handle network errors
        return Promise.reject(new Error('Network error. Please check your connection.'));
      }
    );
  }

  // Generic request method
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client(config);
      return response.data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Unknown error occurred');
    }
  }

  // GET request
  public async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    return this.request<T>({ method: 'GET', url, params });
  }

  // POST request
  public async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'POST', url, data });
  }

  // PUT request
  public async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'PUT', url, data });
  }

  // PATCH request
  public async patch<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({ method: 'PATCH', url, data });
  }

  // DELETE request
  public async delete<T>(url: string): Promise<T> {
    return this.request<T>({ method: 'DELETE', url });
  }

  // File upload with progress tracking
  public async uploadFile<T>(
    url: string,
    file: File,
    onProgress?: (percentage: number) => void
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentage);
        }
      },
    });
  }

  // Specific API methods

  // Send chat message
  public async sendChatMessage(payload: {
    task: string;
    conversation_state?: Record<string, any>;
    agent_states?: Record<string, boolean>;
  }) {
    return this.post('/api/v1/agents/execute', payload);
  }

  // Upload receipt
  public async uploadReceipt(file: File) {
    return this.uploadFile('/api/v1/receipts/upload', file);
  }

  // Get products
  public async getProducts() {
    return this.get('/api/v1/pantry/products');
  }

  // Get weather data
  public async getWeatherData(location: string) {
    return this.get('/api/v1/weather', { location });
  }
}

// Create a singleton instance
export const ApiService = new ApiServiceClass();

// Helper function for fetching weather data (used in Server Components)
export async function fetchWeatherData(location: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/weather?location=${encodeURIComponent(location)}`);
  if (!response.ok) {
    throw new Error('Failed to fetch weather data');
  }
  return response.json();
}
```

## 7. Performance Optimization

### Lazy Loading

Next.js provides built-in support for code splitting through dynamic imports. We'll use this feature to lazily load components and modules that aren't immediately needed, reducing the initial bundle size and improving load times.

```typescript
// src/app/shopping/page.tsx
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import { Loading } from '@/components/ui/Loading';

// Dynamically import the ShoppingPage component
const ShoppingPage = dynamic(
  () => import('@/components/shopping/ShoppingPage'),
  {
    loading: () => <Loading />,
    ssr: false, // Disable server-side rendering for components that need browser APIs
  }
);

export default function Shopping() {
  return (
    <Suspense fallback={<Loading />}>
      <ShoppingPage />
    </Suspense>
  );
}
```

### Memoization

We'll use React's memoization features (`React.memo`, `useMemo`, and `useCallback`) to optimize rendering performance by avoiding unnecessary re-renders.

```typescript
// src/components/cooking/RecipeCard.tsx
import React, { useMemo } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Recipe } from '@/types/cooking';

interface RecipeCardProps {
  recipe: Recipe;
  onSelect: (recipe: Recipe) => void;
}

// Memoize the component to prevent unnecessary re-renders
export const RecipeCard = React.memo(({ recipe, onSelect }: RecipeCardProps) => {
  // Memoize the ingredient list to avoid recalculating on each render
  const ingredientList = useMemo(() => {
    return recipe.ingredients.map(ingredient => (
      <Badge key={ingredient.id} variant="outline" className="mr-1 mb-1">
        {ingredient.name}
      </Badge>
    ));
  }, [recipe.ingredients]);

  return (
    <Card
      className="p-4 cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onSelect(recipe)}
    >
      <h3 className="text-lg font-semibold">{recipe.name}</h3>
      <p className="text-sm text-gray-500 mb-2">
        {recipe.prepTime} min • {recipe.difficulty}
      </p>
      <div className="flex flex-wrap mt-2">
        {ingredientList}
      </div>
    </Card>
  );
});

RecipeCard.displayName = 'RecipeCard';
```

## 8. Responsiveness and Accessibility

### Mobile-First Approach

We'll design the UI using a mobile-first approach, ensuring that the application looks and works well on devices of all sizes.

```typescript
// src/components/layout/MainLayout.tsx
import { ReactNode } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { Sidebar } from './Sidebar';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <div className="flex flex-grow flex-col md:flex-row">
        {/* Sidebar - hidden on mobile, visible on tablet and desktop */}
        <div className="hidden md:block md:w-64 lg:w-80 shrink-0">
          <Sidebar />
        </div>

        {/* Mobile drawer for sidebar content */}
        <div className="md:hidden">
          {/* Mobile drawer implementation */}
        </div>

        {/* Main content area - full width on mobile, partial width on desktop */}
        <main className="flex-grow p-4 md:p-6">
          {children}
        </main>
      </div>

      <Footer />
    </div>
  );
}
```

### WCAG Compliance

We'll ensure that the application meets WCAG (Web Content Accessibility Guidelines) standards by implementing proper semantic HTML, ARIA attributes, keyboard navigation, and color contrast.

```typescript
// src/components/ui/Input/Input.tsx
import React from 'react';

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    // Generate a unique ID for the input if not provided
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    return (
      <div className="space-y-2">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          className={`
            w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500
            ${error ? 'border-red-500' : 'border-gray-300'}
            ${className}
          `}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
          }
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-red-500" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

## 9. Migration Plan (Phased Approach)

### Phase 1: Infrastructure Setup (Weeks 1-2)

1. Set up Next.js project with TypeScript
2. Configure linting, formatting, and other development tools
3. Create project structure according to the plan
4. Implement base UI components

### Phase 2: Core Module Development (Weeks 3-6)

1. Implement ApiService for communication with the backend
2. Develop basic layout and navigation
3. Implement Dashboard module
4. Implement Chat module
5. Implement Shopping module
6. Implement Cooking module

### Phase 3: Integration & Testing (Weeks 7-8)

1. Integrate all modules with the backend API
2. Implement error handling and edge cases
3. Conduct unit and integration tests
4. Perform end-to-end testing

### Phase 4: Optimization & Refinement (Weeks 9-10)

1. Optimize performance (lazy loading, memoization)
2. Ensure responsiveness across all devices
3. Implement accessibility features
4. Conduct user testing and gather feedback

### Phase 5: Deployment & Handover (Weeks 11-12)

1. Set up CI/CD pipeline
2. Deploy to staging environment
3. Conduct final testing
4. Deploy to production
5. Document the codebase
6. Provide knowledge transfer sessions

## 10. Anticipated Benefits

### For Users:

- **Improved Performance**: Faster load times and more responsive UI
- **Enhanced User Experience**: More intuitive and modern interface
- **Mobile Access**: Fully responsive design works well on all devices
- **Accessibility**: WCAG-compliant design ensures access for all users

### For Development:

- **Maintainability**: Modular architecture and clean code make maintenance easier
- **Scalability**: The new architecture can easily accommodate future features
- **Testability**: TypeScript and component-based architecture improve testability
- **Developer Experience**: Modern tools and type safety enhance productivity

## 11. Conclusion

This refactoring plan provides a comprehensive roadmap for transforming the FoodSave AI frontend from Streamlit to Next.js with TypeScript. The plan focuses on maintaining all existing functionality while significantly improving the user experience, performance, and maintainability of the application.

By following this plan, the development team will be able to create a modern, responsive, and accessible web application that meets the needs of both users and developers. The phased approach ensures that the refactoring process is manageable and allows for continuous testing and refinement throughout the development cycle.

The result will be a robust, scalable frontend that interfaces seamlessly with the existing backend API and provides a solid foundation for future enhancements.
