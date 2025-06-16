"use client";

import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message } from '@/types/chat';
import { ApiService } from '@/services/ApiService';

export function useChat(context: 'general' | 'shopping' | 'cooking' = 'general') {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>('');

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

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    const userMessage: Message = { id: uuidv4(), role: 'user', content };
    setMessages((prev: Message[]) => [...prev, userMessage]);

    // Add a placeholder for the assistant's response
    const assistantMessageId = uuidv4();
    setMessages((prev: Message[]) => [...prev, { id: assistantMessageId, role: 'assistant', content: '' }]);

    try {
      await ApiService.sendChatMessage(
        {
          message: content,
          session_id: sessionId,
          agent_states: {
            weather: context === 'general',
            search: context === 'general',
            shopping: context === 'shopping',
            cooking: context === 'cooking',
          },
        },
        (chunk) => {
          setMessages((prev: Message[]) =>
            prev.map((msg: Message) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + (chunk.response || '') }
                : msg
            )
          );
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      setMessages((prev: Message[]) =>
        prev.map((msg: Message) =>
          msg.id === assistantMessageId
            ? { ...msg, content: 'Przepraszam, wystąpił błąd.' }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

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

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
}
