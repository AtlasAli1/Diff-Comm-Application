'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';
import { TrendingUp, Users, Target } from 'lucide-react';

interface CommissionSummary {
  total_commission: number;
  total_employees: number;
  average_commission: number;
  by_type: {
    leadGeneration: number;
    sales: number;
    workDone: number;
  };
}

interface CommissionBreakdownProps {
  commissionData: CommissionSummary | null;
}

// Our specific commission type colors
const COMMISSION_COLORS = {
  leadGeneration: 'hsl(var(--chart-1))', // Blue
  sales: 'hsl(var(--chart-2))',          // Green  
  workDone: 'hsl(var(--chart-3))',       // Orange
};

const COMMISSION_LABELS = {
  leadGeneration: 'Lead Generation',
  sales: 'Sales',
  workDone: 'Work Done',
};

export function CommissionBreakdown({ commissionData }: CommissionBreakdownProps) {
  if (!commissionData || commissionData.total_commission === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="font-medium">No commission breakdown available</p>
        <p className="text-sm mt-1">Calculate commissions to see breakdown by type</p>
      </div>
    );
  }

  // Prepare data for our pie chart based on our 3 commission types
  const chartData = [
    {
      name: COMMISSION_LABELS.leadGeneration,
      value: commissionData.by_type.leadGeneration,
      color: COMMISSION_COLORS.leadGeneration,
    },
    {
      name: COMMISSION_LABELS.sales,
      value: commissionData.by_type.sales,
      color: COMMISSION_COLORS.sales,
    },
    {
      name: COMMISSION_LABELS.workDone,
      value: commissionData.by_type.workDone,
      color: COMMISSION_COLORS.workDone,
    },
  ].filter(item => item.value > 0); // Only show types with commissions

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percentage = ((data.value / commissionData.total_commission) * 100).toFixed(1);
      
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-md">
          <p className="font-medium">{data.name}</p>
          <p className="text-sm text-muted-foreground">
            {formatCurrency(data.value)} ({percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-semibold">{formatCurrency(commissionData.total_commission)}</div>
          <div className="text-xs text-muted-foreground">Total Commissions</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold">{commissionData.total_employees}</div>
          <div className="text-xs text-muted-foreground">Employees</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold">{formatCurrency(commissionData.average_commission)}</div>
          <div className="text-xs text-muted-foreground">Average</div>
        </div>
      </div>

      {chartData.length > 0 ? (
        <>
          {/* Pie Chart */}
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Legend with Details */}
          <div className="space-y-2">
            {chartData.map((item, index) => {
              const percentage = ((item.value / commissionData.total_commission) * 100).toFixed(1);
              
              return (
                <div key={item.name} className="flex items-center justify-between p-2 rounded hover:bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm font-medium">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {percentage}%
                    </Badge>
                    <span className="text-sm font-semibold">
                      {formatCurrency(item.value)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="text-center py-4 text-muted-foreground">
          <p className="text-sm">All commission types are $0</p>
        </div>
      )}

      {/* Commission Type Explanations */}
      <div className="mt-4 p-3 bg-muted/30 rounded-lg">
        <div className="text-sm text-muted-foreground space-y-1">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-3 w-3" />
            <span><strong>Lead Gen:</strong> Commission for bringing in customers</span>
          </div>
          <div className="flex items-center gap-2">
            <Target className="h-3 w-3" />
            <span><strong>Sales:</strong> Commission for closing the sale</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-3 w-3" />
            <span><strong>Work Done:</strong> Commission split among techs performing work</span>
          </div>
        </div>
      </div>
    </div>
  );
}