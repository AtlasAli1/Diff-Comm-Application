import pytest
from decimal import Decimal
from datetime import datetime
from models.employee import Employee
from models.business_unit import BusinessUnit, Commission
from models.calculator import CommissionCalculator

class TestEmployee:
    """Test cases for Employee model"""
    
    def test_employee_creation(self):
        """Test basic employee creation"""
        emp = Employee(
            name="John Doe",
            hourly_rate=Decimal('25.00'),
            regular_hours=Decimal('40'),
            ot_hours=Decimal('5'),
            dt_hours=Decimal('2')
        )
        
        assert emp.name == "John Doe"
        assert emp.hourly_rate == Decimal('25.00')
        assert emp.total_hours == Decimal('47')
    
    def test_labor_cost_calculation(self):
        """Test labor cost calculations"""
        emp = Employee(
            name="Jane Smith",
            hourly_rate=Decimal('30.00'),
            regular_hours=Decimal('40'),
            ot_hours=Decimal('8'),
            dt_hours=Decimal('4')
        )
        
        expected_regular = Decimal('40') * Decimal('30.00')  # 1200.00
        expected_ot = Decimal('8') * Decimal('30.00') * Decimal('1.5')  # 360.00
        expected_dt = Decimal('4') * Decimal('30.00') * Decimal('2.0')  # 240.00
        expected_total = expected_regular + expected_ot + expected_dt  # 1800.00
        
        assert emp.regular_cost == expected_regular
        assert emp.overtime_cost == expected_ot
        assert emp.double_time_cost == expected_dt
        assert emp.total_labor_cost == expected_total
    
    def test_employee_validation(self):
        """Test employee input validation"""
        # Test name validation
        with pytest.raises(ValueError):
            Employee(name="")
        
        # Test negative rate validation
        with pytest.raises(ValueError):
            Employee(name="Test", hourly_rate=Decimal('-5.00'))

class TestBusinessUnit:
    """Test cases for BusinessUnit model"""
    
    def test_business_unit_creation(self):
        """Test basic business unit creation"""
        unit = BusinessUnit(
            name="Project Alpha",
            revenue=Decimal('100000.00'),
            commission_rate=Decimal('10.0')
        )
        
        assert unit.name == "Project Alpha"
        assert unit.revenue == Decimal('100000.00')
        assert unit.commission_rate == Decimal('10.0')
    
    def test_commission_calculation(self):
        """Test commission amount calculation"""
        unit = BusinessUnit(
            name="Project Beta",
            revenue=Decimal('50000.00'),
            commission_rate=Decimal('15.0')
        )
        
        expected_commission = Decimal('50000.00') * Decimal('15.0') / Decimal('100')
        assert unit.commission_amount == expected_commission
    
    def test_commission_rate_validation(self):
        """Test commission rate validation"""
        # Test rate over 100%
        with pytest.raises(ValueError):
            BusinessUnit(name="Test", commission_rate=Decimal('150.0'))
        
        # Test negative rate
        with pytest.raises(ValueError):
            BusinessUnit(name="Test", commission_rate=Decimal('-5.0'))

class TestCommission:
    """Test cases for Commission model"""
    
    def test_commission_creation(self):
        """Test basic commission creation"""
        commission = Commission(
            employee_id="emp_123",
            business_unit_id="unit_456",
            amount=Decimal('1000.00'),
            percentage=Decimal('100.0'),
            period_start=datetime.now(),
            period_end=datetime.now()
        )
        
        assert commission.employee_id == "emp_123"
        assert commission.amount == Decimal('1000.00')
        assert commission.adjusted_amount == Decimal('1000.00')
    
    def test_adjusted_amount_calculation(self):
        """Test adjusted commission amount with percentage"""
        commission = Commission(
            employee_id="emp_123",  
            business_unit_id="unit_456",
            amount=Decimal('1000.00'),
            percentage=Decimal('75.0'),
            period_start=datetime.now(),
            period_end=datetime.now()
        )
        
        expected_adjusted = Decimal('1000.00') * Decimal('75.0') / Decimal('100')
        assert commission.adjusted_amount == expected_adjusted
    
    def test_commission_approval(self):
        """Test commission approval workflow"""
        commission = Commission(
            employee_id="emp_123",
            business_unit_id="unit_456", 
            amount=Decimal('500.00'),
            period_start=datetime.now(),
            period_end=datetime.now()
        )
        
        assert commission.status == 'pending'
        
        commission.approve("manager_user")
        
        assert commission.status == 'approved'
        assert commission.approved_by == "manager_user"
        assert commission.approved_at is not None

