"""
Commission calculation service - core business logic for commission calculations
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import logging

from ..models.commission import (
    CommissionRequest,
    CommissionCalculation,
    CommissionDetail,
    EfficiencyPayDetail,
    CommissionSummary,
    EfficiencyPayResult,
    CommissionType
)
from ..models.employee import EmployeeStatus, CommissionPlan

logger = logging.getLogger(__name__)


class CommissionService:
    """Service class for commission calculation business logic"""
    
    def __init__(self):
        pass
    
    async def calculate_commissions(self, request: CommissionRequest) -> Tuple[List[CommissionCalculation], CommissionSummary, Optional[EfficiencyPayResult]]:
        """
        Calculate commissions for specified employees and period
        
        Returns:
            Tuple of (calculations, summary, efficiency_results)
        """
        logger.info(f"Calculating commissions for {len(request.employee_ids)} employees")
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        # Get necessary data
        employee_df = session.get_employee_data()
        revenue_df = session.get_revenue_data()
        timesheet_df = session.get_timesheet_data()
        business_settings = session.get_business_unit_settings()
        employee_overrides = session.get_employee_overrides()
        timesheet_overrides = session.get_timesheet_hour_overrides()
        
        if employee_df.empty:
            raise ValueError("No employee data available")
        
        # Filter employees by requested IDs
        if request.employee_ids:
            employee_df = employee_df.iloc[request.employee_ids].copy()
        
        calculations = []
        total_commission = Decimal('0.00')
        total_hourly_pay = Decimal('0.00') 
        total_efficiency_pay = Decimal('0.00')
        total_final_pay = Decimal('0.00')
        
        # Breakdown by type
        lead_gen_total = Decimal('0.00')
        sales_total = Decimal('0.00')
        work_done_total = Decimal('0.00')
        
        # Business unit breakdown
        business_unit_summary = {}
        
        # Calculate for each employee
        for emp_idx, emp_row in employee_df.iterrows():
            employee_name = emp_row['Name']
            
            # Calculate revenue-based commissions
            commission_details = []
            employee_commission_total = Decimal('0.00')
            
            if not revenue_df.empty:
                emp_commissions = await self._calculate_employee_revenue_commissions(
                    employee_name, revenue_df, business_settings, employee_overrides,
                    request.start_date, request.end_date
                )
                commission_details.extend(emp_commissions)
                employee_commission_total = sum(detail.commission_amount for detail in emp_commissions)
            
            # Calculate efficiency pay if timesheet data exists
            efficiency_detail = None
            if not timesheet_df.empty:
                efficiency_detail = await self._calculate_employee_efficiency_pay(
                    employee_name, emp_row, timesheet_df, timesheet_overrides, employee_commission_total
                )
            
            # Create calculation result
            calculation = CommissionCalculation(
                employee_id=emp_idx,
                employee_name=employee_name,
                period_start=request.start_date,
                period_end=request.end_date,
                commission_details=commission_details,
                efficiency_details=efficiency_detail
            )
            
            # Calculate totals by type
            for detail in commission_details:
                if detail.commission_type == CommissionType.LEAD_GENERATION:
                    calculation.lead_generation_commission += detail.commission_amount
                    lead_gen_total += detail.commission_amount
                elif detail.commission_type == CommissionType.SALES:
                    calculation.sales_commission += detail.commission_amount 
                    sales_total += detail.commission_amount
                elif detail.commission_type == CommissionType.WORK_DONE:
                    calculation.work_done_commission += detail.commission_amount
                    work_done_total += detail.commission_amount
                
                # Business unit totals
                bu = detail.business_unit
                if bu not in business_unit_summary:
                    business_unit_summary[bu] = Decimal('0.00')
                business_unit_summary[bu] += detail.commission_amount
            
            calculation.total_commission = employee_commission_total
            
            if efficiency_detail:
                calculation.hourly_pay = efficiency_detail.hourly_pay
                calculation.efficiency_pay = efficiency_detail.efficiency_pay
                calculation.final_pay = efficiency_detail.final_pay
                
                total_hourly_pay += efficiency_detail.hourly_pay
                total_efficiency_pay += efficiency_detail.efficiency_pay
                total_final_pay += efficiency_detail.final_pay
            
            total_commission += employee_commission_total
            calculations.append(calculation)
        
        # Create summary
        summary = CommissionSummary(
            period_start=request.start_date,
            period_end=request.end_date,
            total_employees=len(calculations),
            total_commission_amount=total_commission,
            total_hourly_pay=total_hourly_pay,
            total_efficiency_pay=total_efficiency_pay,
            total_final_pay=total_final_pay,
            lead_generation_total=lead_gen_total,
            sales_total=sales_total,
            work_done_total=work_done_total,
            business_unit_summary=business_unit_summary
        )
        
        # Create efficiency results if applicable
        efficiency_results = None
        if not timesheet_df.empty:
            efficiency_calculations = [c.efficiency_details for c in calculations if c.efficiency_details]
            if efficiency_calculations:
                positive_count = len([e for e in efficiency_calculations if e.efficiency_pay > 0])
                negative_count = len([e for e in efficiency_calculations if e.efficiency_pay < 0])
                avg_efficiency = total_efficiency_pay / len(efficiency_calculations) if efficiency_calculations else Decimal('0.00')
                
                efficiency_results = EfficiencyPayResult(
                    employees_calculated=len(efficiency_calculations),
                    total_efficiency_pay=total_efficiency_pay,
                    positive_efficiency_count=positive_count,
                    negative_efficiency_count=negative_count,
                    average_efficiency_pay=avg_efficiency
                )
        
        logger.info(f"Completed calculations for {len(calculations)} employees")
        return calculations, summary, efficiency_results
    
    async def _calculate_employee_revenue_commissions(
        self, 
        employee_name: str,
        revenue_df: pd.DataFrame,
        business_settings: Dict,
        employee_overrides: Dict,
        start_date: date,
        end_date: date
    ) -> List[CommissionDetail]:
        """Calculate revenue-based commissions for an employee"""
        
        details = []
        
        # Filter revenue data by date if possible
        filtered_revenue = revenue_df.copy()
        if 'Date' in revenue_df.columns:
            try:
                filtered_revenue['Date'] = pd.to_datetime(filtered_revenue['Date'])
                mask = (filtered_revenue['Date'] >= pd.to_datetime(start_date)) & (filtered_revenue['Date'] <= pd.to_datetime(end_date))
                filtered_revenue = filtered_revenue[mask]
            except Exception:
                pass  # Use all data if date filtering fails
        
        # Find revenue column
        revenue_column = self._get_revenue_column(filtered_revenue)
        if not revenue_column:
            return details
        
        # Process each business unit
        for business_unit, settings in business_settings.items():
            if not settings.get('enabled', True):
                continue
            
            # Filter revenue for this business unit
            if 'Business Unit' in filtered_revenue.columns:
                unit_revenue = filtered_revenue[filtered_revenue['Business Unit'] == business_unit]
            else:
                unit_revenue = filtered_revenue
            
            if unit_revenue.empty:
                continue
            
            # Lead Generation commissions
            if 'Lead Generated By' in unit_revenue.columns and settings.get('lead_gen_rate', 0) > 0:
                lead_details = self._calculate_commission_type(
                    unit_revenue, employee_name, 'Lead Generated By', 
                    business_unit, settings['lead_gen_rate'], revenue_column,
                    CommissionType.LEAD_GENERATION, employee_overrides, 'lead_gen'
                )
                details.extend(lead_details)
            
            # Sales commissions  
            if 'Sold By' in unit_revenue.columns and settings.get('sold_by_rate', 0) > 0:
                sales_details = self._calculate_commission_type(
                    unit_revenue, employee_name, 'Sold By',
                    business_unit, settings['sold_by_rate'], revenue_column,
                    CommissionType.SALES, employee_overrides, 'sold_by'
                )
                details.extend(sales_details)
            
            # Work Done commissions
            if 'Assigned Technicians' in unit_revenue.columns and settings.get('work_done_rate', 0) > 0:
                work_details = self._calculate_work_done_commissions(
                    unit_revenue, employee_name, business_unit, 
                    settings['work_done_rate'], revenue_column, employee_overrides
                )
                details.extend(work_details)
        
        return details
    
    def _calculate_commission_type(
        self,
        revenue_df: pd.DataFrame,
        employee_name: str, 
        column_name: str,
        business_unit: str,
        base_rate: float,
        revenue_column: str,
        commission_type: CommissionType,
        employee_overrides: Dict,
        override_type: str
    ) -> List[CommissionDetail]:
        """Calculate commissions for a specific type (lead gen, sales)"""
        
        details = []
        
        for _, row in revenue_df.iterrows():
            assigned_employee = row.get(column_name)
            if pd.notna(assigned_employee) and assigned_employee == employee_name:
                revenue_amount = pd.to_numeric(row.get(revenue_column, 0), errors='coerce')
                if pd.isna(revenue_amount):
                    revenue_amount = 0
                
                # Get commission rate (check for overrides)
                rate = self._get_employee_commission_rate(
                    employee_name, business_unit, override_type, base_rate, employee_overrides
                )
                
                commission_amount = Decimal(str(revenue_amount)) * (Decimal(str(rate)) / 100)
                
                detail = CommissionDetail(
                    employee_id=0,  # Will be set by caller
                    employee_name=employee_name,
                    commission_type=commission_type,
                    business_unit=business_unit,
                    revenue_amount=Decimal(str(revenue_amount)),
                    commission_rate=Decimal(str(rate)),
                    commission_amount=commission_amount,
                    job_number=row.get('Job Number', 'Unknown')
                )
                details.append(detail)
        
        return details
    
    def _calculate_work_done_commissions(
        self,
        revenue_df: pd.DataFrame,
        employee_name: str,
        business_unit: str,
        base_rate: float,
        revenue_column: str,
        employee_overrides: Dict
    ) -> List[CommissionDetail]:
        """Calculate work done commissions (handles multiple technicians per job)"""
        
        details = []
        
        for _, row in revenue_df.iterrows():
            techs_str = row.get('Assigned Technicians')
            if pd.notna(techs_str):
                # Split technicians
                technicians = [t.strip() for t in str(techs_str).replace('&', ',').split(',') if t.strip()]
                
                if employee_name in technicians:
                    revenue_amount = pd.to_numeric(row.get(revenue_column, 0), errors='coerce')
                    if pd.isna(revenue_amount):
                        revenue_amount = 0
                    
                    # Get commission rate
                    rate = self._get_employee_commission_rate(
                        employee_name, business_unit, 'work_done', base_rate, employee_overrides
                    )
                    
                    commission_amount = Decimal(str(revenue_amount)) * (Decimal(str(rate)) / 100)
                    
                    detail = CommissionDetail(
                        employee_id=0,
                        employee_name=employee_name,
                        commission_type=CommissionType.WORK_DONE,
                        business_unit=business_unit,
                        revenue_amount=Decimal(str(revenue_amount)),
                        commission_rate=Decimal(str(rate)),
                        commission_amount=commission_amount,
                        job_number=row.get('Job Number', 'Unknown')
                    )
                    details.append(detail)
        
        return details
    
    async def _calculate_employee_efficiency_pay(
        self,
        employee_name: str,
        employee_row: pd.Series,
        timesheet_df: pd.DataFrame,
        timesheet_overrides: Dict,
        commission_total: Decimal
    ) -> Optional[EfficiencyPayDetail]:
        """Calculate efficiency pay for an employee"""
        
        # Get employee details
        hourly_rate = Decimal(str(employee_row.get('Hourly Rate', 0)))
        commission_plan = employee_row.get('Commission Plan', 'Hourly + Commission')
        
        # Get hours (with overrides)
        regular_hours, ot_hours, dt_hours = self._get_employee_hours_with_overrides(
            employee_name, timesheet_df, timesheet_overrides
        )
        
        # Calculate hourly pay with proper multipliers
        regular_pay = regular_hours * hourly_rate
        ot_pay = ot_hours * hourly_rate * Decimal('1.5')
        dt_pay = dt_hours * hourly_rate * Decimal('2.0')
        hourly_pay = regular_pay + ot_pay + dt_pay
        total_hours = regular_hours + ot_hours + dt_hours
        
        # Calculate final pay based on plan
        if commission_plan == 'Efficiency Pay':
            final_pay = max(hourly_pay, commission_total)
            efficiency_pay = final_pay - hourly_pay
        else:  # Hourly + Commission
            final_pay = hourly_pay + commission_total
            efficiency_pay = Decimal('0.00')
        
        return EfficiencyPayDetail(
            employee_id=0,  # Will be set by caller
            employee_name=employee_name,
            commission_plan=commission_plan,
            regular_hours=regular_hours,
            ot_hours=ot_hours,
            dt_hours=dt_hours,
            total_hours=total_hours,
            hourly_rate=hourly_rate,
            hourly_pay=hourly_pay,
            commission_total=commission_total,
            efficiency_pay=efficiency_pay,
            final_pay=final_pay
        )
    
    def _get_employee_hours_with_overrides(
        self, 
        employee_name: str, 
        timesheet_df: pd.DataFrame,
        overrides: Dict
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Get employee hours with hour overrides applied"""
        
        # Check for overrides first
        if employee_name in overrides:
            override_data = overrides[employee_name]
            return (
                Decimal(str(override_data.get('regular_hours', 0))),
                Decimal(str(override_data.get('ot_hours', 0))),
                Decimal(str(override_data.get('dt_hours', 0)))
            )
        
        # Get from timesheet data
        if 'Employee Name' not in timesheet_df.columns:
            return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')
        
        emp_timesheet = timesheet_df[timesheet_df['Employee Name'] == employee_name]
        if emp_timesheet.empty:
            return Decimal('0.00'), Decimal('0.00'), Decimal('0.00')
        
        # Sum hours across all entries for this employee
        regular_hours = Decimal('0.00')
        ot_hours = Decimal('0.00') 
        dt_hours = Decimal('0.00')
        
        # Handle different column naming conventions
        if 'Reg Hours' in emp_timesheet.columns:
            regular_hours = Decimal(str(pd.to_numeric(emp_timesheet['Reg Hours'], errors='coerce').fillna(0).sum()))
        elif 'Regular Hours' in emp_timesheet.columns:
            regular_hours = Decimal(str(pd.to_numeric(emp_timesheet['Regular Hours'], errors='coerce').fillna(0).sum()))
        
        if 'OT Hours' in emp_timesheet.columns:
            ot_hours = Decimal(str(pd.to_numeric(emp_timesheet['OT Hours'], errors='coerce').fillna(0).sum()))
        
        if 'DT Hours' in emp_timesheet.columns:
            dt_hours = Decimal(str(pd.to_numeric(emp_timesheet['DT Hours'], errors='coerce').fillna(0).sum()))
        
        return regular_hours, ot_hours, dt_hours
    
    def _get_revenue_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect the revenue column in the dataframe"""
        revenue_keywords = ['revenue', 'total', 'amount', 'sales']
        
        for col in df.columns:
            if any(keyword in col.lower() for keyword in revenue_keywords):
                return col
        return None
    
    def _get_employee_commission_rate(
        self, 
        employee: str, 
        business_unit: str, 
        commission_type: str,
        default_rate: float, 
        overrides: Dict
    ) -> float:
        """Get commission rate for an employee, checking for overrides"""
        
        # Map commission types to override keys
        type_map = {
            'lead_gen': 'lead_gen_rate',
            'sold_by': 'sold_by_rate', 
            'work_done': 'work_done_rate'
        }
        
        override_key = type_map.get(commission_type)
        use_override_key = f"use_{commission_type}_override"
        
        # Check if there's an override for this employee in this business unit
        if (business_unit in overrides and 
            employee in overrides[business_unit] and
            overrides[business_unit][employee].get(use_override_key, False)):
            
            return overrides[business_unit][employee].get(override_key, default_rate)
        
        return default_rate