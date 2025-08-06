export interface BusinessUnit {
  id: number;
  name: string;
  lead_gen_rate: number;
  sales_rate: number;
  work_done_rate: number;
  created_at: string;
  updated_at: string;
}

export interface BusinessUnitCreate {
  name: string;
  lead_gen_rate: number;
  sales_rate: number;
  work_done_rate: number;
}

export interface BusinessUnitUpdate extends Partial<BusinessUnitCreate> {}