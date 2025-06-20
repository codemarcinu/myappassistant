'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ReceiptUploader } from '@/components/shopping/ReceiptUploader';
import { ProductTable } from '@/components/shopping/ProductTable';
import { useShopping } from '@/hooks/useShopping';
import { MessageInput } from '@/components/chat/MessageInput';
import { MessageList } from '@/components/chat/MessageList';
import { useChat } from '@/hooks/useChat';

export default function ShoppingPage() {
  const { products, isLoading: shoppingLoading, error: shoppingError, uploadReceipt, deleteProduct, updateProduct } = useShopping();
  const { messages, isLoading: chatLoading, error: chatError, sendMessage, usePerplexity, togglePerplexity } = useChat('shopping');

  const isLoading = shoppingLoading || chatLoading;
  const error = shoppingError || chatError;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      {/* Lewa strona - Zarządzanie zakupami */}
      <div className="space-y-4">
        <Card>
          <ReceiptUploader onUpload={uploadReceipt} isUploading={shoppingLoading} />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Lista produktów</CardTitle>
          </CardHeader>
          <CardContent>
            <ProductTable
              products={products}
              isLoading={shoppingLoading}
              onDeleteProduct={deleteProduct}
              onEditProduct={updateProduct}
            />
          </CardContent>
        </Card>
      </div>

      {/* Prawa strona - Czat zakupowy */}
      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Asystent zakupowy</CardTitle>
          {error && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}
        </CardHeader>
        <CardContent className="flex-grow overflow-auto p-4">
          <MessageList messages={messages} isLoading={chatLoading} />
        </CardContent>
        <div className="p-4 border-t">
          <MessageInput
            onSendMessage={sendMessage}
            isLoading={chatLoading}
            placeholder="Zapytaj o produkty, promocje, lub poproś o listę zakupów..."
            usePerplexity={usePerplexity}
            onTogglePerplexity={togglePerplexity}
          />
        </div>
      </Card>
    </div>
  );
}
