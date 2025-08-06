'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { PayPeriod } from '@/types/payPeriod';
import { Employee } from '@/types/employee';
import { BusinessUnit } from '@/types/businessUnit';
import { CommissionCalculation } from '@/types/commission';

interface AppState {
  // CENTRAL CONCEPT: Current Pay Period - Everything revolves around this
  currentPayPeriod: PayPeriod | null;
  setCurrentPayPeriod: (period: PayPeriod | null) => void;

  // Core Business Data
  employees: Employee[];
  setEmployees: (employees: Employee[]) => void;
  
  businessUnits: BusinessUnit[];
  setBusinessUnits: (units: BusinessUnit[]) => void;
  
  // Data uploaded for current pay period
  timesheetData: any[];
  setTimesheetData: (data: any[]) => void;
  
  revenueData: any[];
  setRevenueData: (data: any[]) => void;

  // Commission Results - tied to specific pay period
  commissionResults: {
    payPeriodId: number | null;
    calculations: CommissionCalculation[];
    summary: {
      totalCommissions: number;
      totalEmployees: number;
      averageCommission: number;
      byType: {
        leadGeneration: number;
        sales: number;
        workDone: number;
      };
    } | null;
  } | null;
  setCommissionResults: (results: any) => void;

  // Company Configuration - Our specific business rules
  companySettings: {
    // Auto-detection features
    autoDetectEmployees: boolean;
    autoDetectBusinessUnits: boolean;
    allowManualHourOverrides: boolean;
    showDetailedCalculations: boolean;
    
    // Commission calculation settings
    roundingMode: 'nearest_cent' | 'nearest_dollar';
    minimumCommissionAmount: number;
    includeWeekendsInCalculations: boolean;
    
    // Pay period settings
    scheduleType: 'weekly' | 'bi-weekly' | 'semi-monthly' | 'monthly' | null;
    payDelayDays: number;
  };
  updateCompanySettings: (settings: Partial<AppState['companySettings']>) => void;

  // UI State
  loading: {
    employees: boolean;
    calculations: boolean;
    upload: boolean;
    payPeriods: boolean;
  };
  setLoading: (key: keyof AppState['loading'], value: boolean) => void;

  // Upload tracking
  uploadStatus: {
    timesheetUploaded: boolean;
    revenueUploaded: boolean;
    lastUploadDate: string | null;
    validationErrors: any[];
  };
  updateUploadStatus: (status: Partial<AppState['uploadStatus']>) => void;
}

const AppStateContext = createContext<AppState | undefined>(undefined);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [currentPayPeriod, setCurrentPayPeriod] = useState<PayPeriod | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [timesheetData, setTimesheetData] = useState<any[]>([]);
  const [revenueData, setRevenueData] = useState<any[]>([]);
  const [commissionResults, setCommissionResults] = useState<AppState['commissionResults']>(null);
  
  // Our specific business settings
  const [companySettings, setCompanySettings] = useState<AppState['companySettings']>({
    // Auto-detection (core to our system)
    autoDetectEmployees: true,
    autoDetectBusinessUnits: true,
    allowManualHourOverrides: true,
    showDetailedCalculations: true,
    
    // Calculation settings
    roundingMode: 'nearest_cent',
    minimumCommissionAmount: 0,
    includeWeekendsInCalculations: true,
    
    // Pay period settings
    scheduleType: null,
    payDelayDays: 5,
  });

  const [loading, setLoadingState] = useState<AppState['loading']>({
    employees: false,
    calculations: false,
    upload: false,
    payPeriods: false,
  });

  const [uploadStatus, setUploadStatus] = useState<AppState['uploadStatus']>({
    timesheetUploaded: false,
    revenueUploaded: false,
    lastUploadDate: null,
    validationErrors: [],
  });

  const updateCompanySettings = (settings: Partial<AppState['companySettings']>) => {
    setCompanySettings((prev) => ({ ...prev, ...settings }));
  };

  const setLoading = (key: keyof AppState['loading'], value: boolean) => {
    setLoadingState((prev) => ({ ...prev, [key]: value }));
  };

  const updateUploadStatus = (status: Partial<AppState['uploadStatus']>) => {
    setUploadStatus((prev) => ({ ...prev, ...status }));
  };

  const value: AppState = {
    // Central pay period concept
    currentPayPeriod,
    setCurrentPayPeriod,
    
    // Core data
    employees,
    setEmployees,
    businessUnits,
    setBusinessUnits,
    timesheetData,
    setTimesheetData,
    revenueData,
    setRevenueData,
    commissionResults,
    setCommissionResults,
    
    // Configuration
    companySettings,
    updateCompanySettings,
    
    // State management
    loading,
    setLoading,
    uploadStatus,
    updateUploadStatus,
  };

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within AppStateProvider');
  }
  return context;
}