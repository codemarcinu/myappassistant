'use client';
import { WeatherSection } from '@/components/WeatherSection';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { LLMModelSettings } from '@/components/dashboard/LLMModelSettings';

export default function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* Sekcja pogodowa */}
      <WeatherSection />

      {/* Ustawienia modeli LLM */}
      <LLMModelSettings />

      {/* Interfejs czatu */}
      <ChatInterface />
    </div>
  );
}
