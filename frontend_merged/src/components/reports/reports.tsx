'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { FileText, Download, Eye, TrendingUp, Users, Building2 } from 'lucide-react'
import { useAppState } from '@/contexts/AppStateContext'
import { formatPayPeriodRange, formatCurrency } from '@/lib/utils'

export function Reports() {
  const { currentPayPeriod, commissionResults, employees } = useAppState()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            Generate and export detailed commission reports and analytics
          </p>
        </div>
        <div className="flex items-center gap-2">
          {currentPayPeriod && (
            <Badge variant="outline" className="gap-1">
              <FileText className="h-3 w-3" />
              {formatPayPeriodRange(currentPayPeriod.start_date, currentPayPeriod.end_date)}
            </Badge>
          )}
          <Button disabled={!commissionResults}>
            <Download className="h-4 w-4 mr-2" />
            Export All
          </Button>
        </div>
      </div>

      {/* Report Categories */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">Employee Reports</CardTitle>
              </div>
              <Button variant="ghost" size="sm">
                <Eye className="h-4 w-4" />
              </Button>
            </div>
            <CardDescription>
              Individual commission breakdowns and pay statements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Employees with commissions:</span>
                <span className="font-medium">
                  {commissionResults?.calculations.filter(c => c.total_commission > 0).length || 0}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Avg commission:</span>
                <span className="font-medium">
                  {commissionResults?.summary ? 
                    formatCurrency(commissionResults.summary.totalCommissions / commissionResults.summary.totalEmployees) : 
                    '$0'
                  }
                </span>
              </div>
            </div>
            <div className="mt-4 space-y-1">
              <Button variant="outline" size="sm" className="w-full" disabled={!commissionResults}>
                <FileText className="h-4 w-4 mr-2" />
                Individual Pay Statements
              </Button>
              <Button variant="outline" size="sm" className="w-full" disabled={!commissionResults}>
                <Download className="h-4 w-4 mr-2" />
                Export Employee Report
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">Business Unit Reports</CardTitle>
              </div>
              <Button variant="ghost" size="sm">
                <Eye className="h-4 w-4" />
              </Button>
            </div>
            <CardDescription>
              Revenue and commission analysis by business unit
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Total units:</span>
                <span className="font-medium">4 active</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Commission breakdown:</span>
                <span className="font-medium">By type</span>
              </div>
            </div>
            <div className="mt-4 space-y-1">
              <Button variant="outline" size="sm" className="w-full">
                <TrendingUp className="h-4 w-4 mr-2" />
                Performance Analysis
              </Button>
              <Button variant="outline" size="sm" className="w-full">
                <Download className="h-4 w-4 mr-2" />
                Export Unit Report
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">Executive Reports</CardTitle>
              </div>
              <Button variant="ghost" size="sm">
                <Eye className="h-4 w-4" />
              </Button>
            </div>
            <CardDescription>
              High-level analytics and trend analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Total commissions:</span>
                <span className="font-medium">
                  {commissionResults?.summary ? 
                    formatCurrency(commissionResults.summary.totalCommissions) : 
                    '$0'
                  }
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Commission rate:</span>
                <span className="font-medium">10.2%</span>
              </div>
            </div>
            <div className="mt-4 space-y-1">
              <Button variant="outline" size="sm" className="w-full">
                <TrendingUp className="h-4 w-4 mr-2" />
                Trend Analysis
              </Button>
              <Button variant="outline" size="sm" className="w-full">
                <Download className="h-4 w-4 mr-2" />
                Export Executive Summary
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Reports */}
      {commissionResults ? (
        <Card>
          <CardHeader>
            <CardTitle>Commission Report Details</CardTitle>
            <CardDescription>
              Detailed breakdown for {currentPayPeriod ? `Period #${currentPayPeriod.period_number}` : 'current period'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {formatCurrency(commissionResults.summary?.totalCommissions || 0)}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Commissions</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {commissionResults.summary?.totalEmployees || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Employees</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {formatCurrency(commissionResults.summary?.totalCommissions / commissionResults.summary?.totalEmployees || 0)}
                  </div>
                  <div className="text-sm text-muted-foreground">Average</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">3</div>
                  <div className="text-sm text-muted-foreground">Commission Types</div>
                </div>
              </div>

              {commissionResults.summary && (
                <div>
                  <h4 className="font-medium mb-4">Commission Breakdown by Type</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 rounded-full bg-chart-1" />
                        <span className="font-medium">Lead Generation</span>
                      </div>
                      <div className="text-lg font-semibold">
                        {formatCurrency(commissionResults.summary.byType.leadGeneration)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {((commissionResults.summary.byType.leadGeneration / commissionResults.summary.totalCommissions) * 100).toFixed(1)}% of total
                      </div>
                    </div>
                    
                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 rounded-full bg-chart-2" />
                        <span className="font-medium">Sales</span>
                      </div>
                      <div className="text-lg font-semibold">
                        {formatCurrency(commissionResults.summary.byType.sales)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {((commissionResults.summary.byType.sales / commissionResults.summary.totalCommissions) * 100).toFixed(1)}% of total
                      </div>
                    </div>
                    
                    <div className="p-4 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 rounded-full bg-chart-3" />
                        <span className="font-medium">Work Done</span>
                      </div>
                      <div className="text-lg font-semibold">
                        {formatCurrency(commissionResults.summary.byType.workDone)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {((commissionResults.summary.byType.workDone / commissionResults.summary.totalCommissions) * 100).toFixed(1)}% of total
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Report Data Available</h3>
            <p className="text-muted-foreground mb-4">
              Calculate commissions to generate detailed reports and analytics
            </p>
            <Button variant="outline">
              Go to Commission Calculator
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}