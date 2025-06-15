import { Card } from '../ui/Card';
import { MessageList } from '../chat/MessageList';
import { MessageInput } from '../chat/MessageInput';
import { Message } from '@/types/chat';
import { CookingChatProps } from '@/types/cooking';

export function CookingChat({
  pantryItems,
  onSendMessage,
  messages,
  isLoading = false
}: CookingChatProps) {
  return (
    <Card className="h-[calc(100vh-200px)] flex flex-col">
      <div className="p-4 border-b">
        <h2 className="text-xl font-semibold">Asystent kulinarny</h2>
        <p className="text-sm text-gray-500 mt-1">
          Masz {pantryItems.length} {pantryItems.length === 1 ? 'produkt' : 'produktów'} w spiżarni
        </p>
      </div>

      <div className="flex-grow overflow-auto p-4">
        <MessageList messages={messages} isLoading={isLoading} />
      </div>

      <div className="p-4 border-t">
        <MessageInput
          onSendMessage={onSendMessage}
          isLoading={isLoading}
          placeholder="Zapytaj o przepisy, pomysły na obiad..."
        />
      </div>
    </Card>
  );
};
