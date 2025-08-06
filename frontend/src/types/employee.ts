export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  full_name: string;
  status: 'Active' | 'Inactive' | 'Helper/Apprentice' | 'Excluded from Payroll';
  pay_type: 'Efficiency Pay' | 'Hourly + Commission';
  hourly_rate: number;
  created_at: string;
  updated_at: string;
  commission_overrides?: {
    [businessUnit: string]: {
      lead_gen_rate?: number;
      sales_rate?: number;
      work_done_rate?: number;
    };
  };
}

export interface EmployeeCreate {
  first_name: string;
  last_name: string;
  status: Employee['status'];
  pay_type: Employee['pay_type'];
  hourly_rate: number;
  commission_overrides?: Employee['commission_overrides'];
}

export interface EmployeeUpdate extends Partial<EmployeeCreate> {}

export interface EmployeeSummary {
  total: number;
  active: number;
  inactive: number;
  helpers: number;
  excluded: number;
  commission_eligible: number;
  efficiency_pay_count: number;
  hourly_plus_commission_count: number;
}