'use client'

import { Calculator, BarChart3, Database, Settings, Home, Building2 } from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from '@/components/ui/sidebar'
import { ThemeToggle } from '@/components/theme-toggle'
import { Badge } from '@/components/ui/badge'
import { useAppState } from '@/contexts/AppStateContext'
import { useQuery } from '@tanstack/react-query'
import { healthService } from '@/lib/api/services'
import { cn } from '@/lib/utils'

// Navigation items reflecting our business logic
const items = [
  {
    title: 'Dashboard',
    url: '#',
    icon: Home,
    id: 'dashboard',
    description: 'Overview and metrics'
  },
  {
    title: 'Company Setup',
    url: '#',
    icon: Building2,
    id: 'company-setup',
    description: 'Employees, pay periods, business units'
  },
  {
    title: 'Data Management',
    url: '#',
    icon: Database,
    id: 'data-management',
    description: 'Upload timesheets and revenue data'
  },
  {
    title: 'Commission Calculator',
    url: '#',
    icon: Calculator,
    id: 'commission-calculator',
    description: 'Calculate commissions for pay periods'
  },
  {
    title: 'Reports',
    url: '#',
    icon: BarChart3,
    id: 'reports',
    description: 'View and export commission reports'
  },
]

interface AppSidebarProps {
  onNavigate: (section: string) => void
  activeSection: string
}

export function AppSidebar({ onNavigate, activeSection }: AppSidebarProps) {
  const { currentPayPeriod, companySettings, uploadStatus } = useAppState()
  
  // Monitor API health
  const { data: healthStatus } = useQuery({
    queryKey: ['apiHealth'],
    queryFn: healthService.getHealth,
    refetchInterval: 30000, // Check every 30 seconds
    retry: false,
  });

  return (
    <Sidebar>
      <SidebarHeader className="border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calculator className="h-6 w-6 text-primary" />
            <div>
              <span className="font-semibold">Commission Pro</span>
              <div className="text-xs text-muted-foreground">v2.0.0</div>
            </div>
          </div>
          <ThemeToggle />
        </div>
        
        {/* System Status */}
        <div className="mt-3 space-y-1">
          {healthStatus && (
            <Badge 
              variant={healthStatus.status === 'healthy' ? 'default' : 'destructive'}
              className="w-full justify-center gap-1"
            >
              <div className="h-2 w-2 rounded-full bg-current" />
              API {healthStatus.status === 'healthy' ? 'Connected' : 'Issues'}
            </Badge>
          )}
          
          {currentPayPeriod && (
            <Badge variant="outline" className="w-full justify-center">
              Period #{currentPayPeriod.period_number}
            </Badge>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const isActive = activeSection === item.id;
                
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton 
                      onClick={() => onNavigate(item.id)}
                      className={cn(
                        "cursor-pointer",
                        isActive && "bg-primary/10 text-primary font-medium"
                      )}
                      tooltip={item.description}
                    >
                      <item.icon className={cn(
                        "h-4 w-4",
                        isActive && "text-primary"
                      )} />
                      <span>{item.title}</span>
                      
                      {/* Status indicators based on our business logic */}
                      {item.id === 'data-management' && (uploadStatus.validationErrors.length > 0) && (
                        <Badge variant="destructive" className="ml-auto h-5 w-5 p-0 text-xs">
                          !
                        </Badge>
                      )}
                      
                      {item.id === 'company-setup' && !currentPayPeriod && (
                        <Badge variant="outline" className="ml-auto h-5 w-5 p-0 text-xs">
                          !
                        </Badge>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Quick Stats - Our Business Logic */}
        <SidebarGroup>
          <SidebarGroupLabel>Quick Stats</SidebarGroupLabel>
          <SidebarGroupContent className="space-y-2 px-2">
            <div className="text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Data Status:</span>
                <span className={cn(
                  "font-medium",
                  (uploadStatus.timesheetUploaded && uploadStatus.revenueUploaded) 
                    ? "text-green-600" : "text-orange-600"
                )}>
                  {(uploadStatus.timesheetUploaded && uploadStatus.revenueUploaded) 
                    ? "Ready" : "Incomplete"}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Auto-Detect:</span>
                <span className="font-medium">
                  {companySettings.autoDetectEmployees ? "On" : "Off"}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-muted-foreground">Schedule:</span>
                <span className="font-medium">
                  {companySettings.scheduleType || "Not Set"}
                </span>
              </div>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-4">
        <div className="text-xs text-muted-foreground">
          <div>Commission Calculator Pro</div>
          <div>Enterprise Edition</div>
          {currentPayPeriod && (
            <div className="mt-1 text-primary font-medium">
              Active: Period #{currentPayPeriod.period_number}
            </div>
          )}
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}