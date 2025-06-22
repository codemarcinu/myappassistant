"use client";

import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { ReceiptUploaderProps } from '@/types/shopping';

export function ReceiptUploader({
  onUpload,
  isUploading
}: ReceiptUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (file.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(file));
      } else {
        setPreviewUrl(null);
      }
      setIsConfirming(true);
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      await onUpload(selectedFile);
      setSelectedFile(null);
      setPreviewUrl(null);
      setIsConfirming(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setIsConfirming(false);
  };

  return (
    <Card className="p-4 mb-6">
      <h3 className="text-lg font-semibold mb-3">Wgraj paragon</h3>
      {!isConfirming ? (
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="file"
            accept=".jpg,.jpeg,.png,.pdf"
            onChange={handleFileChange}
            className="flex-grow"
            disabled={isUploading}
          />
        </div>
      ) : (
        <div className="mt-4">
          <div className="mb-4">
            <p className="text-sm mb-2">Wybrany plik: {selectedFile?.name}</p>
            <div className="border rounded-md overflow-hidden mb-4 max-h-96">
              {selectedFile && selectedFile.type.startsWith('image/') && previewUrl ? (
                <img src={previewUrl} alt="Podgląd" className="w-full object-contain" />
              ) : (
                <div className="p-4 bg-gray-100 text-center">
                  <p>Podgląd niedostępny dla plików PDF</p>
                </div>
              )}
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleUpload}
                disabled={isUploading}
                isLoading={isUploading}
              >
                {isUploading ? 'Przetwarzanie...' : 'Zatwierdź i prześlij'}
              </Button>
              <Button
                variant="secondary"
                onClick={handleCancel}
                disabled={isUploading}
              >
                Anuluj
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
