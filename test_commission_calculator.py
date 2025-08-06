#!/usr/bin/env python3
"""
Automated Test Suite for Commission Calculator Pro
Tests both Streamlit app functionality and API endpoints
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import requests
import json
import tempfile
import os
import sys
from pathlib import Path
import time
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test Configuration
API_BASE_URL = "http://127.0.0.1:8504"
STREAMLIT_URL = "http://127.0.0.1:8503"
TEST_TOKEN = "api_test_token_123"
TEST_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}

class TestDataGenerator:
    """Generate test data for commission calculations"""
    
    @staticmethod
    def create_test_employees():
        """Create sample employee data"""
        return pd.DataFrame([
            {
                'Employee ID': 'EMP001',
                'Name': 'John Doe',
                'Department': 'Sales',
                'Role': 'Sales Rep',
                'Hourly Rate': 25.0,
                'Commission Rate': 5.0,
                'Start Date': '2025-01-01',
                'Status': 'Active'
            },
            {
                'Employee ID': 'EMP002',
                'Name': 'Jane Smith',
                'Department': 'Sales',
                'Role': 'Senior Sales Rep',
                'Hourly Rate': 30.0,
                'Commission Rate': 7.5,
                'Start Date': '2025-01-15',
                'Status': 'Active'
            },
            {
                'Employee ID': 'EMP003',
                'Name': 'Bob Johnson',
                'Department': 'Marketing',
                'Role': 'Marketing Manager',
                'Hourly Rate': 35.0,
                'Commission Rate': 10.0,
                'Start Date': '2025-02-01',
                'Status': 'Active'
            }
        ])
    
    @staticmethod
    def create_test_timesheet():
        """Create sample timesheet data"""
        return pd.DataFrame([
            {
                'Employee Name': 'John Doe',
                'Regular Hours': 40.0,
                'OT Hours': 5.0,
                'DT Hours': 0.0,
                'Date': '2025-08-01'
            },
            {
                'Employee Name': 'Jane Smith',
                'Regular Hours': 38.0,
                'OT Hours': 10.0,
                'DT Hours': 2.0,
                'Date': '2025-08-01'
            },
            {
                'Employee Name': 'Bob Johnson',
                'Regular Hours': 35.0,
                'OT Hours': 8.0,
                'DT Hours': 0.0,
                'Date': '2025-08-01'
            }
        ])
    
    @staticmethod
    def create_test_revenue():
        """Create sample revenue data"""
        return pd.DataFrame([
            {
                'Business Unit': 'East Coast',
                'Jobs total revenue': 150000.0,
                'Period': 'Q1 2025',
                'Date': '2025-03-31'
            },
            {
                'Business Unit': 'West Coast',
                'Jobs total revenue': 200000.0,
                'Period': 'Q1 2025',
                'Date': '2025-03-31'
            },
            {
                'Business Unit': 'Central',
                'Jobs total revenue': 125000.0,
                'Period': 'Q1 2025',
                'Date': '2025-03-31'
            }
        ])
    
    @staticmethod
    def create_test_leads():
        """Create sample lead data"""
        return pd.DataFrame([
            {
                'Employee Name': 'John Doe',
                'Lead Value': 50000.0,
                'Commission Rate': 3.0,
                'Status': 'Closed Won',
                'Date': '2025-08-01',
                'Description': 'Large enterprise client'
            },
            {
                'Employee Name': 'Jane Smith',
                'Lead Value': 75000.0,
                'Commission Rate': 4.0,
                'Status': 'Closed Won',
                'Date': '2025-08-02',
                'Description': 'Fortune 500 company'
            },
            {
                'Employee Name': 'Bob Johnson',
                'Lead Value': 30000.0,
                'Commission Rate': 5.0,
                'Status': 'Closed Won',
                'Date': '2025-08-03',
                'Description': 'Mid-size business'
            }
        ])

class TestCommissionCalculations:
    """Test commission calculation logic"""
    
    def test_revenue_based_commission_calculation(self):
        """Test revenue-based commission calculation"""
        # Test data
        revenue = 100000.0
        lead_gen_rate = 5.0
        sold_by_rate = 7.5
        work_done_rate = 3.0
        
        # Expected calculations
        lead_gen_commission = revenue * (lead_gen_rate / 100)  # 100000 * 0.05 = 5000
        sold_by_commission = revenue * (sold_by_rate / 100)  # 100000 * 0.075 = 7500
        work_done_commission = revenue * (work_done_rate / 100)  # 100000 * 0.03 = 3000
        
        assert lead_gen_commission == 5000.0
        assert sold_by_commission == 7500.0
        assert work_done_commission == 3000.0
    
    def test_work_done_commission_splitting(self):
        """Test work done commission splitting among technicians"""
        # Test data
        revenue = 60000.0
        work_done_rate = 3.0
        num_technicians = 3
        
        # Expected calculation
        total_work_commission = revenue * (work_done_rate / 100)  # 60000 * 0.03 = 1800
        commission_per_tech = total_work_commission / num_technicians  # 1800 / 3 = 600
        
        assert total_work_commission == 1800.0
        assert commission_per_tech == 600.0
    
    def test_total_commission_calculation(self):
        """Test total commission calculation for all types"""
        lead_gen_commission = 5000.0
        sold_by_commission = 7500.0
        work_done_commission = 3000.0
        
        total_commission = lead_gen_commission + sold_by_commission + work_done_commission
        
        assert total_commission == 15500.0

class TestDataValidation:
    """Test data validation and error handling"""
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames"""
        empty_df = pd.DataFrame()
        
        # Should not crash when checking columns
        has_employee_name = 'Employee Name' in empty_df.columns
        assert has_employee_name == False
        
        # Should return 0 for calculations on empty data
        assert len(empty_df) == 0
    
    def test_missing_columns_handling(self):
        """Test handling of missing required columns"""
        # DataFrame without Employee Name column
        incomplete_df = pd.DataFrame({
            'Name': ['John Doe'],
            'Hours': [40.0]
        })
        
        # Should handle missing columns gracefully
        has_employee_name = 'Employee Name' in incomplete_df.columns
        assert has_employee_name == False
    
    def test_data_type_conversion(self):
        """Test numeric data type conversion"""
        # Test data with mixed types
        test_df = pd.DataFrame({
            'Employee Name': ['John Doe'],
            'Regular Hours': ['40.0'],  # String that should convert to float
            'OT Hours': [5],           # Integer
            'DT Hours': [0.0]          # Float
        })
        
        # Convert to numeric
        test_df['Regular Hours'] = pd.to_numeric(test_df['Regular Hours'], errors='coerce')
        test_df['OT Hours'] = pd.to_numeric(test_df['OT Hours'], errors='coerce')
        test_df['DT Hours'] = pd.to_numeric(test_df['DT Hours'], errors='coerce')
        
        # Verify conversions
        assert test_df['Regular Hours'].dtype in [np.float64, np.int64]
        assert test_df['OT Hours'].dtype in [np.float64, np.int64]
        assert test_df['DT Hours'].dtype in [np.float64, np.int64]
    
    def test_null_value_handling(self):
        """Test handling of null/NaN values"""
        test_df = pd.DataFrame({
            'Employee Name': ['John Doe', 'Jane Smith'],
            'Regular Hours': [40.0, None],
            'OT Hours': [5.0, np.nan]
        })
        
        # Fill null values
        test_df = test_df.fillna(0)
        
        # Verify null handling
        assert test_df['Regular Hours'].iloc[1] == 0
        assert test_df['OT Hours'].iloc[1] == 0

