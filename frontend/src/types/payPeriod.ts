export interface PayPeriod {
  id: number;
  period_number: number;
  start_date: string;
  end_date: string;
  pay_date: string;
  status: 'Active' | 'Completed' | 'Future';
  created_at: string;
  updated_at: string;
}

export interface PayPeriodGenerate {
  schedule_type: 'weekly' | 'bi-weekly' | 'semi-monthly' | 'monthly';
  first_period_start: string;
  pay_delay_days: number;
}

export interface PayPeriodStats {
  total_periods: number;
  completed_periods: number;
  current_period?: PayPeriod;
  upcoming_periods: PayPeriod[];
  schedule_type?: string;
}