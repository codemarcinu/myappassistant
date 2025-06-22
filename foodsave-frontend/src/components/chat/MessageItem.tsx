import ReactMarkdown from 'react-markdown';
import { Card } from '../ui/Card';
import { Message } from '@/types/chat';

interface MessageItemProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageItem({ message, isStreaming = false }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} max-w-[80%]`}>
        <div
          className={`h-8 w-8 rounded-full flex items-center justify-center ${isUser ? 'bg-blue-500' : 'bg-gray-500'} text-white`}
        >
          {isUser ? '👤' : '🤖'}
        </div>
        <Card className={`p-3 mx-2 ${isUser ? 'bg-blue-100' : 'bg-gray-100'}`}>
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-gray-500 ml-1 animate-pulse"></span>
            )}
          </div>
          {message.data && (
            <div className="mt-2 text-xs p-2 bg-white rounded">
              <pre className="whitespace-pre-wrap overflow-auto">
                {typeof message.data === 'object'
                  ? JSON.stringify(message.data, null, 2)
                  : String(message.data)}
              </pre>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
