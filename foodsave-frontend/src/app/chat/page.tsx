'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const { messages, isLoading, error, sendMessage } = useChat();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Asystent AI</h1>

      <Card className="min-h-[calc(100vh-200px)] flex flex-col">
        <div className="p-4 border-b">
          {error && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}
        </div>

        <div className="flex-grow overflow-auto p-4">
          <MessageList messages={messages} isLoading={isLoading} />
        </div>

        <div className="p-4 border-t">
          <MessageInput
            onSendMessage={sendMessage}
            isLoading={isLoading}
            placeholder="Zadaj pytanie lub opisz swój problem..."
          />
        </div>
      </Card>
    </div>
  );
}
