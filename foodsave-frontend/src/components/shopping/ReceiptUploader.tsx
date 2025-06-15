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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (selectedFile) {
      await onUpload(selectedFile);
      setSelectedFile(null);
    }
  };

  return (
    <Card className="p-4 mb-6">
      <h3 className="text-lg font-semibold mb-3">Wgraj paragon</h3>
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={handleFileChange}
          className="flex-grow"
          disabled={isUploading}
        />
        <Button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          isLoading={isUploading}
        >
          {isUploading ? 'Przetwarzanie...' : 'Wgraj'}
        </Button>
      </div>
      {selectedFile && (
        <div className="mt-2 text-sm">
          Wybrany plik: {selectedFile.name}
        </div>
      )}
    </Card>
  );
}
