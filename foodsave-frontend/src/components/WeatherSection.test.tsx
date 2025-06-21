import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { WeatherSection } from './WeatherSection';
import * as ApiServiceModule from '../services/ApiService';

describe('WeatherSection', () => {
  beforeAll(() => {
    // Mock crypto.randomUUID
    Object.defineProperty(globalThis, 'crypto', {
      value: { randomUUID: () => 'mock-uuid' },
      configurable: true,
    });
  });

  it('renderuje nagłówek i sekcję pogodową', async () => {
    jest.spyOn(ApiServiceModule.ApiService, 'getWeather').mockResolvedValue([
      { location: 'Warszawa', temperature: 20, description: 'Słonecznie', icon: '01d' },
    ]);
    render(<WeatherSection />);
    expect(screen.getByText('Prognoza pogody')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Warszawa/i)).toBeInTheDocument();
    });
  });
});