class TestCommissionCalculator:
    """Test cases for CommissionCalculator model"""
    
    def test_calculator_initialization(self):
        """Test calculator initialization"""
        calc = CommissionCalculator()
        
        assert len(calc.employees) == 0
        assert len(calc.business_units) == 0
        assert len(calc.commissions) == 0
    
    def test_add_employee(self):
        """Test adding employee to calculator"""
        calc = CommissionCalculator()
        emp = Employee(name="Test Employee", hourly_rate=Decimal('20.00'))
        
        calc.add_employee(emp)
        
        assert len(calc.employees) == 1
        assert emp.id in calc.employees
    
    def test_add_business_unit(self):
        """Test adding business unit to calculator"""
        calc = CommissionCalculator()
        unit = BusinessUnit(name="Test Unit", revenue=Decimal('25000.00'))
        
        calc.add_business_unit(unit)
        
        assert len(calc.business_units) == 1
        assert unit.id in calc.business_units
    
    def test_find_employee_by_name(self):
        """Test finding employee by name"""
        calc = CommissionCalculator()
        emp = Employee(name="John Doe", hourly_rate=Decimal('25.00'))
        calc.add_employee(emp)
        
        found_emp = calc.find_employee_by_name("John Doe")
        assert found_emp is not None
        assert found_emp.name == "John Doe"
        
        not_found = calc.find_employee_by_name("Jane Smith")
        assert not_found is None
    
    def test_analytics_data(self):
        """Test analytics data generation"""
        calc = CommissionCalculator()
        
        # Add test data
        emp = Employee(name="Test Emp", hourly_rate=Decimal('30.00'), regular_hours=Decimal('40'))
        unit = BusinessUnit(name="Test Unit", revenue=Decimal('10000.00'), commission_rate=Decimal('10.0'))
        
        calc.add_employee(emp)
        calc.add_business_unit(unit)
        
        analytics = calc.get_analytics_data()
        
        assert 'kpis' in analytics
        assert analytics['kpis']['total_revenue'] > 0
        assert analytics['employees'] == 1
        assert analytics['business_units'] == 1

class TestDataValidation:
    """Test cases for data validation"""
    
    def test_timesheet_validation(self):
        """Test timesheet data validation"""
        from utils.validators import DataValidator
        import pandas as pd
        
        # Valid data
        valid_data = pd.DataFrame({
            'Employee Name': ['John Doe', 'Jane Smith'],
            'Regular Hours': [40, 38],
            'OT Hours': [5, 0],
            'DT Hours': [0, 2]
        })
        
        is_valid, errors, cleaned_df = DataValidator.validate_timesheet_data(valid_data)
        
        assert is_valid == True
        assert len(errors) == 0
        assert len(cleaned_df) == 2
    
    def test_revenue_validation(self):
        """Test revenue data validation"""
        from utils.validators import DataValidator
        import pandas as pd
        
        # Valid revenue data
        valid_data = pd.DataFrame({
            'Business Unit': ['Project A', 'Project B'],
            'Revenue': [50000, 75000]
        })
        
        is_valid, errors, cleaned_df = DataValidator.validate_revenue_data(valid_data)
        
        assert is_valid == True
        assert len(errors) == 0
        assert len(cleaned_df) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])