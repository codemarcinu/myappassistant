'use client';

import React from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageInput } from './MessageInput';
import { MessageList } from './MessageList';
import { Card } from '../ui/Card';

export function ChatInterface() {
  const {
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
  } = useChat();

  return (
    <Card className="flex flex-col h-[70vh] p-4" data-testid="chat-interface">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Asystent AI</h2>
        <button
          onClick={clearChat}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Wyczyść czat
        </button>
      </div>

      <div className="flex-grow overflow-y-auto mb-4 pr-2">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>

      <MessageInput
        onSendMessage={sendMessage}
        isLoading={isLoading}
        usePerplexity={usePerplexity}
        onTogglePerplexity={togglePerplexity}
        useBielik={useBielik}
        onToggleModel={toggleModel}
        isShoppingMode={isShoppingMode}
        onToggleShoppingMode={toggleShoppingMode}
        isCookingMode={isCookingMode}
        onToggleCookingMode={toggleCookingMode}
      />

      {error && (
        <div className="mt-2 text-red-500 text-sm">
          {error}
        </div>
      )}
    </Card>
  );
}
