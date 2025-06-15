"use client";

import { useState } from 'react';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { PantryItem, PantryListProps } from '@/types/cooking';

export function PantryList({
  items,
  isLoading = false,
  onAddItem,
  onDeleteItem,
  onUpdateItem
}: PantryListProps) {
  const [newItem, setNewItem] = useState('');

  const handleAddItem = async () => {
    if (newItem.trim() && onAddItem) {
      await onAddItem({ name: newItem, unified_category: 'Nieskategoryzowane' });
      setNewItem('');
    }
  };

  if (isLoading) {
    return <Card className="h-[calc(100vh-200px)] animate-pulse" />;
  }

  return (
    <Card className="h-[calc(100vh-200px)] overflow-auto">
      <div className="p-4 border-b">
        <h2 className="text-xl font-semibold mb-4">Moja Spiżarnia</h2>
        <div className="flex gap-2">
          <Input
            type="text"
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            placeholder="Dodaj nowy produkt..."
            className="flex-grow"
          />
          <Button onClick={handleAddItem} disabled={!newItem.trim()}>
            Dodaj
          </Button>
        </div>
      </div>

      <div className="divide-y">
        {items.map((item) => (
          <div key={item.id} className="p-3 hover:bg-gray-50">
            <div className="flex justify-between items-center">
              <div>
                <div className="font-medium">{item.name}</div>
                <div className="text-sm text-gray-500">{item.unified_category}</div>
              </div>
              <div className="flex gap-2">
                {onUpdateItem && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onUpdateItem(item.id, {})}
                  >
                    Edytuj
                  </Button>
                )}
                {onDeleteItem && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDeleteItem(item.id)}
                  >
                    Usuń
                  </Button>
                )}
              </div>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <div className="p-4 text-center text-gray-500">
            Twoja spiżarnia jest pusta
          </div>
        )}
      </div>
    </Card>
  );
}
