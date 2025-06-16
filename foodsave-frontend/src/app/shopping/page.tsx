'use client';

import React from 'react';
import { MaterialCard } from '@/components/ui/MaterialCard';
import { ReceiptUploader } from '@/components/shopping/ReceiptUploader';
import { ProductTable } from '@/components/shopping/ProductTable';
import { useShopping } from '@/hooks/useShopping';
import { MessageInput } from '@/components/chat/MessageInput';
import { MessageList } from '@/components/chat/MessageList';
import { useChat } from '@/hooks/useChat';

export default function ShoppingPage() {
  const { products, isLoading: shoppingLoading, error: shoppingError, uploadReceipt, deleteProduct, updateProduct } = useShopping();
  const { messages, isLoading: chatLoading, error: chatError, sendMessage } = useChat();

  const isLoading = shoppingLoading || chatLoading;
  const error = shoppingError || chatError;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      {/* Lewa strona - Zarządzanie zakupami */}
      <div className="space-y-4">
        <MaterialCard>
          <ReceiptUploader onUpload={uploadReceipt} isUploading={shoppingLoading} />
        </MaterialCard>
        <MaterialCard>
          <div className="p-4">
            <h2 className="text-xl font-semibold mb-4">Lista produktów</h2>
            <ProductTable
              products={products}
              isLoading={shoppingLoading}
              onDeleteProduct={deleteProduct}
              onEditProduct={updateProduct}
            />
          </div>
        </MaterialCard>
      </div>

      {/* Prawa strona - Czat zakupowy */}
      <MaterialCard className="flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Asystent zakupowy</h2>
          {error && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}
        </div>
        <div className="flex-grow overflow-auto p-4">
          <MessageList messages={messages} isLoading={chatLoading} />
        </div>
        <div className="p-4 border-t">
          <MessageInput
            onSendMessage={sendMessage}
            isLoading={chatLoading}
            placeholder="Zapytaj o produkty, ceny, paragony..."
          />
        </div>
      </MaterialCard>
    </div>
  );
}
