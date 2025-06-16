'use client';
import { MaterialCard } from '@/components/ui/MaterialCard';
import { MaterialButton } from '@/components/ui/MaterialButton';
import { WeatherSection } from '@/components/WeatherSection';

export default function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* Sekcja pogodowa */}
      <WeatherSection />

      {/* Główne przyciski nawigacyjne */}
      <MaterialCard className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MaterialButton className="shadow-md rounded-lg text-lg h-12">
            Czat Ogólny
          </MaterialButton>
          <MaterialButton className="shadow-md rounded-lg text-lg h-12">
            Zakupy
          </MaterialButton>
          <MaterialButton className="shadow-md rounded-lg text-lg h-12">
            Gotowanie
          </MaterialButton>
        </div>
      </MaterialCard>
    </div>
  );
}
