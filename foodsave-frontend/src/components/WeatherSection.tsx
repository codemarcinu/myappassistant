'use client';
import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { ApiService, ApiError } from '@/services/ApiService';
import logger from '../lib/logger';

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

  const fetchWeather = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true);
    setError(null);

    try {
      // Lokacje, dla których chcemy pobrać pogodę
      const locations = ['Ząbki', 'Warszawa'];
      logger.info('Fetching weather for locations:', locations);

      const data = await ApiService.getWeather(locations, signal);
      logger.info('Weather data received:', data);

      setWeatherData(data as WeatherData[]);
    } catch (err) {
      // Check for all possible cancellation/abort error types
      const isCanceled =
        (err instanceof ApiError && (err.code === 'ABORTED' || err.message === 'canceled')) ||
        (err instanceof Error && (err.name === 'AbortError' || err.message === 'canceled' || err.message.includes('canceled')));

      if (isCanceled) {
        logger.info('Weather request was canceled - this is normal during component unmount');
        return;
      }

      // Log as error only for non-cancellation errors
      logger.error('Weather fetch error:', err);
      setError('Nie udało się pobrać danych pogodowych.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;

    const loadWeather = async () => {
      try {
        await fetchWeather(controller.signal);
      } catch (error) {
        if (isMounted) {
          logger.error('Weather loading error:', error);
        }
      }
    };

    loadWeather();

    // Cleanup function to abort request when component unmounts
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [fetchWeather]);

  // DEBUG: Print render state
  logger.debug('Render: isLoading', { isLoading, error, weatherData });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prognoza pogody</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {isLoading && <p>Ładowanie prognozy...</p>}
          {error && weatherData.length === 0 && <p className="text-red-500">{error}</p>}
          {!isLoading && weatherData.length === 0 && !error && (
            <p className="text-gray-500">Brak danych pogodowych</p>
          )}
          {!isLoading && weatherData.length > 0 && weatherData.map((weather: WeatherData) => (
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
