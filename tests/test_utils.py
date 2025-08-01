import pytest
import pandas as pd
import json
import tempfile
import os
from decimal import Decimal
from datetime import datetime
from utils.validators import DataValidator
from utils.export import ExportManager
from utils.database import DatabaseManager

class TestDataValidator:
    """Test cases for DataValidator utility"""
    
    def test_validate_commission_rates(self):
        """Test commission rates validation"""
        # Valid rates
        valid_rates = {'Unit A': 10.0, 'Unit B': 15.5, 'Unit C': 8.0}
        is_valid, errors = DataValidator.validate_commission_rates(valid_rates)
        
        assert is_valid == True
        assert len(errors) == 0
        
        # Invalid rates (negative)
        invalid_rates = {'Unit A': -5.0, 'Unit B': 10.0}
        is_valid, errors = DataValidator.validate_commission_rates(invalid_rates)
        
        assert is_valid == False
        assert len(errors) > 0
        
        # Invalid rates (over 100%)
        invalid_rates = {'Unit A': 150.0}
        is_valid, errors = DataValidator.validate_commission_rates(invalid_rates)
        
        assert is_valid == False
        assert len(errors) > 0
    
    def test_validate_hourly_rates(self):
        """Test hourly rates validation"""
        # Valid employee data
        valid_employees = {
            'emp1': {'name': 'John', 'hourly_rate': 25.0},
            'emp2': {'name': 'Jane', 'hourly_rate': 30.0}
        }
        
        is_valid, messages = DataValidator.validate_hourly_rates(valid_employees)
        assert is_valid == True
        
        # Invalid rates (zero)
        invalid_employees = {
            'emp1': {'name': 'John', 'hourly_rate': 0.0}
        }
        
        is_valid, messages = DataValidator.validate_hourly_rates(invalid_employees)
        assert is_valid == False
    
    def test_validate_commission_split(self):
        """Test commission split validation"""
        # Valid split (sums to 100%)
        valid_split = {
            'emp1': Decimal('60.0'),
            'emp2': Decimal('40.0')
        }
        
        is_valid, message = DataValidator.validate_commission_split(valid_split)
        assert is_valid == True
        
        # Invalid split (doesn't sum to 100%)
        invalid_split = {
            'emp1': Decimal('60.0'),
            'emp2': Decimal('30.0')
        }
        
        is_valid, message = DataValidator.validate_commission_split(invalid_split)
        assert is_valid == False
    
    def test_validate_date_range(self):
        """Test date range validation"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        is_valid, message = DataValidator.validate_date_range(start_date, end_date)
        assert is_valid == True
        
        # Invalid range (start after end)
        is_valid, message = DataValidator.validate_date_range(end_date, start_date)
        assert is_valid == False
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Valid filename
        clean_name = DataValidator.sanitize_filename("report_2024.xlsx")
        assert clean_name == "report_2024.xlsx"
        
        # Filename with invalid characters
        dirty_name = "report<>2024|?.xlsx"
        clean_name = DataValidator.sanitize_filename(dirty_name)
        assert "<" not in clean_name
        assert ">" not in clean_name
        assert "|" not in clean_name
        assert "?" not in clean_name

class TestExportManager:
    """Test cases for ExportManager utility"""
    
    def test_export_to_csv(self):
        """Test CSV export functionality"""
        export_mgr = ExportManager()
        
        test_data = [
            {'name': 'John', 'amount': 1000.0},
            {'name': 'Jane', 'amount': 1500.0}
        ]
        
        csv_output = export_mgr.export_to_csv(test_data)
        
        assert 'name,amount' in csv_output
        assert 'John,1000.0' in csv_output
        assert 'Jane,1500.0' in csv_output
    
    def test_export_to_json(self):
        """Test JSON export functionality"""
        export_mgr = ExportManager()
        
        test_data = {
            'employees': ['John', 'Jane'],
            'total': 2500.0
        }
        
        json_output = export_mgr.export_to_json(test_data)
        parsed_data = json.loads(json_output)
        
        assert parsed_data['employees'] == ['John', 'Jane']
        assert parsed_data['total'] == 2500.0
    
    def test_generate_payroll_export(self):
        """Test payroll export generation"""
        export_mgr = ExportManager()
        
        commission_data = [
            {
                'employee_name': 'John Doe',
                'employee_id': 'EMP001',
                'regular_hours': 40,
                'ot_hours': 5,
                'dt_hours': 0,
                'hourly_rate': 25.0,
                'labor_cost': 1187.50,
                'commission_amount': 500.0,
                'total_earnings': 1687.50,
                'department': 'Sales'
            }
        ]
        
        payroll_df = export_mgr.generate_payroll_export(
            commission_data, 
            '2024-01-01', 
            '2024-01-31'
        )
        
        assert len(payroll_df) == 1
        assert 'Employee Name' in payroll_df.columns
        assert 'Total Earnings' in payroll_df.columns
        assert payroll_df.iloc[0]['Employee Name'] == 'John Doe'
    
    def test_generate_executive_summary(self):
        """Test executive summary generation"""
        export_mgr = ExportManager()
        
        analytics_data = {
            'kpis': {
                'total_revenue': 100000.0,
                'total_labor_cost': 25000.0,
                'total_commissions': 10000.0,
                'gross_profit': 65000.0,
                'profit_margin': 65.0
            },
            'employees': 5,
            'business_units': 3,
            'active_commissions': 15,
            'period': {
                'start': '2024-01-01',
                'end': '2024-01-31'
            }
        }
        
        summary = export_mgr.generate_executive_summary(analytics_data)
        
        assert 'Executive Commission Summary' in summary
        assert '$100,000.00' in summary
        assert '65.0%' in summary

class TestDatabaseManager:
    """Test cases for DatabaseManager utility"""
    
    def test_database_initialization(self):
        """Test database initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            backup_dir = os.path.join(temp_dir, "backups")
            
            db_manager = DatabaseManager(db_path, backup_dir)
            
            # Check if database file was created
            assert os.path.exists(db_path)
            # Check if backup directory was created
            assert os.path.exists(backup_dir)
    
    def test_save_and_get_employees(self):
        """Test saving and retrieving employees"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db_manager = DatabaseManager(db_path)
            
            # Test employee data
            employee_data = {
                'id': 'emp_001',
                'name': 'John Doe',
                'hourly_rate': 25.0,
                'department': 'Sales',
                'is_active': True,
                'regular_hours': 40.0,
                'ot_hours': 5.0,
                'dt_hours': 0.0
            }
            
            # Save employee
            success = db_manager.save_employee(employee_data)
            assert success == True
            
            # Retrieve employees
            employees = db_manager.get_employees()
            assert len(employees) == 1
            assert employees[0]['name'] == 'John Doe'
    
    def test_save_and_get_business_units(self):
        """Test saving and retrieving business units"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db_manager = DatabaseManager(db_path)
            
            # Test business unit data
            unit_data = {
                'id': 'unit_001',
                'name': 'Project Alpha',
                'commission_rate': 10.0,
                'category': 'Software',
                'is_active': True,
                'revenue': 50000.0
            }
            
            # Save business unit
            success = db_manager.save_business_unit(unit_data)
            assert success == True
            
            # Retrieve business units
            units = db_manager.get_business_units()
            assert len(units) == 1
            assert units[0]['name'] == 'Project Alpha'
    
    def test_audit_logging(self):
        """Test audit log functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db_manager = DatabaseManager(db_path)
            
            # Log an action
            db_manager.log_action('test_action', {'key': 'value'}, 'test_user')
            
            # Retrieve audit logs
            logs = db_manager.get_audit_log(10)
            assert len(logs) == 1
            assert logs[0]['action'] == 'test_action'
            assert logs[0]['user'] == 'test_user'
            assert logs[0]['details']['key'] == 'value'
    
    def test_backup_creation(self):
        """Test database backup functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            backup_dir = os.path.join(temp_dir, "backups")
            
            db_manager = DatabaseManager(db_path, backup_dir)
            
            # Create a backup
            backup_path = db_manager.create_backup("test_backup")
            
            # Check if backup file was created
            assert os.path.exists(backup_path)
            assert "test_backup" in backup_path

