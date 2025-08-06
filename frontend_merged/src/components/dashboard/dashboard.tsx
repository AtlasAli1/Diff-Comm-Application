'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { TrendingUp, TrendingDown, DollarSign, Users, Calendar, Target, Award, Clock, ArrowUpRight, ArrowDownRight, Calculator, AlertTriangle, CheckCircle } from 'lucide-react'
import { RevenueChart } from './revenue-chart'
import { TopPerformersChart } from './top-performers-chart'
import { CommissionBreakdown } from './commission-breakdown'
import { useQuery } from '@tanstack/react-query'
import { employeeService, payPeriodService, commissionService } from '@/lib/api/services'
import { useAppState } from '@/contexts/AppStateContext'
import { formatCurrency, formatPayPeriodRange } from '@/lib/utils'
import { format } from 'date-fns'

export function Dashboard() {
  const { currentPayPeriod, revenueData, uploadStatus, commissionResults } = useAppState()

  // Get real employee summary from our API
  const { data: employeeSummary } = useQuery({
    queryKey: ['employeeSummary'],
    queryFn: employeeService.getEmployeeSummary,
  });

  // Get pay period stats
  const { data: payPeriodStats } = useQuery({
    queryKey: ['payPeriodStats'],
    queryFn: payPeriodService.getPayPeriodStats,
  });

  // Get commission summary for current period
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

  // Calculate current period revenue from our data
  const currentPeriodRevenue = revenueData
    .filter(item => {
      if (!currentPayPeriod) return false;
      const itemDate = new Date(item.date);
      return itemDate >= new Date(currentPayPeriod.start_date) && 
             itemDate <= new Date(currentPayPeriod.end_date);
    })
    .reduce((sum, item) => sum + (parseFloat(item.revenue) || 0), 0);

  // Our real business metrics
  const metrics = [
    {
      title: 'Total Revenue',
      value: formatCurrency(currentPeriodRevenue),
      change: currentPeriodRevenue > 0 ? '+' + ((currentPeriodRevenue / 100000) * 100).toFixed(1) + '%' : '0%',
      trend: currentPeriodRevenue > 0 ? 'up' : 'down',
      icon: DollarSign,
      description: currentPayPeriod ? 'This pay period' : 'No period selected'
    },
    {
      title: 'Total Commissions',
      value: formatCurrency(commissionSummary?.total_commission || 0),
      change: commissionSummary ? '+' + ((commissionSummary.total_commission / currentPeriodRevenue * 100) || 0).toFixed(1) + '%' : '0%',
      trend: commissionSummary ? 'up' : 'down',
      icon: Target,
      description: currentPayPeriod ? 'This pay period' : 'No period selected'
    },
    {
      title: 'Active Employees',
      value: employeeSummary?.active?.toString() || '0',
      change: employeeSummary ? `+${employeeSummary.efficiency_pay_count} efficiency` : '0',
      trend: 'up',
      icon: Users,
      description: `${employeeSummary?.commission_eligible || 0} commission eligible`
    },
    {
      title: 'Avg Commission Rate',
      value: commissionSummary && currentPeriodRevenue > 0 
        ? ((commissionSummary.total_commission / currentPeriodRevenue) * 100).toFixed(1) + '%'
        : '0%',
      change: commissionSummary ? 'Calculated' : 'Not calculated',
      trend: commissionSummary ? 'up' : 'down',
      icon: Award,
      description: 'Based on current data'
    },
  ];

  // System readiness check
  const getSystemReadiness = () => {
    let readyCount = 0;
    let totalChecks = 4;
    
    if (currentPayPeriod) readyCount++;
    if (employeeSummary && employeeSummary.active > 0) readyCount++;
    if (uploadStatus.timesheetUploaded) readyCount++;
    if (uploadStatus.revenueUploaded) readyCount++;
    
    return (readyCount / totalChecks) * 100;
  };

  const systemReadiness = getSystemReadiness();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            {currentPayPeriod 
              ? `Commission overview for ${formatPayPeriodRange(currentPayPeriod.start_date, currentPayPeriod.end_date)}`
              : 'Select a pay period to view commission data'
            }
          </p>
        </div>
        <div className="flex items-center gap-2">
          {currentPayPeriod ? (
            <Badge variant="outline" className="gap-1">
              <Clock className="h-3 w-3" />
              Period #{currentPayPeriod.period_number}
            </Badge>
          ) : (
            <Badge variant="destructive" className="gap-1">
              <AlertTriangle className="h-3 w-3" />
              No Pay Period
            </Badge>
          )}
          
          <Button disabled={!currentPayPeriod || !uploadStatus.revenueUploaded}>
            <Calculator className="h-4 w-4 mr-2" />
            Calculate Commissions
          </Button>
        </div>
      </div>

      {/* System Readiness Alert */}
      {systemReadiness < 100 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <div>
                <strong>System Setup: {systemReadiness.toFixed(0)}% Complete</strong>
                <div className="text-sm mt-1">
                  {!currentPayPeriod && "• Configure pay periods in Company Setup"}
                  {employeeSummary?.active === 0 && "• Add employees in Company Setup"}
                  {!uploadStatus.timesheetUploaded && "• Upload timesheet data"}
                  {!uploadStatus.revenueUploaded && "• Upload revenue data"}
                </div>
              </div>
              <Progress value={systemReadiness} className="w-32" />
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Real Business Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
              <metric.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center text-xs text-muted-foreground">
                {metric.trend === 'up' && currentPeriodRevenue > 0 ? (
                  <ArrowUpRight className="mr-1 h-3 w-3 text-green-500" />
                ) : (
                  <ArrowDownRight className="mr-1 h-3 w-3 text-red-500" />
                )}
                <span className={metric.trend === 'up' && currentPeriodRevenue > 0 ? 'text-green-500' : 'text-red-500'}>
                  {metric.change}
                </span>
                <span className="ml-1">{metric.description}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts with Real Data */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Revenue Trends</CardTitle>
            <CardDescription>
              Revenue by pay period - our pay period centric approach
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <RevenueChart />
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Top Performers</CardTitle>
            <CardDescription>
              {currentPayPeriod ? `Top earners for Period #${currentPayPeriod.period_number}` : 'Select pay period to view'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TopPerformersChart commissions={commissionSummary?.top_earners || []} />
          </CardContent>
        </Card>
      </div>

      {/* Our Business Logic Features */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Commission Breakdown</CardTitle>
            <CardDescription>
              Lead Gen, Sales, and Work Done commissions by business unit
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CommissionBreakdown commissionData={commissionSummary} />
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Pay Period Status</CardTitle>
            <CardDescription>
              Current pay period information and schedule
            </CardDescription>
          </CardHeader>
          <CardContent>
            {currentPayPeriod ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Period Number:</span>
                    <span className="text-sm">#{currentPayPeriod.period_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Status:</span>
                    <Badge variant={currentPayPeriod.status === 'Active' ? 'default' : 'secondary'}>
                      {currentPayPeriod.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Pay Date:</span>
                    <span className="text-sm">{format(new Date(currentPayPeriod.pay_date), 'MMM d, yyyy')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Schedule:</span>
                    <span className="text-sm">{payPeriodStats?.schedule_type || 'Not Set'}</span>
                  </div>
                </div>
                
                <div className="pt-2 border-t">
                  <div className="text-sm font-medium mb-2">Data Status:</div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs">Timesheet Data:</span>
                      {uploadStatus.timesheetUploaded ? (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      ) : (
                        <AlertTriangle className="h-3 w-3 text-orange-500" />
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs">Revenue Data:</span>
                      {uploadStatus.revenueUploaded ? (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      ) : (
                        <AlertTriangle className="h-3 w-3 text-orange-500" />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  No pay period selected
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Configure pay periods in Company Setup
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions - Business Logic Aligned */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common commission management tasks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Button 
              variant="outline" 
              className="h-20 flex-col gap-2"
              disabled={!currentPayPeriod || !uploadStatus.revenueUploaded}
            >
              <Calculator className="h-6 w-6" />
              Calculate Commissions
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex-col gap-2"
              onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'company-setup' }))}
            >
              <Users className="h-6 w-6" />
              Manage Employees
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex-col gap-2"
              onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'company-setup' }))}
            >
              <Calendar className="h-6 w-6" />
              Configure Pay Periods
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex-col gap-2"
              disabled={!commissionResults}
              onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'reports' }))}
            >
              <TrendingUp className="h-6 w-6" />
              View Reports
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}