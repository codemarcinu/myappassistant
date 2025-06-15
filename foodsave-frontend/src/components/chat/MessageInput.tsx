"use client";

import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { MessageInputProps } from '@/types/chat';

export function MessageInput({
  onSendMessage,
  isLoading = false,
  placeholder = "Wpisz wiadomość..."
}: MessageInputProps) {
  const [inputValue, setInputValue] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const message = inputValue.trim();
    if (message && !isLoading) {
      onSendMessage(message);
      setInputValue('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center mt-4">
      <Input
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        placeholder={placeholder}
        className="flex-grow mr-2"
        disabled={isLoading}
      />
      <Button
        type="submit"
        disabled={isLoading || !inputValue.trim()}
        isLoading={isLoading}
      >
        Wyślij
      </Button>
    </form>
  );
}
