/**
 * Type definitions for the Chat module
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  isError?: boolean;
  data?: any;
  timestamp?: number;
  usePerplexity?: boolean;
  useBielik?: boolean;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  conversationState: Record<string, any>;
  usePerplexity: boolean;
}

export interface ChatContextType {
  state: ChatState;
  sendMessage: (content: string, usePerplexity?: boolean) => Promise<void>;
  clearChat: () => void;
  togglePerplexity: () => void;
}

export interface MessageItemProps {
  message: Message;
  isLoading?: boolean;
}

export interface MessageInputProps {
  onSendMessage: (message: string, usePerplexity?: boolean, useBielik?: boolean) => void;
  isLoading?: boolean;
  placeholder?: string;
  usePerplexity?: boolean;
  onTogglePerplexity?: () => void;
  useBielik?: boolean;
  onToggleModel?: () => void;
  isShoppingMode?: boolean;
  onToggleShoppingMode?: () => void;
  isCookingMode?: boolean;
  onToggleCookingMode?: () => void;
}

export interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}
