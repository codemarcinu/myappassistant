'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ReceiptUploader } from '@/components/shopping/ReceiptUploader';
import { ProductTable } from '@/components/shopping/ProductTable';
import { useShopping } from '@/hooks/useShopping';
import { MessageInput } from '@/components/chat/MessageInput';
import { MessageList } from '@/components/chat/MessageList';
import { useChat } from '@/hooks/useChat';
import { ReceiptDataTable } from '@/components/shopping/ReceiptDataTable';
import { ApiService } from '@/services/ApiService';
import { Product } from '@/types/shopping';

export default function ShoppingPage() {
  const { products, isLoading: shoppingLoading, error: shoppingError, fetchProducts } = useShopping();
  const { messages, isLoading: chatLoading, error: chatError, sendMessage } = useChat('shopping');

  const [processingStep, setProcessingStep] = useState<'upload' | 'ocr' | 'analyze' | 'edit' | 'saving' | 'done'>('upload');
  const [ocrText, setOcrText] = useState<string | null>(null);
  const [analyzedProducts, setAnalyzedProducts] = useState<Product[]>([]);
  const [receiptMeta, setReceiptMeta] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const isLoading = shoppingLoading || chatLoading || processingStep === 'ocr' || processingStep === 'analyze' || processingStep === 'saving';

  const handleFileUpload = async (file: File) => {
    setError(null);
    setProcessingStep('ocr');
    try {
      // 1. OCR
      const ocrRes: any = await ApiService.uploadReceipt(file);
      const ocrText = ocrRes?.data?.text || '';
      setOcrText(ocrText);
      setProcessingStep('analyze');
      // 2. Analiza
      const analyzeRes: any = await ApiService.analyzeReceipt(ocrText);
      const data = analyzeRes?.data || {};
      setAnalyzedProducts(data.items || []);
      setReceiptMeta({
        store: data.store_name,
        date: data.date,
        total: data.total,
      });
      setProcessingStep('edit');
    } catch (err: any) {
      setError(err?.message || 'Błąd podczas przetwarzania paragonu');
      setProcessingStep('upload');
    }
  };

  const handleSaveProducts = async (editedProducts: Product[]) => {
    setProcessingStep('saving');
    setError(null);
    try {
      // 3. Zapis do bazy
      const payload = {
        trip_date: receiptMeta?.date || new Date().toISOString().slice(0, 10),
        store_name: receiptMeta?.store || 'Nieznany sklep',
        total_amount: receiptMeta?.total || 0,
        products: editedProducts.map(p => ({
          name: p.name,
          quantity: p.quantity,
          unit: p.unit,
          price: p.price,
          category: p.category,
          expiry_date: p.expiry_date || null,
        })),
      };
      await ApiService.saveReceiptData(payload);
      setProcessingStep('done');
      await fetchProducts();
      setTimeout(() => {
        setProcessingStep('upload');
        setOcrText(null);
        setAnalyzedProducts([]);
        setReceiptMeta(null);
      }, 2000);
    } catch (err: any) {
      setError(err?.message || 'Błąd podczas zapisu produktów');
      setProcessingStep('edit');
    }
  };

  const handleCancelEdit = () => {
    setProcessingStep('upload');
    setOcrText(null);
    setAnalyzedProducts([]);
    setReceiptMeta(null);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      {/* Lewa strona - Zarządzanie zakupami */}
      <div className="space-y-4">
        <Card>
          {processingStep === 'upload' && (
            <ReceiptUploader
              onUpload={handleFileUpload}
              isUploading={isLoading}
            />
          )}
          {processingStep === 'ocr' && (
            <div className="p-4 text-center">Wykonywanie OCR...</div>
          )}
          {processingStep === 'analyze' && (
            <div className="p-4 text-center">Analiza paragonu...</div>
          )}
          {processingStep === 'edit' && analyzedProducts.length > 0 && (
            <ReceiptDataTable
              products={analyzedProducts}
              onSave={handleSaveProducts}
              onCancel={handleCancelEdit}
            />
          )}
          {processingStep === 'saving' && (
            <div className="p-4 text-center">Zapisywanie produktów...</div>
          )}
          {processingStep === 'done' && (
            <div className="p-4 text-center text-green-600">Produkty zostały zapisane!</div>
          )}
          {error && (
            <div className="p-4 text-center text-red-600">{error}</div>
          )}
        </Card>
        {processingStep === 'upload' && (
          <Card>
            <CardHeader>
              <CardTitle>Lista produktów</CardTitle>
            </CardHeader>
            <CardContent>
              <ProductTable
                products={products}
                isLoading={shoppingLoading}
              />
            </CardContent>
          </Card>
        )}
      </div>
      {/* Prawa strona - Czat zakupowy */}
      <Card className="flex flex-col">
        <CardHeader>
          <CardTitle>Asystent zakupowy</CardTitle>
          {(shoppingError || chatError) && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 rounded">
              {shoppingError || chatError}
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
          />
        </div>
      </Card>
    </div>
  );
}
