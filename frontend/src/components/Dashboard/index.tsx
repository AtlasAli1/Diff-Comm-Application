'use client';

import { useQuery } from '@tanstack/react-query';
import { employeeService, payPeriodService, commissionService } from '@/lib/api/services';
import { useAppState } from '@/contexts/AppStateContext';
import MetricCard from './MetricCard';
import RevenueChart from './RevenueChart';
import TopPerformers from './TopPerformers';
import { format } from 'date-fns';

export default function Dashboard() {
  const { currentPayPeriod, revenueData } = useAppState();

  // Fetch employee summary
  const { data: employeeSummary } = useQuery({
    queryKey: ['employeeSummary'],
    queryFn: employeeService.getEmployeeSummary,
  });

  // Fetch pay period stats
  const { data: payPeriodStats } = useQuery({
    queryKey: ['payPeriodStats'],
    queryFn: payPeriodService.getPayPeriodStats,
  });

  // Fetch commission summary for current period
  const { data: commissionSummary } = useQuery({
    queryKey: ['commissionSummary', currentPayPeriod?.id],
    queryFn: () => {
      if (!currentPayPeriod) return null;
      return commissionService.getCommissionSummary({
        start_date: currentPayPeriod.start_date,
        end_date: currentPayPeriod.end_date,
      });
    },
    enabled: !!currentPayPeriod,
  });

  // Calculate revenue for current period
  const currentPeriodRevenue = revenueData
    .filter(item => {
      if (!currentPayPeriod) return false;
      const itemDate = new Date(item.date);
      return itemDate >= new Date(currentPayPeriod.start_date) && 
             itemDate <= new Date(currentPayPeriod.end_date);
    })
    .reduce((sum, item) => sum + (item.revenue || 0), 0);

  return (
    <div className="space-y-6">
      {/* Status Bar */}
      {currentPayPeriod && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-medium text-blue-900">Current Pay Period</h3>
              <p className="text-sm text-blue-700">
                {format(new Date(currentPayPeriod.start_date), 'MMM d')} - {' '}
                {format(new Date(currentPayPeriod.end_date), 'MMM d, yyyy')}
              </p>
            </div>
            <div className="text-right">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                {currentPayPeriod.status}
              </span>
              <p className="text-sm text-gray-600 mt-1">
                Pay Date: {format(new Date(currentPayPeriod.pay_date), 'MMM d, yyyy')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Total Employees"
          value={employeeSummary?.total || 0}
          icon="users"
          color="blue"
        />
        <MetricCard
          title="Active Employees"
          value={employeeSummary?.active || 0}
          icon="user-check"
          color="green"
        />
        <MetricCard
          title="Revenue This Period"
          value={`$${currentPeriodRevenue.toLocaleString()}`}
          icon="currency-dollar"
          color="indigo"
        />
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Revenue Trend (Last 6 Periods)
          </h3>
          <RevenueChart />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Top Performers This Period
          </h3>
          <TopPerformers commissions={commissionSummary?.top_earners || []} />
        </div>
      </div>

      {/* Business Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Business Metrics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {payPeriodStats?.total_periods || 0}
            </p>
            <p className="text-sm text-gray-600">Total Pay Periods</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {payPeriodStats?.completed_periods || 0}
            </p>
            <p className="text-sm text-gray-600">Completed Periods</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              ${(commissionSummary?.average_commission || 0).toLocaleString()}
            </p>
            <p className="text-sm text-gray-600">Avg Commission</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">
              {employeeSummary?.commission_eligible || 0}
            </p>
            <p className="text-sm text-gray-600">Commission Eligible</p>
          </div>
        </div>
      </div>
    </div>
  );
}