'use client';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/utils';
import { Trophy, Award, Medal } from 'lucide-react';

interface TopPerformer {
  employee_id: number;
  employee_name: string;
  amount: number;
}

interface TopPerformersChartProps {
  commissions: TopPerformer[];
}

export function TopPerformersChart({ commissions }: TopPerformersChartProps) {
  if (!commissions || commissions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Award className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="font-medium">No commission data available</p>
        <p className="text-sm mt-1">Calculate commissions to see top performers</p>
      </div>
    );
  }

  // Get initials for avatar
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase();
  };

  // Get ranking icon
  const getRankingIcon = (index: number) => {
    switch (index) {
      case 0:
        return <Trophy className="h-4 w-4 text-yellow-500" />;
      case 1:
        return <Award className="h-4 w-4 text-gray-400" />;
      case 2:
        return <Medal className="h-4 w-4 text-amber-600" />;
      default:
        return <div className="h-4 w-4 flex items-center justify-center text-sm font-semibold text-muted-foreground">#{index + 1}</div>;
    }
  };

  // Calculate percentage of top performer for progress bars
  const topAmount = Math.max(...commissions.map(p => p.amount));

  return (
    <div className="space-y-4">
      {commissions.slice(0, 5).map((performer, index) => {
        const percentage = topAmount > 0 ? (performer.amount / topAmount) * 100 : 0;
        
        return (
          <div key={performer.employee_id} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-muted/50 transition-colors">
            {/* Ranking */}
            <div className="flex-shrink-0 w-8 flex justify-center">
              {getRankingIcon(index)}
            </div>

            {/* Avatar */}
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs font-semibold">
                {getInitials(performer.employee_name)}
              </AvatarFallback>
            </Avatar>

            {/* Employee Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium truncate">
                  {performer.employee_name}
                </p>
                <Badge 
                  variant={index === 0 ? "default" : "secondary"}
                  className="text-xs"
                >
                  {formatCurrency(performer.amount)}
                </Badge>
              </div>
              
              {/* Progress bar showing relative performance */}
              <div className="w-full bg-muted rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    index === 0 ? 'bg-primary' : 'bg-muted-foreground'
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              
              <p className="text-xs text-muted-foreground mt-1">
                Employee ID: {performer.employee_id} • {percentage.toFixed(1)}% of top
              </p>
            </div>
          </div>
        );
      })}

      {/* Summary */}
      {commissions.length > 5 && (
        <div className="mt-4 p-3 bg-muted/30 rounded-lg text-center">
          <p className="text-sm text-muted-foreground">
            +{commissions.length - 5} more employees with commissions
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Total: {formatCurrency(commissions.reduce((sum, p) => sum + p.amount, 0))}
          </p>
        </div>
      )}
    </div>
  );
}