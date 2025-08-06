export interface CommissionDetail {
  job_id: string;
  date: string;
  business_unit: string;
  commission_type: 'Lead Generation' | 'Sales' | 'Work Done';
  revenue: number;
  commission_rate: number;
  commission_amount: number;
  technicians?: string[];
}

export interface CommissionCalculation {
  employee_id: number;
  employee_name: string;
  pay_type: string;
  hours_worked: number;
  hourly_rate: number;
  hourly_pay: number;
  commission_details: CommissionDetail[];
  total_commission: number;
  efficiency_pay: number;
  final_pay: number;
  pay_breakdown: {
    lead_generation: number;
    sales: number;
    work_done: number;
  };
}

export interface CommissionRequest {
  employee_ids: number[];
  start_date: string;
  end_date: string;
}

export interface PayPeriodCommissionRequest {
  pay_period_id: number;
  employee_ids?: number[];
}

export interface CommissionSummary {
  total_commission: number;
  total_employees: number;
  average_commission: number;
  highest_earner: {
    employee_id: number;
    employee_name: string;
    amount: number;
  };
  top_earners: Array<{
    employee_id: number;
    employee_name: string;
    amount: number;
  }>;
  by_type: {
    lead_generation: number;
    sales: number;
    work_done: number;
  };
}