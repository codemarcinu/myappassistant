'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { FloatingActionButton } from '@/components/ui/FloatingActionButton';
import { MessageCircle } from 'lucide-react';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const { messages, isLoading, error, sendMessage, usePerplexity, togglePerplexity } = useChat('general');

  return (
    <div className="relative h-[calc(100vh-100px)]">
      <Card className="h-full flex flex-col">
        <CardHeader>
          <CardTitle>Asystent AI</CardTitle>
          {error && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}
        </CardHeader>

        <CardContent className="flex-grow overflow-auto p-4">
          <MessageList messages={messages} isLoading={isLoading} />
        </CardContent>

        <div className="p-4 border-t">
          <MessageInput
            onSendMessage={sendMessage}
            isLoading={isLoading}
            placeholder="Zadaj pytanie lub opisz swój problem..."
            usePerplexity={usePerplexity}
            onTogglePerplexity={togglePerplexity}
          />
        </div>
      </Card>
      <FloatingActionButton
        onClick={() => { /* TODO: Implement new chat functionality */ }}
        icon={MessageCircle}
        label="Nowy czat"
        variant="extended"
      />
    </div>
  );
}
