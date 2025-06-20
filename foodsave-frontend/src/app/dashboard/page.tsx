'use client';
import { WeatherSection } from '@/components/WeatherSection';
import { ChatInterface } from '@/components/chat/ChatInterface';

export default function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* Sekcja pogodowa */}
      <WeatherSection />

      {/* Interfejs czatu */}
      <ChatInterface />
    </div>
  );
}
