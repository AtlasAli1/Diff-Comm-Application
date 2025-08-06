'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Plus, Users, Building2, Calendar, Settings, AlertTriangle, CheckCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useAppState } from '@/contexts/AppStateContext'
import { useQuery } from '@tanstack/react-query'
import { employeeService, businessUnitService, payPeriodService } from '@/lib/api/services'
import { EmployeeManagement } from './employee-management'

export function CompanySetup() {
  const [activeTab, setActiveTab] = useState('employees')
  const { currentPayPeriod, companySettings } = useAppState()

  // Get real employee data
  const { data: employeeSummary } = useQuery({
    queryKey: ['employeeSummary'],
    queryFn: employeeService.getEmployeeSummary,
  });

  // Get business units
  const { data: businessUnits } = useQuery({
    queryKey: ['businessUnits'],
    queryFn: businessUnitService.getBusinessUnits,
  });

  // Get pay period stats
  const { data: payPeriodStats } = useQuery({
    queryKey: ['payPeriodStats'],
    queryFn: payPeriodService.getPayPeriodStats,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Company Setup</h1>
          <p className="text-muted-foreground">
            Configure your pay periods, employees, business units, and commission structure.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="gap-1">
            <Users className="h-3 w-3" />
            {employeeSummary?.active || 0} Active Employees
          </Badge>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Employee
          </Button>
        </div>
      </div>

      {/* Setup Progress Alert */}
      <Alert className={!currentPayPeriod || !employeeSummary?.active ? 'border-orange-200 bg-orange-50' : 'border-green-200 bg-green-50'}>
        <div className="flex items-center gap-2">
          {!currentPayPeriod || !employeeSummary?.active ? (
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          ) : (
            <CheckCircle className="h-4 w-4 text-green-600" />
          )}
          <AlertDescription>
            <div className="flex items-center justify-between">
              <div>
                <strong className={!currentPayPeriod || !employeeSummary?.active ? 'text-orange-900' : 'text-green-900'}>
                  Company Setup Status
                </strong>
                <div className="text-sm mt-1 space-y-1">
                  {!currentPayPeriod && (
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-3 w-3 text-orange-600" />
                      <span className="text-orange-700">Configure pay periods to begin calculations</span>
                    </div>
                  )}
                  {!employeeSummary?.active && (
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-3 w-3 text-orange-600" />
                      <span className="text-orange-700">Add employees to calculate commissions</span>
                    </div>
                  )}
                  {currentPayPeriod && employeeSummary?.active && (
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-3 w-3 text-green-600" />
                      <span className="text-green-700">Ready for commission calculations</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </AlertDescription>
        </div>
      </Alert>

      {/* Tabs - Our Business Logic Order */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="pay-periods" className="gap-2">
            <Calendar className="h-4 w-4" />
            Pay Periods
            {!currentPayPeriod && <AlertTriangle className="h-3 w-3 text-orange-500" />}
          </TabsTrigger>
          <TabsTrigger value="employees" className="gap-2">
            <Users className="h-4 w-4" />
            Employees
            {!employeeSummary?.active && <AlertTriangle className="h-3 w-3 text-orange-500" />}
          </TabsTrigger>
          <TabsTrigger value="business-units" className="gap-2">
            <Building2 className="h-4 w-4" />
            Business Units
            {!businessUnits?.length && <AlertTriangle className="h-3 w-3 text-orange-500" />}
          </TabsTrigger>
          <TabsTrigger value="settings" className="gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pay-periods" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Pay Period Configuration</CardTitle>
              <CardDescription>
                Set up your automated pay period schedule - the foundation of our commission system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">Pay Period Setup</p>
                <p className="text-sm mt-1">Configure bi-weekly, weekly, or monthly schedules</p>
                <p className="text-xs mt-2 text-orange-600">
                  This component will include automated pay period generation
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="employees" className="space-y-4">
          <EmployeeManagement />
        </TabsContent>

        <TabsContent value="business-units" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Business Unit Setup</CardTitle>
              <CardDescription>
                Configure business units and their commission rates for Lead Gen, Sales, and Work Done
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Building2 className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">Business Units</p>
                <p className="text-sm mt-1">Electrical, Plumbing, HVAC, etc.</p>
                <p className="text-xs mt-2 text-orange-600">
                  Each unit has different commission rates for our 3 commission types
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Company Settings</CardTitle>
              <CardDescription>
                Configure auto-detection, rounding, and calculation preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="font-medium">Detection Settings</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Auto-detect employees:</span>
                        <Badge variant={companySettings.autoDetectEmployees ? "default" : "secondary"}>
                          {companySettings.autoDetectEmployees ? "Enabled" : "Disabled"}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Auto-detect business units:</span>
                        <Badge variant={companySettings.autoDetectBusinessUnits ? "default" : "secondary"}>
                          {companySettings.autoDetectBusinessUnits ? "Enabled" : "Disabled"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-medium">Calculation Settings</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Rounding mode:</span>
                        <Badge variant="outline">{companySettings.roundingMode}</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span>Schedule type:</span>
                        <Badge variant="outline">{companySettings.scheduleType || "Not Set"}</Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}