'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { PantryList } from '@/components/cooking/PantryList';
import { CookingChat } from '@/components/cooking/CookingChat';
import { useCooking } from '@/hooks/useCooking';

export default function CookingPage() {
  const {
    pantryItems,
    isLoading,
    error,
    addPantryItem,
    updatePantryItem,
    deletePantryItem,
    messages,
    sendCookingMessage,
    usePerplexity,
    togglePerplexity,
  } = useCooking();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      {/* Lewa strona - Zarządzanie spiżarnią */}
      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Moja Spiżarnia</CardTitle>
        </CardHeader>
        <CardContent className="flex-grow">
          <PantryList
            items={pantryItems || []}
            onAddItem={addPantryItem}
            onUpdateItem={updatePantryItem}
            onDeleteItem={deletePantryItem}
          />
        </CardContent>
      </Card>

      {/* Prawa strona - Czat o gotowaniu */}
      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Asystent Gotowania</CardTitle>
        </CardHeader>
        <CardContent className="flex-grow">
          <CookingChat
            pantryItems={pantryItems}
            onSendMessage={sendCookingMessage}
            messages={messages}
            isLoading={isLoading}
            usePerplexity={usePerplexity}
            onTogglePerplexity={togglePerplexity}
          />
        </CardContent>
      </Card>
    </div>
  );
}
