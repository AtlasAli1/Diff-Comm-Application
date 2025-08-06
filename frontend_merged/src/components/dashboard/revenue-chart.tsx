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
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { formatCurrency, formatPayPeriodRange } from '@/lib/utils';

export function RevenueChart() {
  const { revenueData, currentPayPeriod } = useAppState();

  // Get last 6 completed pay periods for trend analysis
  const { data: payPeriods, isLoading } = useQuery({
    queryKey: ['payPeriodsForChart'],
    queryFn: () => payPeriodService.getPayPeriods({ 
      limit: 8, // Get more to ensure we have enough data
    }),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[300px]">
        <div className="animate-pulse text-muted-foreground">Loading revenue data...</div>
      </div>
    );
  }

  if (!payPeriods?.items || payPeriods.items.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-center">
        <div className="text-muted-foreground">
          <p>No pay periods available</p>
          <p className="text-sm mt-1">Configure pay periods in Company Setup</p>
        </div>
      </div>
    );
  }

  // Calculate revenue for each period from our uploaded data
  const chartData = payPeriods.items
    .slice(0, 6) // Show last 6 periods
    .map(period => {
      const periodRevenue = revenueData
        .filter(item => {
          const itemDate = new Date(item.date);
          return itemDate >= new Date(period.start_date) && 
                 itemDate <= new Date(period.end_date);
        })
        .reduce((sum, item) => sum + (parseFloat(item.revenue) || 0), 0);

      return {
        period: `Period ${period.period_number}`,
        periodRange: formatPayPeriodRange(period.start_date, period.end_date),
        revenue: periodRevenue,
        isCurrentPeriod: currentPayPeriod?.id === period.id,
        periodId: period.id,
      };
    })
    .reverse(); // Show chronologically

  if (chartData.every(item => item.revenue === 0)) {
    return (
      <div className="flex items-center justify-center h-[300px] text-center">
        <div className="text-muted-foreground">
          <p>No revenue data uploaded</p>
          <p className="text-sm mt-1">Upload revenue data in Data Management</p>
        </div>
      </div>
    );
  }

  const maxRevenue = Math.max(...chartData.map(item => item.revenue));
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
        <XAxis 
          dataKey="period" 
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis 
          tickFormatter={(value) => {
            if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
            return `$${value}`;
          }}
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip 
          formatter={(value: number) => [formatCurrency(value), 'Revenue']}
          labelFormatter={(label, payload) => {
            const data = payload?.[0]?.payload;
            return data ? `${label}: ${data.periodRange}` : label;
          }}
          contentStyle={{
            backgroundColor: 'var(--background)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
          }}
        />
        
        {/* Highlight current period */}
        {chartData.find(item => item.isCurrentPeriod) && (
          <ReferenceLine 
            x={chartData.find(item => item.isCurrentPeriod)?.period} 
            stroke="hsl(var(--primary))" 
            strokeWidth={2}
            strokeDasharray="4 4"
          />
        )}
        
        <Line 
          type="monotone" 
          dataKey="revenue" 
          stroke="hsl(var(--primary))" 
          strokeWidth={3}
          dot={(props) => {
            const { cx, cy, payload } = props;
            return (
              <circle
                cx={cx}
                cy={cy}
                r={payload.isCurrentPeriod ? 6 : 4}
                fill={payload.isCurrentPeriod ? "hsl(var(--primary))" : "hsl(var(--primary))"}
                stroke={payload.isCurrentPeriod ? "hsl(var(--background))" : "transparent"}
                strokeWidth={payload.isCurrentPeriod ? 2 : 0}
              />
            );
          }}
          activeDot={{ r: 6, stroke: 'hsl(var(--primary))', strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}