"use client";

import { useState } from 'react';
import { Message } from '@/types/chat';
import { ApiService } from '@/services/ApiService';

interface ConversationResponse {
  response?: string;
  conversation_state?: Record<string, any>;
  data?: any;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Cześć! Jestem Twoim asystentem FoodSave. W czym mogę dziś pomóc?'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationState, setConversationState] = useState<Record<string, any>>({});

  const sendMessage = async (content: string) => {
    try {
      setError(null);
      setIsLoading(true);

      // Add user message to the chat
      const userMessage: Message = { role: 'user', content };
      setMessages((prev: Message[]) => [...prev, userMessage]);

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
      }) as ConversationResponse;

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

      setMessages((prev: Message[]) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  // Function to clear chat history
  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Cześć! Jestem Twoim asystentem FoodSave. W czym mogę dziś pomóc?'
      }
    ]);
    setConversationState({});
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
}
