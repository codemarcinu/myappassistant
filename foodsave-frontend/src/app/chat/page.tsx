'use client';

import React from 'react';
import { MaterialCard } from '@/components/ui/MaterialCard';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';
import { MessageCircle } from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const { messages, isLoading, error, sendMessage } = useChat('general');

  return (
    <div className="relative h-[calc(100vh-100px)]">
      <MaterialCard className="h-full flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold">Asystent AI</h1>
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
      </MaterialCard>
      <FloatingActionButton
        onClick={() => { /* TODO: Implement new chat functionality */ }}
        icon={MessageCircle}
        label="Nowy czat"
        variant="extended"
      />
    </div>
  );
}
