'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Calculator, Play, Users, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import { useAppState } from '@/contexts/AppStateContext'
import { formatPayPeriodRange, formatCurrency } from '@/lib/utils'

export function CommissionCalc() {
  const [calculationStatus, setCalculationStatus] = useState<'idle' | 'calculating' | 'completed'>('idle')
  const { currentPayPeriod, uploadStatus, revenueData, employees, commissionResults } = useAppState()

  // Check if ready for calculation
  const isReadyForCalculation = currentPayPeriod && 
    uploadStatus.timesheetUploaded && 
    uploadStatus.revenueUploaded && 
    employees.length > 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Commission Calculator</h1>
          <p className="text-muted-foreground">
            Calculate commissions using our Lead Gen, Sales, and Work Done methodology
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={isReadyForCalculation ? "default" : "secondary"} className="gap-1">
            <Calculator className="h-3 w-3" />
            {isReadyForCalculation ? 'Ready to Calculate' : 'Setup Required'}
          </Badge>
          <Button 
            className="gap-2"
            disabled={!isReadyForCalculation || calculationStatus === 'calculating'}
            onClick={() => setCalculationStatus('calculating')}
          >
            <Play className="h-4 w-4" />
            {calculationStatus === 'calculating' ? 'Calculating...' : 'Calculate Commissions'}
          </Button>
        </div>
      </div>

      {/* Prerequisites Check */}
      <Alert className={isReadyForCalculation ? 'border-green-200 bg-green-50' : 'border-orange-200 bg-orange-50'}>
        <div className="flex items-center gap-2">
          {isReadyForCalculation ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          )}
          <AlertDescription>
            <div>
              <strong className={isReadyForCalculation ? 'text-green-900' : 'text-orange-900'}>
                Commission Calculation Prerequisites
              </strong>
              <div className="grid grid-cols-2 gap-4 mt-2 text-sm">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {currentPayPeriod ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-3 w-3 text-orange-600" />
                    )}
                    <span>Pay Period: {currentPayPeriod ? `#${currentPayPeriod.period_number}` : 'Not Selected'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {employees.length > 0 ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-3 w-3 text-orange-600" />
                    )}
                    <span>Employees: {employees.length} configured</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {uploadStatus.timesheetUploaded ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-3 w-3 text-orange-600" />
                    )}
                    <span>Timesheet Data: {uploadStatus.timesheetUploaded ? 'Uploaded' : 'Missing'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {uploadStatus.revenueUploaded ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-3 w-3 text-orange-600" />
                    )}
                    <span>Revenue Data: {uploadStatus.revenueUploaded ? 'Uploaded' : 'Missing'}</span>
                  </div>
                </div>
              </div>
            </div>
          </AlertDescription>
        </div>
      </Alert>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Eligible Employees</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {employees.filter(e => e.status === 'Active').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Ready for calculation
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Revenue to Process</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(revenueData.reduce((sum, item) => sum + (parseFloat(item.revenue) || 0), 0))}
            </div>
            <p className="text-xs text-muted-foreground">
              Current period
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Est. Commissions</CardTitle>
            <Calculator className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {commissionResults ? formatCurrency(commissionResults.summary?.totalCommissions || 0) : '--'}
            </div>
            <p className="text-xs text-muted-foreground">
              {commissionResults ? 'Calculated' : 'Not calculated'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Calculation</CardTitle>
            <Calculator className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {commissionResults ? 'Complete' : 'None'}
            </div>
            <p className="text-xs text-muted-foreground">
              {commissionResults ? `${commissionResults.calculations.length} employees` : 'Run calculation'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Commission Calculation Interface */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Calculation Setup</CardTitle>
            <CardDescription>
              Configure commission calculation parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Commission Types</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-chart-1" />
                    <span><strong>Lead Generation:</strong> Commission for bringing in customers</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-chart-2" />
                    <span><strong>Sales:</strong> Commission for closing the sale</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-chart-3" />
                    <span><strong>Work Done:</strong> Commission split among technicians</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Pay Models</h4>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p><strong>Efficiency Pay:</strong> MAX(hourly pay, total commission)</p>
                  <p><strong>Hourly + Commission:</strong> Hourly pay + all commission</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Calculation Results</CardTitle>
            <CardDescription>
              Review commission calculation results
            </CardDescription>
          </CardHeader>
          <CardContent>
            {commissionResults ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-lg font-semibold">
                      {formatCurrency(commissionResults.summary?.totalCommissions || 0)}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Commissions</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold">
                      {commissionResults.summary?.totalEmployees || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">Employees Processed</div>
                  </div>
                </div>
                
                {commissionResults.summary && (
                  <div className="space-y-2">
                    <h5 className="font-medium">By Commission Type:</h5>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Lead Generation:</span>
                        <span>{formatCurrency(commissionResults.summary.byType.leadGeneration)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Sales:</span>
                        <span>{formatCurrency(commissionResults.summary.byType.sales)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Work Done:</span>
                        <span>{formatCurrency(commissionResults.summary.byType.workDone)}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calculator className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">No calculation results</p>
                <p className="text-sm mt-1">Run commission calculation to see results</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}