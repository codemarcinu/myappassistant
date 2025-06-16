'use client';

import React from 'react';
import { MaterialCard } from '@/components/ui/MaterialCard';
import { PantryList } from '@/components/cooking/PantryList';
import { CookingChat } from '@/components/cooking/CookingChat';
import { useCooking } from '@/hooks/useCooking';

export default function CookingPage() {
  const {
    pantryItems,
    messages,
    isLoading,
    error,
    addPantryItem,
    deletePantryItem,
    updatePantryItem,
    sendCookingMessage
  } = useCooking();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      {/* Lewa strona - Spiżarnia */}
      <MaterialCard className="flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Twoja spiżarnia</h2>
        </div>
        <div className="p-4 flex-grow">
          <PantryList
            items={pantryItems}
            isLoading={isLoading}
            onAddItem={addPantryItem}
            onDeleteItem={deletePantryItem}
            onUpdateItem={updatePantryItem}
          />
        </div>
      </MaterialCard>

      {/* Prawa strona - Chat kulinarny */}
      <MaterialCard className="flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Agent kulinarny</h2>
        </div>
        <div className="p-4 flex-grow">
          <CookingChat
            pantryItems={pantryItems}
            messages={messages}
            isLoading={isLoading}
            onSendMessage={sendCookingMessage}
          />
        </div>
         {error && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}
      </MaterialCard>
    </div>
  );
}
