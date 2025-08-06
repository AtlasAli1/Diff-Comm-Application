import { 
  UsersIcon, 
  UserGroupIcon,
  CurrencyDollarIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: 'users' | 'user-check' | 'currency-dollar' | 'check-circle';
  color: 'blue' | 'green' | 'indigo' | 'purple';
}

const iconMap = {
  'users': UsersIcon,
  'user-check': UserGroupIcon,
  'currency-dollar': CurrencyDollarIcon,
  'check-circle': CheckCircleIcon,
};

const colorMap = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  indigo: 'bg-indigo-500',
  purple: 'bg-purple-500',
};

export default function MetricCard({ title, value, icon, color }: MetricCardProps) {
  const Icon = iconMap[icon];
  const bgColor = colorMap[color];

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`${bgColor} rounded-md p-3`}>
              <Icon className="h-6 w-6 text-white" aria-hidden="true" />
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="text-2xl font-semibold text-gray-900">
                {value}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}