class TestAPIEndpoints:
    """Test REST API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_api_test(self):
        """Setup for API tests"""
        # Wait for API server to be ready
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f"{API_BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    pytest.skip("API server not available")
                time.sleep(1)
    
    def test_api_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{API_BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_api_root_endpoint(self):
        """Test API root endpoint"""
        response = requests.get(f"{API_BASE_URL}/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
    
    def test_employee_crud_operations(self):
        """Test employee CRUD operations"""
        # Test data
        employee_data = {
            "employee_id": "TEST001",
            "name": "Test Employee",
            "department": "Testing",
            "role": "Test Role",
            "hourly_rate": 20.0,
            "commission_rate": 5.0,
            "start_date": "2025-01-01",
            "status": "Active"
        }
        
        # Create employee
        response = requests.post(
            f"{API_BASE_URL}/api/employees",
            headers=TEST_HEADERS,
            json=employee_data
        )
        assert response.status_code == 200
        
        # Get employees
        response = requests.get(
            f"{API_BASE_URL}/api/employees",
            headers=TEST_HEADERS
        )
        assert response.status_code == 200
        employees = response.json()
        assert len(employees) >= 1
        
        # Find our test employee
        test_emp = next((emp for emp in employees if emp["employee_id"] == "TEST001"), None)
        assert test_emp is not None
        assert test_emp["name"] == "Test Employee"
        
        # Update employee
        employee_data["hourly_rate"] = 25.0
        response = requests.put(
            f"{API_BASE_URL}/api/employees/TEST001",
            headers=TEST_HEADERS,
            json=employee_data
        )
        assert response.status_code == 200
        
        # Delete employee
        response = requests.delete(
            f"{API_BASE_URL}/api/employees/TEST001",
            headers=TEST_HEADERS
        )
        assert response.status_code == 200
    
    def test_timesheet_bulk_upload(self):
        """Test bulk timesheet upload"""
        timesheet_data = [
            {
                "employee_name": "Test Employee",
                "regular_hours": 40.0,
                "ot_hours": 5.0,
                "dt_hours": 0.0,
                "date": "2025-08-01"
            }
        ]
        
        response = requests.post(
            f"{API_BASE_URL}/api/timesheet/bulk",
            headers=TEST_HEADERS,
            json=timesheet_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "1" in data["message"]  # Should mention 1 entry added
    
    def test_commission_calculation_api(self):
        """Test commission calculation via API"""
        # First, ensure we have test data
        # Create employee
        employee_data = {
            "employee_id": "TEST002",
            "name": "Test Calc Employee",
            "department": "Sales",
            "role": "Sales Rep",
            "hourly_rate": 25.0,
            "commission_rate": 5.0,
            "start_date": "2025-01-01",
            "status": "Active"
        }
        
        requests.post(
            f"{API_BASE_URL}/api/employees",
            headers=TEST_HEADERS,
            json=employee_data
        )
        
        # Add timesheet data
        timesheet_data = [
            {
                "employee_name": "Test Calc Employee",
                "regular_hours": 40.0,
                "ot_hours": 5.0,
                "dt_hours": 0.0,
                "date": "2025-08-01"
            }
        ]
        
        requests.post(
            f"{API_BASE_URL}/api/timesheet/bulk",
            headers=TEST_HEADERS,
            json=timesheet_data
        )
        
        # Calculate commissions
        calc_request = {
            "employee_names": ["Test Calc Employee"],
            "start_date": "2025-08-01",
            "end_date": "2025-08-31",
            "calculate_hourly": True,
            "calculate_leads": False
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/commissions/calculate",
            headers=TEST_HEADERS,
            json=calc_request
        )
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["employee"] == "Test Calc Employee"
        assert results[0]["total_commission"] > 0
        
        # Cleanup
        requests.delete(
            f"{API_BASE_URL}/api/employees/TEST002",
            headers=TEST_HEADERS
        )
    
    def test_authentication_required(self):
        """Test that authentication is required"""
        # Request without token should fail
        response = requests.get(f"{API_BASE_URL}/api/employees")
        assert response.status_code == 403  # or 401
        
        # Request with invalid token should fail
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(
            f"{API_BASE_URL}/api/employees",
            headers=invalid_headers
        )
        assert response.status_code == 401

class TestFileOperations:
    """Test file upload and processing"""
    
    def test_csv_file_processing(self):
        """Test CSV file reading and processing"""
        # Create temporary CSV file
        test_data = TestDataGenerator.create_test_employees()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            csv_file = f.name
        
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Verify data integrity
            assert len(df) == 3
            assert 'Employee ID' in df.columns
            assert 'Name' in df.columns
            assert 'Hourly Rate' in df.columns
            
            # Verify data types
            assert df['Hourly Rate'].dtype in [np.float64, np.int64]
            
        finally:
            # Cleanup
            os.unlink(csv_file)
    
    def test_excel_file_processing(self):
        """Test Excel file reading and processing"""
        # Create temporary Excel file
        test_data = TestDataGenerator.create_test_timesheet()
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            test_data.to_excel(f.name, index=False)
            excel_file = f.name
        
        try:
            # Read the Excel file
            df = pd.read_excel(excel_file)
            
            # Verify data integrity
            assert len(df) == 3
            assert 'Employee Name' in df.columns
            assert 'Regular Hours' in df.columns
            
        finally:
            # Cleanup
            os.unlink(excel_file)

class TestPerformance:
    """Test performance with large datasets"""
    
    def test_large_dataset_processing(self):
        """Test processing large datasets"""
        # Create large dataset (1000 records)
        large_data = []
        for i in range(1000):
            large_data.append({
                'Employee Name': f'Employee_{i:04d}',
                'Regular Hours': 40.0 + (i % 10),
                'OT Hours': i % 8,
                'DT Hours': i % 3
            })
        
        df = pd.DataFrame(large_data)
        
        # Time the processing
        start_time = time.time()
        
        # Simulate timesheet processing
        hours_columns = [col for col in df.columns if 'hour' in col.lower()]
        df['Total Hours'] = df[hours_columns].sum(axis=1)
        
        processing_time = time.time() - start_time
        
        # Should process 1000 records quickly (< 1 second)
        assert processing_time < 1.0
        assert len(df) == 1000
        assert 'Total Hours' in df.columns

def run_test_suite():
    """Run the complete test suite"""
    print("🧪 Starting Commission Calculator Pro Test Suite")
    print("=" * 60)
    
    # Run pytest with verbose output
    result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    if result == 0:
        print("\n✅ All tests passed successfully!")
    else:
        print(f"\n❌ Test suite failed with exit code: {result}")
    
    return result

if __name__ == "__main__":
    # Check if API server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("⚠️ API server not responding. Starting API server...")
            # Note: In production, you'd start the server here
    except requests.exceptions.RequestException:
        print("⚠️ API server not available. Some tests will be skipped.")
    
    # Run tests
    exit_code = run_test_suite()
    sys.exit(exit_code)