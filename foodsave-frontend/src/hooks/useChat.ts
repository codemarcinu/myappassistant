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
  const [isShoppingMode, setIsShoppingMode] = useState(false);
  const [isCookingMode, setIsCookingMode] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);

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

      // Create a new empty assistant message for streaming
      const assistantMessageId = uuidv4();
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true,
      };

      // Set as the current streaming message
      setStreamingMessage(assistantMessage);

      // Send message to the API
      const response = await ApiService.sendChatMessage({
        message: content,
        session_id: sessionId,
        agent_states: {
          weather: true,
          search: true,
          shopping: isShoppingMode,
          cooking: isCookingMode,
        },
        usePerplexity: usePerplexity || false,
        useBielik: useBielik !== undefined ? useBielik : true,
      }, (chunk) => {
        // Handle streaming response
        if (chunk && chunk.text) {
          setStreamingMessage(prev => {
            if (!prev) return null;
            return {
              ...prev,
              content: prev.content + chunk.text,
              data: chunk.data || prev.data,
            };
          });
        }
      });

      // After streaming is complete, add the final message to the list
      setMessages(prev => {
        // First check if the streaming message is already in the list
        if (prev.some(msg => msg.id === assistantMessageId)) {
          return prev;
        }

        // If we have a streaming message, use that as the final message
        if (streamingMessage && streamingMessage.content) {
          return [...prev, streamingMessage];
        }

        // Fallback to the response from the API if no streaming content
        const finalMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: response?.response || 'Przepraszam, wystąpił błąd w przetwarzaniu.',
          data: response?.data || null,
          usePerplexity: usePerplexity || false,
          useBielik: useBielik !== undefined ? useBielik : true,
        };
        return [...prev, finalMessage];
      });

      // Clear the streaming message
      setStreamingMessage(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Wystąpił nieznany błąd';
      setError(errorMessage);

      const errorResponse: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: `Wystąpił błąd: ${errorMessage}`,
        isError: true,
      };
      setMessages(prev => [...prev, errorResponse]);
      setStreamingMessage(null);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, isShoppingMode, isCookingMode, streamingMessage]);

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
    setStreamingMessage(null);
  };

  // Function to toggle Perplexity
  const togglePerplexity = () => {
    setUsePerplexity((prev: boolean) => !prev);
  };

  // Function to toggle model (Bielik/Gemma)
  const toggleModel = () => {
    setUseBielik((prev: boolean) => !prev);
  };

  const toggleShoppingMode = () => {
    setIsShoppingMode((prev: boolean) => !prev);
  };

  const toggleCookingMode = () => {
    setIsCookingMode((prev: boolean) => !prev);
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
    isShoppingMode,
    toggleShoppingMode,
    isCookingMode,
    toggleCookingMode,
    streamingMessage,
  };
}
