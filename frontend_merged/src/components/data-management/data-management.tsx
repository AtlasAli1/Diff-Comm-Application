'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Upload, Download, Database, FileText, AlertTriangle, CheckCircle } from 'lucide-react'
import { useAppState } from '@/contexts/AppStateContext'
import { formatPayPeriodRange } from '@/lib/utils'

export function DataManagement() {
  const [activeTab, setActiveTab] = useState('upload')
  const { currentPayPeriod, uploadStatus, revenueData, timesheetData } = useAppState()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Management</h1>
          <p className="text-muted-foreground">
            Upload timesheet and revenue data for commission calculations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="gap-1">
            <Database className="h-3 w-3" />
            {currentPayPeriod ? formatPayPeriodRange(currentPayPeriod.start_date, currentPayPeriod.end_date) : 'No Period Selected'}
          </Badge>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Download Templates
          </Button>
        </div>
      </div>

      {/* Data Status Alert */}
      <Alert className={uploadStatus.timesheetUploaded && uploadStatus.revenueUploaded ? 'border-green-200 bg-green-50' : 'border-orange-200 bg-orange-50'}>
        <div className="flex items-center gap-2">
          {uploadStatus.timesheetUploaded && uploadStatus.revenueUploaded ? (
            <CheckCircle className="h-4 w-4 text-green-600" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          )}
          <AlertDescription>
            <div>
              <strong className={uploadStatus.timesheetUploaded && uploadStatus.revenueUploaded ? 'text-green-900' : 'text-orange-900'}>
                Data Upload Status for {currentPayPeriod ? `Period #${currentPayPeriod.period_number}` : 'Current Period'}
              </strong>
              <div className="flex items-center gap-4 mt-2 text-sm">
                <div className="flex items-center gap-1">
                  {uploadStatus.timesheetUploaded ? (
                    <CheckCircle className="h-3 w-3 text-green-600" />
                  ) : (
                    <AlertTriangle className="h-3 w-3 text-orange-600" />
                  )}
                  <span>Timesheet Data: {uploadStatus.timesheetUploaded ? 'Uploaded' : 'Missing'}</span>
                </div>
                <div className="flex items-center gap-1">
                  {uploadStatus.revenueUploaded ? (
                    <CheckCircle className="h-3 w-3 text-green-600" />
                  ) : (
                    <AlertTriangle className="h-3 w-3 text-orange-600" />
                  )}
                  <span>Revenue Data: {uploadStatus.revenueUploaded ? 'Uploaded' : 'Missing'}</span>
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
            <CardTitle className="text-sm font-medium">Revenue Records</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{revenueData.length.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {currentPayPeriod ? 'Current period' : 'All periods'}
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Timesheet Records</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{timesheetData.length.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {currentPayPeriod ? 'Current period' : 'All periods'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Validation Status</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{uploadStatus.validationErrors.length}</div>
            <p className="text-xs text-muted-foreground">
              Validation errors
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Upload</CardTitle>
            <Upload className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {uploadStatus.lastUploadDate ? 'Today' : '--'}
            </div>
            <p className="text-xs text-muted-foreground">
              {uploadStatus.lastUploadDate || 'No uploads yet'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Data Management Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upload" className="gap-2">
            <Upload className="h-4 w-4" />
            File Upload
          </TabsTrigger>
          <TabsTrigger value="revenue" className="gap-2">
            <Database className="h-4 w-4" />
            Revenue Data
          </TabsTrigger>
          <TabsTrigger value="timesheet" className="gap-2">
            <FileText className="h-4 w-4" />
            Timesheet Data
          </TabsTrigger>
          <TabsTrigger value="validation" className="gap-2">
            <AlertTriangle className="h-4 w-4" />
            Validation
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>File Upload</CardTitle>
              <CardDescription>
                Upload CSV or Excel files with timesheet and revenue data for commission calculations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-muted-foreground">
                <Upload className="h-12 w-12 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Drag & Drop File Upload</h3>
                <p className="text-sm mb-4">
                  Upload CSV/Excel files with validation and progress tracking
                </p>
                <div className="text-xs space-y-1">
                  <p><strong>Required columns:</strong></p>
                  <p>Revenue: Date, Job ID, Customer, Business Unit, Jobs Total Revenue</p>
                  <p>Timesheet: Employee Name, Date, Hours, Business Unit</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="revenue" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Revenue Data</CardTitle>
              <CardDescription>
                View and manage uploaded revenue data for commission calculations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Database className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">Revenue data will display here</p>
                <p className="text-sm mt-1">Upload revenue data to see job records</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timesheet" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Timesheet Data</CardTitle>
              <CardDescription>
                View and manage employee timesheet data with manual override capabilities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">Timesheet data will display here</p>
                <p className="text-sm mt-1">Upload timesheet data to see employee hours</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Validation</CardTitle>
              <CardDescription>
                Review validation errors and data quality issues
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">Validation results will appear here</p>
                <p className="text-sm mt-1">Upload data to see validation status</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}