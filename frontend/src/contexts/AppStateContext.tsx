'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { PayPeriod } from '@/types/payPeriod';
import { Employee } from '@/types/employee';
import { BusinessUnit } from '@/types/businessUnit';
import { CommissionCalculation } from '@/types/commission';

interface AppState {
  // Current context
  currentPayPeriod: PayPeriod | null;
  setCurrentPayPeriod: (period: PayPeriod | null) => void;

  // Loaded data
  employees: Employee[];
  setEmployees: (employees: Employee[]) => void;
  
  businessUnits: BusinessUnit[];
  setBusinessUnits: (units: BusinessUnit[]) => void;
  
  timesheetData: any[];
  setTimesheetData: (data: any[]) => void;
  
  revenueData: any[];
  setRevenueData: (data: any[]) => void;

  // Calculation results
  commissionResults: {
    payPeriodId: number | null;
    calculations: CommissionCalculation[];
    summary: any;
  } | null;
  setCommissionResults: (results: any) => void;

  // Company settings
  companySettings: {
    autoDetectEmployees: boolean;
    autoDetectUnits: boolean;
    allowManualOverrides: boolean;
    showDetailedCalculations: boolean;
  };
  updateCompanySettings: (settings: Partial<AppState['companySettings']>) => void;

  // UI State
  loading: {
    employees: boolean;
    calculations: boolean;
    upload: boolean;
  };
  setLoading: (key: keyof AppState['loading'], value: boolean) => void;
}

const AppStateContext = createContext<AppState | undefined>(undefined);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [currentPayPeriod, setCurrentPayPeriod] = useState<PayPeriod | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [timesheetData, setTimesheetData] = useState<any[]>([]);
  const [revenueData, setRevenueData] = useState<any[]>([]);
  const [commissionResults, setCommissionResults] = useState<AppState['commissionResults']>(null);
  
  const [companySettings, setCompanySettings] = useState<AppState['companySettings']>({
    autoDetectEmployees: true,
    autoDetectUnits: true,
    allowManualOverrides: true,
    showDetailedCalculations: true,
  });

  const [loading, setLoadingState] = useState<AppState['loading']>({
    employees: false,
    calculations: false,
    upload: false,
  });

  const updateCompanySettings = (settings: Partial<AppState['companySettings']>) => {
    setCompanySettings((prev) => ({ ...prev, ...settings }));
  };

  const setLoading = (key: keyof AppState['loading'], value: boolean) => {
    setLoadingState((prev) => ({ ...prev, [key]: value }));
  };

  const value: AppState = {
    currentPayPeriod,
    setCurrentPayPeriod,
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
    companySettings,
    updateCompanySettings,
    loading,
    setLoading,
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