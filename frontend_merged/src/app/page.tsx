'use client'

import { useState, useEffect } from 'react'
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Calendar, AlertTriangle, CheckCircle } from 'lucide-react'
import { Dashboard } from '@/components/dashboard/dashboard'
import { CompanySetup } from '@/components/company-setup/company-setup'
import { DataManagement } from '@/components/data-management/data-management'
import { CommissionCalc } from '@/components/commission-calc/commission-calc'
import { Reports } from '@/components/reports/reports'
import { AppSidebar } from '@/components/app-sidebar'
import { PayPeriodSelector } from '@/components/PayPeriodSelector'
import { useAppState } from '@/contexts/AppStateContext'
import { useQuery } from '@tanstack/react-query'
import { payPeriodService } from '@/lib/api/services'
import { format } from 'date-fns'

export default function Home() {
  const [activeSection, setActiveSection] = useState('dashboard')
  const { currentPayPeriod, setCurrentPayPeriod } = useAppState()

  // Load current pay period on mount - THIS IS CENTRAL TO OUR SYSTEM
  const { data: currentPeriod, isLoading: isLoadingPeriod } = useQuery({
    queryKey: ['currentPayPeriod'],
    queryFn: payPeriodService.getCurrentPayPeriod,
    onSuccess: (data) => {
      if (!currentPayPeriod) {
        setCurrentPayPeriod(data);
      }
    },
  });

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <Dashboard />
      case 'company-setup':
        return <CompanySetup />
      case 'data-management':
        return <DataManagement />
      case 'commission-calculator':
        return <CommissionCalc />
      case 'reports':
        return <Reports />
      default:
        return <Dashboard />
    }
  }

  // Pay period status indicator
  const getPayPeriodStatus = () => {
    if (!currentPayPeriod) return { icon: AlertTriangle, color: 'destructive', text: 'No Pay Period' };
    
    switch (currentPayPeriod.status) {
      case 'Active':
        return { icon: CheckCircle, color: 'default', text: 'Active Period' };
      case 'Completed':
        return { icon: Calendar, color: 'secondary', text: 'Period Completed' };
      case 'Future':
        return { icon: Calendar, color: 'outline', text: 'Future Period' };
      default:
        return { icon: AlertTriangle, color: 'destructive', text: 'Unknown Status' };
    }
  };

  const statusInfo = getPayPeriodStatus();
  const StatusIcon = statusInfo.icon;

  return (
    <div className="flex min-h-screen w-full">
      <AppSidebar onNavigate={setActiveSection} activeSection={activeSection} />
      <SidebarInset className="flex-1">
        {/* Header with Pay Period - OUR CORE CONCEPT */}
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          
          <div className="flex items-center gap-4 flex-1">
            <h1 className="text-lg font-semibold">Commission Calculator Pro</h1>
            
            {/* PAY PERIOD IS CENTRAL - Always visible */}
            <div className="flex items-center gap-2 ml-auto">
              <PayPeriodSelector />
              
              {currentPayPeriod && (
                <Badge variant={statusInfo.color as any} className="gap-1">
                  <StatusIcon className="h-3 w-3" />
                  {statusInfo.text}
                </Badge>
              )}
              
              {isLoadingPeriod && (
                <Badge variant="outline" className="gap-1 animate-pulse">
                  <Calendar className="h-3 w-3" />
                  Loading...
                </Badge>
              )}
            </div>
          </div>
        </header>

        {/* Pay Period Alert - Show if no pay period configured */}
        {!currentPayPeriod && !isLoadingPeriod && (
          <div className="mx-4 mt-4 p-4 border border-orange-200 bg-orange-50 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <div>
                <p className="font-medium text-orange-900">Pay Periods Not Configured</p>
                <p className="text-sm text-orange-700">
                  Set up your pay period schedule in Company Setup to begin calculating commissions.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 p-6">
          {renderContent()}
        </div>
      </SidebarInset>
    </div>
  )
}