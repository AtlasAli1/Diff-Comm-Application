export interface UploadWarning {
  row?: number;
  field?: string;
  message: string;
}

export interface TimesheetUploadResponse {
  success: boolean;
  message: string;
  records_processed: number;
  date_range: {
    start: string;
    end: string;
  };
  employees_found: string[];
  new_employees: string[];
  warnings: UploadWarning[];
}

export interface RevenueUploadResponse {
  success: boolean;
  message: string;
  records_processed: number;
  date_range: {
    start: string;
    end: string;
  };
  business_units_found: string[];
  new_business_units: string[];
  total_revenue: number;
  warnings: UploadWarning[];
}

export interface EmployeeUploadResponse {
  success: boolean;
  message: string;
  created: number;
  updated: number;
  errors: Array<{
    row: number;
    errors: string[];
  }>;
}