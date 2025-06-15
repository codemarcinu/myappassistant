'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';
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
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Zakupy</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column: Shopping management */}
        <div>
          <ReceiptUploader onUpload={uploadReceipt} isUploading={shoppingLoading} />

          <Card className="mb-6">
            <div className="p-4 border-b">
              <h2 className="text-xl font-semibold">Lista produktów</h2>
            </div>
            <div className="p-4">
              <ProductTable
                products={products}
                isLoading={shoppingLoading}
                onDeleteProduct={deleteProduct}
                onEditProduct={updateProduct}
              />
            </div>
          </Card>
        </div>

        {/* Right column: Shopping chat */}
        <Card className="min-h-[calc(100vh-200px)] flex flex-col">
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
        </Card>
      </div>
    </div>
  );
}
