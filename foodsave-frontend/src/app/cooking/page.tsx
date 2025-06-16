'use client';

import React from 'react';
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
    <>
      <h1 className="text-3xl font-bold mb-6">Gotowanie</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column: Pantry management */}
        <div>
          <PantryList
            items={pantryItems}
            isLoading={isLoading}
            onAddItem={addPantryItem}
            onDeleteItem={deletePantryItem}
            onUpdateItem={updatePantryItem}
          />
        </div>

        {/* Right column: Cooking assistant */}
        <div>
          <CookingChat
            pantryItems={pantryItems}
            messages={messages}
            isLoading={isLoading}
            onSendMessage={sendCookingMessage}
          />
        </div>
      </div>
    </>
  );
}
