import React from 'react';
import { MessageItem } from './MessageItem';
import { MessageListProps } from '@/types/chat';

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false
}) => {
  return (
    <div className="flex flex-col space-y-4">
      {messages.map((message, index) => (
        <MessageItem key={index} message={message} />
      ))}

      {isLoading && (
        <div className="flex justify-start mb-4">
          <div className="flex max-w-[80%]">
            <div className="h-8 w-8 rounded-full flex items-center justify-center bg-gray-500 text-white">
              🤖
            </div>
            <div className="bg-gray-100 p-3 mx-2 rounded-lg">
              <div className="flex space-x-2">
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
