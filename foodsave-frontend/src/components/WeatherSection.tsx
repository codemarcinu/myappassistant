'use client';
import { useEffect, useState } from 'react';
import { MaterialCard } from './ui/MaterialCard';

interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  icon: string;
}

export function WeatherSection() {
  const [weatherData, setWeatherData] = useState<WeatherData[]>([]);

  // Mock data for now
  useEffect(() => {
    setWeatherData([
      { location: 'Ząbki', temperature: 18, condition: 'Słonecznie', icon: '☀️' },
      { location: 'Warszawa', temperature: 17, condition: 'Częściowe zachmurzenie', icon: '⛅️' },
    ]);
  }, []);

  return (
    <MaterialCard className="p-4">
      <h2 className="text-lg font-semibold mb-2">Prognoza pogody</h2>
      <div className="space-y-2">
        {weatherData.map((weather: WeatherData) => (
          <div key={weather.location} className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-2">{weather.icon}</span>
              <div>
                <p className="font-medium">{weather.location}</p>
                <p className="text-sm text-muted-foreground">{weather.condition}</p>
              </div>
            </div>
            <p className="text-lg font-bold">{weather.temperature}°C</p>
          </div>
        ))}
      </div>
    </MaterialCard>
  );
}
