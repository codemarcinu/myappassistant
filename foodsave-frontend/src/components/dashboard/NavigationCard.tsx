import Link from 'next/link';
import { Card } from '../ui/Card';

interface NavigationCardProps {
  title: string;
  href: string;
  icon: string;
  color: string;
  description?: string;
}

export function NavigationCard({
  title,
  href,
  icon,
  color,
  description
}: NavigationCardProps) {
  return (
    <Link href={href} className="block">
      <Card className={`p-6 text-white ${color} hover:opacity-90 transition-all`}>
        <div className="flex flex-col items-center">
          <div className="text-4xl mb-2">{icon}</div>
          <h3 className="text-xl font-semibold">{title}</h3>
          {description && <p className="mt-2 text-sm opacity-90">{description}</p>}
        </div>
      </Card>
    </Link>
  );
}
