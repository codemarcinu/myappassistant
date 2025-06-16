/**
 * Type definitions for the Chat module
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  data?: any;
  timestamp?: number;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  conversationState: Record<string, any>;
}

export interface ChatContextType {
  state: ChatState;
  sendMessage: (content: string) => Promise<void>;
  clearChat: () => void;
}

export interface MessageItemProps {
  message: Message;
  isLoading?: boolean;
}

export interface MessageInputProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
}

export interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}
