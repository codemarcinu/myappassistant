import React from 'react';
import { Card } from '../ui/Card';
import { MessageList } from '../chat/MessageList';
import { MessageInput } from '../chat/MessageInput';
import { Message } from '@/types/chat';
import { CookingChatProps } from '@/types/cooking';
import { useCooking } from '@/hooks/useCooking';

export function CookingChat() {
  const {
    messages,
    isLoading,
    error,
    sendCookingMessage,
    usePerplexity,
    togglePerplexity,
    useBielik,
    toggleModel
  } = useCooking();

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Asystent Kulinarny</h2>
      </div>

      <MessageList messages={messages} />

      <MessageInput
        onSendMessage={sendCookingMessage}
        isLoading={isLoading}
        usePerplexity={usePerplexity}
        onTogglePerplexity={togglePerplexity}
        useBielik={useBielik}
        onToggleModel={toggleModel}
      />

      {error && (
        <div className="mt-2 text-red-500 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
