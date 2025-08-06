"""Commission calculation business service."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger


class CommissionService:
    """Handles all commission calculation business logic."""

    def __init__(self):
        self.commission_rates = {}
        self.business_units = {}
        self.employees = {}

    def set_commission_rates(self, rates: Dict[str, Dict[str, float]]) -> None:
        """Set commission rates for business units.

        Args:
            rates: Dict mapping business unit names to commission rate configs
        """
        self.commission_rates = rates
        logger.info(f"Commission rates configured for {len(rates)} business units")

    def add_business_unit(self, name: str, revenue: Decimal,
                         lead_gen_by: Optional[str] = None,
                         sold_by: Optional[str] = None,
                         assigned_techs: Optional[List[str]] = None) -> None:
        """Add business unit with revenue data.

        Args:
            name: Business unit name
            revenue: Total revenue for the unit
            lead_gen_by: Employee who generated the lead
            sold_by: Employee who made the sale
            assigned_techs: List of technicians assigned to work
        """
        self.business_units[name] = {
            'revenue': revenue,
            'lead_gen_by': lead_gen_by,
            'sold_by': sold_by,
            'assigned_techs': assigned_techs or []
        }
        logger.debug(f"Added business unit: {name} with revenue ${revenue}")

    def add_employee(self, name: str, hourly_rate: Decimal = Decimal('0'),
                    regular_hours: Decimal = Decimal('0'),
                    ot_hours: Decimal = Decimal('0'),
                    dt_hours: Decimal = Decimal('0'),
                    is_helper: bool = False,
                    is_excluded_from_payroll: bool = False) -> None:
        """Add employee with timesheet data.

        Args:
            name: Employee name
            hourly_rate: Employee hourly rate
            regular_hours: Regular hours worked
            ot_hours: Overtime hours worked
            dt_hours: Double time hours worked
            is_helper: Helper/Apprentice status (not eligible for commissions)
            is_excluded_from_payroll: Office employee excluded from payroll calculations
        """
        self.employees[name] = {
            'hourly_rate': hourly_rate,
            'regular_hours': regular_hours,
            'ot_hours': ot_hours,
            'dt_hours': dt_hours,
            'total_hours': regular_hours + ot_hours + dt_hours,
            'is_helper': is_helper,
            'is_excluded_from_payroll': is_excluded_from_payroll
        }
        logger.debug(f"Added employee: {name} with {regular_hours + ot_hours + dt_hours} total hours")

    def calculate_lead_generation_commission(self, business_unit: str,
                                           employee: str) -> Decimal:
        """Calculate lead generation commission for an employee.

        Args:
            business_unit: Name of business unit
            employee: Employee name

        Returns:
            Commission amount as Decimal
        """
        if (business_unit not in self.business_units or
            business_unit not in self.commission_rates):
            return Decimal('0')

        # Check if employee is a helper/apprentice or excluded from payroll
        if employee in self.employees:
            emp_data = self.employees[employee]
            if emp_data.get('is_helper', False):
                logger.debug(f"Lead gen commission skipped for helper/apprentice: {employee}")
                return Decimal('0')
            if emp_data.get('is_excluded_from_payroll', False):
                logger.debug(f"Lead gen commission skipped for payroll-excluded employee: {employee}")
                return Decimal('0')

        unit_data = self.business_units[business_unit]
        rates = self.commission_rates[business_unit]

        if unit_data.get('lead_gen_by') != employee:
            return Decimal('0')

        revenue = unit_data['revenue']
        rate = Decimal(str(rates.get('lead_generated_by', 0))) / Decimal('100')

        commission = revenue * rate
        commission = commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        logger.debug(f"Lead gen commission for {employee} on {business_unit}: ${commission}")
        return commission

    def calculate_sales_commission(self, business_unit: str,
                                 employee: str) -> Decimal:
        """Calculate sales commission for an employee.

        Args:
            business_unit: Name of business unit
            employee: Employee name

        Returns:
            Commission amount as Decimal
        """
        if (business_unit not in self.business_units or
            business_unit not in self.commission_rates):
            return Decimal('0')

        # Check if employee is a helper/apprentice or excluded from payroll
        if employee in self.employees:
            emp_data = self.employees[employee]
            if emp_data.get('is_helper', False):
                logger.debug(f"Sales commission skipped for helper/apprentice: {employee}")
                return Decimal('0')
            if emp_data.get('is_excluded_from_payroll', False):
                logger.debug(f"Sales commission skipped for payroll-excluded employee: {employee}")
                return Decimal('0')

        unit_data = self.business_units[business_unit]
        rates = self.commission_rates[business_unit]

        if unit_data.get('sold_by') != employee:
            return Decimal('0')

        revenue = unit_data['revenue']
        rate = Decimal(str(rates.get('sold_by', 0))) / Decimal('100')

        commission = revenue * rate
        commission = commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        logger.debug(f"Sales commission for {employee} on {business_unit}: ${commission}")
        return commission

    def calculate_work_done_commission(self, business_unit: str,
                                     employee: str) -> Decimal:
        """Calculate work done commission for an employee.

        Args:
            business_unit: Name of business unit
            employee: Employee name

        Returns:
            Commission amount as Decimal
        """
        if (business_unit not in self.business_units or
            business_unit not in self.commission_rates):
            return Decimal('0')

        # Check if employee is a helper/apprentice or excluded from payroll
        if employee in self.employees:
            emp_data = self.employees[employee]
            if emp_data.get('is_helper', False):
                logger.debug(f"Work done commission skipped for helper/apprentice: {employee}")
                return Decimal('0')
            if emp_data.get('is_excluded_from_payroll', False):
                logger.debug(f"Work done commission skipped for payroll-excluded employee: {employee}")
                return Decimal('0')

        unit_data = self.business_units[business_unit]
        rates = self.commission_rates[business_unit]
        assigned_techs = unit_data.get('assigned_techs', [])

        if employee not in assigned_techs or len(assigned_techs) == 0:
            return Decimal('0')

        # Filter out helpers/apprentices and payroll-excluded employees from the split
        eligible_techs = []
        for tech in assigned_techs:
            if tech not in self.employees:
                eligible_techs.append(tech)
            else:
                emp_data = self.employees[tech]
                if not emp_data.get('is_helper', False) and not emp_data.get('is_excluded_from_payroll', False):
                    eligible_techs.append(tech)
        
        if len(eligible_techs) == 0:
            logger.debug(f"No eligible technicians for work done commission on {business_unit}")
            return Decimal('0')

        revenue = unit_data['revenue']
        rate = Decimal(str(rates.get('work_done', 0))) / Decimal('100')

        # Split commission equally among eligible technicians only
        total_commission = revenue * rate
        per_tech_commission = total_commission / Decimal(str(len(eligible_techs)))
        per_tech_commission = per_tech_commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        logger.debug(f"Work done commission for {employee} on {business_unit}: ${per_tech_commission}")
        return per_tech_commission

    def calculate_total_employee_commission(self, employee: str) -> Dict[str, Any]:
        """Calculate total commission for an employee across all business units.

        Args:
            employee: Employee name

        Returns:
            Dictionary with commission breakdown and totals
        """
        # Check if employee is a helper/apprentice or excluded from payroll
        if employee in self.employees:
            emp_data = self.employees[employee]
            if emp_data.get('is_helper', False):
                logger.debug(f"Total commission calculation skipped for helper/apprentice: {employee}")
                return {
                    'lead_generation': Decimal('0'),
                    'sales': Decimal('0'),
                    'work_done': Decimal('0'),
                    'total': Decimal('0'),
                    'details': [],
                    'is_helper': True,
                    'is_excluded_from_payroll': False
                }
            if emp_data.get('is_excluded_from_payroll', False):
                logger.debug(f"Total commission calculation skipped for payroll-excluded employee: {employee}")
                return {
                    'lead_generation': Decimal('0'),
                    'sales': Decimal('0'),
                    'work_done': Decimal('0'),
                    'total': Decimal('0'),
                    'details': [],
                    'is_helper': False,
                    'is_excluded_from_payroll': True
                }

        commission_breakdown = {
            'lead_generation': Decimal('0'),
            'sales': Decimal('0'),
            'work_done': Decimal('0'),
            'total': Decimal('0'),
            'details': [],
            'is_helper': False,
            'is_excluded_from_payroll': False
        }

        for business_unit in self.business_units:
            lead_comm = self.calculate_lead_generation_commission(business_unit, employee)
            sales_comm = self.calculate_sales_commission(business_unit, employee)
            work_comm = self.calculate_work_done_commission(business_unit, employee)

            unit_total = lead_comm + sales_comm + work_comm

            if unit_total > 0:
                commission_breakdown['details'].append({
                    'business_unit': business_unit,
                    'lead_generation': lead_comm,
                    'sales': sales_comm,
                    'work_done': work_comm,
                    'unit_total': unit_total
                })

            commission_breakdown['lead_generation'] += lead_comm
            commission_breakdown['sales'] += sales_comm
            commission_breakdown['work_done'] += work_comm

        commission_breakdown['total'] = (
            commission_breakdown['lead_generation'] +
            commission_breakdown['sales'] +
            commission_breakdown['work_done']
        )

        logger.info(f"Total commission for {employee}: ${commission_breakdown['total']}")
        return commission_breakdown

    def calculate_labor_cost(self, employee: str) -> Dict[str, Decimal]:
        """Calculate labor costs for an employee.

        Args:
            employee: Employee name

        Returns:
            Dictionary with labor cost breakdown
        """
        if employee not in self.employees:
            return {
                'regular_cost': Decimal('0'),
                'ot_cost': Decimal('0'),
                'dt_cost': Decimal('0'),
                'total_cost': Decimal('0')
            }

        emp_data = self.employees[employee]
        hourly_rate = emp_data['hourly_rate']

        regular_cost = emp_data['regular_hours'] * hourly_rate
        ot_cost = emp_data['ot_hours'] * hourly_rate * Decimal('1.5')
        dt_cost = emp_data['dt_hours'] * hourly_rate * Decimal('2.0')
        total_cost = regular_cost + ot_cost + dt_cost

        return {
            'regular_cost': regular_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'ot_cost': ot_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'dt_cost': dt_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_cost': total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        }

    def get_commission_summary(self) -> Dict[str, Any]:
        """Get overall commission summary for all employees.

        Returns:
            Summary statistics and breakdowns
        """
        summary = {
            'total_revenue': Decimal('0'),
            'total_commissions': Decimal('0'),
            'total_labor_cost': Decimal('0'),
            'employees': [],
            'business_units_count': len(self.business_units),
            'employees_count': len(self.employees)
        }

        # Calculate total revenue
        for unit_data in self.business_units.values():
            summary['total_revenue'] += unit_data['revenue']

        # Calculate per-employee data
        for employee in self.employees:
            commission_data = self.calculate_total_employee_commission(employee)
            labor_data = self.calculate_labor_cost(employee)

            employee_summary = {
                'name': employee,
                'commission': commission_data['total'],
                'labor_cost': labor_data['total_cost'],
                'total_earnings': commission_data['total'] + labor_data['total_cost'],
                'commission_breakdown': commission_data
            }

            summary['employees'].append(employee_summary)
            summary['total_commissions'] += commission_data['total']
            summary['total_labor_cost'] += labor_data['total_cost']

        # Calculate profit metrics
        summary['gross_profit'] = summary['total_revenue'] - summary['total_labor_cost'] - summary['total_commissions']
        if summary['total_revenue'] > 0:
            summary['profit_margin'] = (summary['gross_profit'] / summary['total_revenue'] * 100).quantize(
                Decimal('0.1'), rounding=ROUND_HALF_UP
            )
        else:
            summary['profit_margin'] = Decimal('0')

        logger.info(
            f"Commission summary: {summary['employees_count']} employees, "
            f"${summary['total_commissions']} total commissions"
        )
        return summary

    def validate_commission_setup(self) -> Tuple[bool, List[str]]:
        """Validate commission setup for completeness and consistency.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not self.commission_rates:
            errors.append("No commission rates configured")

        if not self.business_units:
            errors.append("No business units added")

        if not self.employees:
            errors.append("No employees added")

        # Check for business units without commission rates
        for unit_name in self.business_units:
            if unit_name not in self.commission_rates:
                errors.append(f"Business unit '{unit_name}' has no commission rates configured")

        # Check for employees referenced but not in employee list
        all_referenced_employees = set()
        for unit_data in self.business_units.values():
            if unit_data.get('lead_gen_by'):
                all_referenced_employees.add(unit_data['lead_gen_by'])
            if unit_data.get('sold_by'):
                all_referenced_employees.add(unit_data['sold_by'])
            all_referenced_employees.update(unit_data.get('assigned_techs', []))

        for emp in all_referenced_employees:
            if emp not in self.employees:
                errors.append(f"Employee '{emp}' referenced in business units but not in employee list")

        return len(errors) == 0, errors
