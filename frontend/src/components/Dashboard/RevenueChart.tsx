'use client';

import { useQuery } from '@tanstack/react-query';
import { payPeriodService } from '@/lib/api/services';
import { useAppState } from '@/contexts/AppStateContext';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { format } from 'date-fns';

export default function RevenueChart() {
  const { revenueData } = useAppState();

  // Get last 6 pay periods
  const { data: payPeriods } = useQuery({
    queryKey: ['payPeriodsForChart'],
    queryFn: () => payPeriodService.getPayPeriods({ 
      limit: 6, 
      status: 'Completed' 
    }),
  });

  // Calculate revenue for each period
  const chartData = payPeriods?.items.map(period => {
    const periodRevenue = revenueData
      .filter(item => {
        const itemDate = new Date(item.date);
        return itemDate >= new Date(period.start_date) && 
               itemDate <= new Date(period.end_date);
      })
      .reduce((sum, item) => sum + (item.revenue || 0), 0);

    return {
      period: `${format(new Date(period.start_date), 'MMM d')}`,
      revenue: periodRevenue,
    };
  }).reverse() || [];

  if (chartData.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No revenue data available.</p>
        <p className="text-sm mt-2">Upload revenue data to see trends.</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="period" />
        <YAxis 
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip 
          formatter={(value: number) => `$${value.toLocaleString()}`}
        />
        <Line 
          type="monotone" 
          dataKey="revenue" 
          stroke="#3B82F6" 
          strokeWidth={2}
          dot={{ fill: '#3B82F6' }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}