class TestIntegration:
    """Integration tests combining multiple components"""
    
    def test_end_to_end_calculation(self):
        """Test complete calculation workflow"""
        from models.calculator import CommissionCalculator
        from models.employee import Employee
        from models.business_unit import BusinessUnit
        
        # Create calculator
        calc = CommissionCalculator()
        
        # Add employees
        emp1 = Employee(
            name="John Doe",
            hourly_rate=Decimal('25.00'),
            regular_hours=Decimal('40'),
            ot_hours=Decimal('5')
        )
        
        emp2 = Employee(
            name="Jane Smith", 
            hourly_rate=Decimal('30.00'),
            regular_hours=Decimal('38'),
            ot_hours=Decimal('2')
        )
        
        calc.add_employee(emp1)
        calc.add_employee(emp2)
        
        # Add business unit
        unit = BusinessUnit(
            name="Project Alpha",
            revenue=Decimal('100000.00'),
            commission_rate=Decimal('10.0')
        )
        
        calc.add_business_unit(unit)
        
        # Calculate commissions
        period_start = datetime(2024, 1, 1)
        period_end = datetime(2024, 1, 31)
        
        commissions = calc.calculate_commissions(period_start, period_end)
        
        # Verify results
        assert len(commissions) > 0
        
        # Check analytics
        analytics = calc.get_analytics_data()
        assert analytics['kpis']['total_revenue'] == 100000.0
        assert analytics['employees'] == 2
        assert analytics['business_units'] == 1
    
    def test_data_export_import_cycle(self):
        """Test complete data export/import cycle"""
        from models.calculator import CommissionCalculator
        from models.employee import Employee
        
        # Create calculator with data
        calc = CommissionCalculator()
        emp = Employee(name="Test Employee", hourly_rate=Decimal('25.00'))
        calc.add_employee(emp)
        
        # Export data
        export_data = calc.export_to_dict()
        
        # Verify export structure
        assert 'employees' in export_data
        assert 'business_units' in export_data
        assert 'analytics' in export_data
        
        # Verify employee data
        assert len(export_data['employees']) == 1
        emp_data = list(export_data['employees'].values())[0]
        assert emp_data['name'] == "Test Employee"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])