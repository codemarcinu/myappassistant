"use client";

import React, { useState } from 'react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { MessageInputProps } from '@/types/chat';
import { Search, Sparkles, Cpu } from 'lucide-react';

export function MessageInput({
  onSendMessage,
  isLoading = false,
  placeholder = "Wpisz wiadomość...",
  usePerplexity = false,
  onTogglePerplexity,
  useBielik = true,
  onToggleModel
}: MessageInputProps) {
  const [inputValue, setInputValue] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const message = inputValue.trim();
    if (message && !isLoading) {
      onSendMessage(message, usePerplexity, useBielik);
      setInputValue('');
    }
  };

  const handleTogglePerplexity = () => {
    if (onTogglePerplexity) {
      onTogglePerplexity();
    }
  };

  const handleToggleModel = () => {
    if (onToggleModel) {
      onToggleModel();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center mt-4">
      <div className="flex-grow mr-2 relative">
        <Input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          placeholder={placeholder}
          className="pr-20"
          disabled={isLoading}
        />
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex space-x-1">
          {/* Model toggle button */}
          <button
            type="button"
            onClick={handleToggleModel}
            className={`p-1 rounded-full transition-all duration-200 ${
              useBielik
                ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                : 'bg-green-100 text-green-600 hover:bg-green-200'
            }`}
            title={useBielik ? 'Przełącz na Gemma' : 'Przełącz na Bielik'}
          >
            <Cpu size={16} />
          </button>
          {/* Perplexity toggle button */}
          <button
            type="button"
            onClick={handleTogglePerplexity}
            className={`p-1 rounded-full transition-all duration-200 ${
              usePerplexity
                ? 'bg-purple-100 text-purple-600 hover:bg-purple-200'
                : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'
            }`}
            title={usePerplexity ? 'Wyłącz Perplexity (użyj lokalnych modeli)' : 'Włącz Perplexity (użyj modeli online)'}
          >
            <Sparkles size={16} />
          </button>
        </div>
      </div>
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
