import { Card } from '../ui/Card';
import { WeatherData } from '@/types/api';

interface WeatherWidgetProps {
  data: WeatherData;
  isLoading?: boolean;
}

export function WeatherWidget({
  data,
  isLoading = false
}: WeatherWidgetProps) {
  if (isLoading) {
    return <Card className="p-4 h-40 animate-pulse" />;
  }

  return (
    <Card className="p-4 mb-4">
      <h2 className="text-xl font-semibold">{data.location}</h2>
      <div className="flex items-center mt-2">
        <div className="text-4xl font-bold mr-2">{data.temperature}°C</div>
        <div>
          <div>{data.condition}</div>
          <div className="text-sm text-gray-500">
            H: {data.highTemp}° L: {data.lowTemp}°
          </div>
        </div>
      </div>
    </Card>
  );
}
