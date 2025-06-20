"use client";

import { useState, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message } from '@/types/chat';
import { ApiService } from '@/services/ApiService';

export function useChat(context: 'general' | 'shopping' | 'cooking' = 'general') {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [usePerplexity, setUsePerplexity] = useState(false);
  const [useBielik, setUseBielik] = useState(true); // Domyślnie używamy Bielika

  useEffect(() => {
    // Initialize session on component mount
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    setMessages([
      {
        id: uuidv4(),
        role: 'assistant',
        content: 'Cześć! Jestem Twoim asystentem FoodSave. W czym mogę dziś pomóc?'
      }
    ]);
  }, []);

  const sendMessage = useCallback(async (content: string, usePerplexity?: boolean, useBielik?: boolean) => {
    try {
      setError(null);
      setIsLoading(true);

      // Add user message to the chat
      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content,
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true
      };
      setMessages(prev => [...prev, userMessage]);

      // Send message to the API
      const response = await ApiService.sendChatMessage({
        message: content,
        session_id: sessionId,
        agent_states: {
          weather: true,
          search: true,
          shopping: context === 'shopping',
          cooking: context === 'cooking',
        },
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true,
      }, (chunk) => {
        // Handle streaming response
        console.log('Received chunk:', chunk);
      });

      // Add assistant response to the chat
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.response || 'Przepraszam, wystąpił błąd w przetwarzaniu.',
        data: response.data,
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, context]);

  // Function to clear chat history
  const clearChat = () => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    setMessages([
      {
        id: uuidv4(),
        role: 'assistant',
        content: 'Cześć! Jestem Twoim asystentem FoodSave. W czym mogę dziś pomóc?'
      }
    ]);
  };

  // Function to toggle Perplexity
  const togglePerplexity = () => {
    setUsePerplexity((prev: boolean) => !prev);
  };

  // Function to toggle model (Bielik/Gemma)
  const toggleModel = () => {
    setUseBielik((prev: boolean) => !prev);
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
    usePerplexity,
    togglePerplexity,
    useBielik,
    toggleModel,
  };
}
