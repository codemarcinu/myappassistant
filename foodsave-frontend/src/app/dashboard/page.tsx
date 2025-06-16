import { WeatherWidget } from '@/components/dashboard/WeatherWidget';
import { NavigationCard } from '@/components/dashboard/NavigationCard';
import { fetchWeatherData } from '@/services/ApiService';

// Mock weather data for when the API is unavailable
const mockWeatherData = {
  location: "Sample Location",
  temperature: 22,
  condition: "Partly Cloudy",
  highTemp: 25,
  lowTemp: 18,
  humidity: 65,
  windSpeed: 10
};

async function Dashboard() {
  // Data fetching using Next.js Server Components with error handling
  let zabkiWeather;
  let warsawWeather;

  try {
    zabkiWeather = await fetchWeatherData('Ząbki');
  } catch (error) {
    console.error('Failed to fetch Ząbki weather:', error);
    zabkiWeather = { ...mockWeatherData, location: 'Ząbki' };
  }

  try {
    warsawWeather = await fetchWeatherData('Warsaw');
  } catch (error) {
    console.error('Failed to fetch Warsaw weather:', error);
    warsawWeather = { ...mockWeatherData, location: 'Warsaw' };
  }

  return (
    <>
      <h1 className="text-3xl font-bold mb-6">Panel FoodSave AI</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <WeatherWidget data={zabkiWeather} />
        <WeatherWidget data={warsawWeather} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NavigationCard
          title="Czat"
          href="/chat"
          icon="💬"
          color="bg-blue-600"
          description="Porozmawiaj z asystentem AI"
        />
        <NavigationCard
          title="Zakupy"
          href="/shopping"
          icon="🛒"
          color="bg-green-600"
          description="Zarządzaj swoimi zakupami"
        />
        <NavigationCard
          title="Gotowanie"
          href="/cooking"
          icon="👨‍🍳"
          color="bg-orange-600"
          description="Znajdź przepisy i zarządzaj spiżarnią"
        />
      </div>
    </>
  );
}

export default Dashboard;
