import { Suspense } from 'react';
import { WeatherWidget } from '@/components/dashboard/WeatherWidget';
import { NavigationCard } from '@/components/dashboard/NavigationCard';
import { fetchWeatherData } from '@/services/ApiService';

async function Dashboard() {
  // Data fetching using Next.js Server Components
  const zabkiWeather = await fetchWeatherData('Ząbki');
  const warsawWeather = await fetchWeatherData('Warsaw');

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">FoodSave AI Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <Suspense fallback={<WeatherWidget data={{} as any} isLoading={true} />}>
          <WeatherWidget data={zabkiWeather} />
        </Suspense>
        <Suspense fallback={<WeatherWidget data={{} as any} isLoading={true} />}>
          <WeatherWidget data={warsawWeather} />
        </Suspense>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NavigationCard
          title="Chat"
          href="/chat"
          icon="💬"
          color="bg-blue-600"
          description="Porozmawiaj z asystentem AI"
        />
        <NavigationCard
          title="Shopping"
          href="/shopping"
          icon="🛒"
          color="bg-green-600"
          description="Zarządzaj swoimi zakupami"
        />
        <NavigationCard
          title="Cooking"
          href="/cooking"
          icon="👨‍🍳"
          color="bg-orange-600"
          description="Znajdź przepisy i zarządzaj spiżarnią"
        />
      </div>
    </div>
  );
}

export default Dashboard;
