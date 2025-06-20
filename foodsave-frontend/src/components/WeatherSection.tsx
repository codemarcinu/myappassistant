'use client';
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { ApiService } from '@/services/ApiService';

interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  icon: string;
}

export function WeatherSection() {
  const [weatherData, setWeatherData] = useState<WeatherData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWeather = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Lokacje, dla których chcemy pobrać pogodę
        const locations = ['Ząbki', 'Warszawa'];
        const data = await ApiService.getWeather(locations);
        setWeatherData(data);
      } catch (err) {
        setError('Nie udało się pobrać danych pogodowych.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWeather();
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prognoza pogody</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {isLoading && <p>Ładowanie prognozy...</p>}
          {error && <p className="text-red-500">{error}</p>}
          {!isLoading && !error && weatherData.map((weather: WeatherData) => (
            <div key={weather.location} className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-2xl mr-2">{weather.icon}</span>
                <div>
                  <p className="font-medium">{weather.location}</p>
                  <p className="text-sm text-muted-foreground">{weather.condition}</p>
                </div>
              </div>
              <p className="text-lg font-bold">{weather.temperature ? `${Math.round(weather.temperature)}°C` : 'N/A'}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
