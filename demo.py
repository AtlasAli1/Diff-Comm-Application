#!/usr/bin/env python3
"""
Commission Calculator Pro - Demo Data Setup
Run this script to populate the system with sample data for testing
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models import Employee, BusinessUnit, CommissionCalculator
from utils import DatabaseManager

def create_demo_data():
    """Create comprehensive demo data for testing the application"""
    
    print("🚀 Setting up Commission Calculator Pro with demo data...")
    
    # Initialize system components
    db_manager = DatabaseManager()
    calc = CommissionCalculator()
    
    print("📊 Creating sample employees...")
    
    # Create sample employees
    employees_data = [
        {"name": "John Smith", "dept": "Sales", "rate": 28.50, "reg": 40, "ot": 6, "dt": 0},
        {"name": "Sarah Johnson", "dept": "Engineering", "rate": 35.00, "reg": 40, "ot": 4, "dt": 2},
        {"name": "Mike Davis", "dept": "Marketing", "rate": 25.00, "reg": 38, "ot": 0, "dt": 0},
        {"name": "Lisa Chen", "dept": "Sales", "rate": 30.00, "reg": 40, "ot": 8, "dt": 0},
        {"name": "Robert Wilson", "dept": "Engineering", "rate": 32.00, "reg": 40, "ot": 2, "dt": 4},
        {"name": "Jennifer Martinez", "dept": "Support", "rate": 22.50, "reg": 40, "ot": 5, "dt": 0},
        {"name": "David Thompson", "dept": "Sales", "rate": 26.75, "reg": 38, "ot": 7, "dt": 1},
        {"name": "Emily Rodriguez", "dept": "Marketing", "rate": 27.25, "reg": 40, "ot": 3, "dt": 0}
    ]
    
    for i, emp_data in enumerate(employees_data, 1):
        employee = Employee(
            name=emp_data["name"],
            hourly_rate=Decimal(str(emp_data["rate"])),
            regular_hours=Decimal(str(emp_data["reg"])),
            ot_hours=Decimal(str(emp_data["ot"])),
            dt_hours=Decimal(str(emp_data["dt"])),
            department=emp_data["dept"],
            employee_id=f"EMP{i:03d}"
        )
        
        calc.add_employee(employee)
        db_manager.save_employee(employee.to_dict())
    
    print("🏢 Creating sample business units...")
    
    # Create sample business units
    business_units_data = [
        {"name": "Project Alpha - Software Development", "category": "Software", "revenue": 85000, "rate": 12.0},
        {"name": "Project Beta - Consulting Services", "category": "Consulting", "revenue": 65000, "rate": 15.0},
        {"name": "Project Gamma - Support Services", "category": "Support", "revenue": 35000, "rate": 8.0},
        {"name": "Project Delta - Marketing Campaign", "category": "Marketing", "revenue": 45000, "rate": 10.0},
        {"name": "Project Epsilon - Infrastructure", "category": "Infrastructure", "revenue": 95000, "rate": 9.0},
        {"name": "Project Zeta - Training Program", "category": "Training", "revenue": 25000, "rate": 14.0}
    ]
    
    for unit_data in business_units_data:
        business_unit = BusinessUnit(
            name=unit_data["name"],
            revenue=Decimal(str(unit_data["revenue"])),
            commission_rate=Decimal(str(unit_data["rate"])),
            category=unit_data["category"],
            description=f"Sample business unit for {unit_data['category']} operations"
        )
        
        calc.add_business_unit(business_unit)
        db_manager.save_business_unit(business_unit.to_dict())
    
    print("💰 Calculating commissions...")
    
    # Calculate commissions for the current period
    period_start = datetime.now().replace(day=1)  # First of current month
    period_end = datetime.now()
    
    commissions = calc.calculate_commissions(period_start, period_end)
    
    # Save commissions to database
    for commission in commissions:
        db_manager.save_commission(commission.to_dict())
    
    # Log demo data creation
    db_manager.log_action('demo_data_created', {
        'employees': len(calc.employees),
        'business_units': len(calc.business_units),
        'commissions': len(commissions),
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat()
    }, 'demo_script')
    
    # Generate summary
    analytics = calc.get_analytics_data()
    
    print("\n✅ Demo data setup complete!")
    print("\n📊 Summary:")
    print(f"   • Employees: {len(calc.employees)}")
    print(f"   • Business Units: {len(calc.business_units)}")
    print(f"   • Total Revenue: ${analytics['kpis']['total_revenue']:,.2f}")
    print(f"   • Total Labor Cost: ${analytics['kpis']['total_labor_cost']:,.2f}")
    print(f"   • Total Commissions: ${analytics['kpis']['total_commissions']:,.2f}")
    print(f"   • Gross Profit: ${analytics['kpis']['gross_profit']:,.2f}")
    print(f"   • Profit Margin: {analytics['kpis']['profit_margin']:.1f}%")
    
    print("\n🔐 Login Credentials:")
    print("   • Username: admin")
    print("   • Password: admin123")
    print("   • ⚠️  Please change the default password after first login!")
    
    print("\n🚀 Ready to start! Run: python run.py")
    
    return calc, db_manager

def create_sample_excel_files():
    """Create sample Excel files for import testing"""
    
    print("\n📁 Creating sample Excel files...")
    
    import pandas as pd
    
    # Sample timesheet data
    timesheet_data = {
        'Employee Name': ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Chen'],
        'Employee ID': ['EMP001', 'EMP002', 'EMP003', 'EMP004'],
        'Department': ['Sales', 'Engineering', 'Marketing', 'Sales'],
        'Regular Hours': [40, 40, 38, 40],
        'OT Hours': [6, 4, 0, 8],
        'DT Hours': [0, 2, 0, 0],
        'Pay Period': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01']
    }
    
    # Sample revenue data
    revenue_data = {
        'Business Unit': [
            'Project Alpha - Software Development',
            'Project Beta - Consulting Services', 
            'Project Gamma - Support Services',
            'Project Delta - Marketing Campaign'
        ],
        'Revenue': [85000, 65000, 35000, 45000],
        'Category': ['Software', 'Consulting', 'Support', 'Marketing'],
        'Period': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01']
    }
    
    # Create Excel files
    with pd.ExcelWriter('sample_timesheet.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(timesheet_data).to_excel(writer, sheet_name='Timesheet', index=False)
    
    with pd.ExcelWriter('sample_revenue.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(revenue_data).to_excel(writer, sheet_name='Revenue', index=False)
    
    # Create combined template
    with pd.ExcelWriter('commission_template.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(timesheet_data).to_excel(writer, sheet_name='Timesheet', index=False)
        pd.DataFrame(revenue_data).to_excel(writer, sheet_name='Revenue', index=False)
        
        # Add configuration sheet
        config_data = {
            'Setting': ['Default Commission Rate', 'Default Hourly Rate', 'OT Multiplier', 'DT Multiplier'],
            'Value': [10.0, 25.0, 1.5, 2.0],
            'Description': [
                'Default commission percentage for new business units',
                'Default hourly rate for new employees',
                'Overtime multiplier (1.5x regular rate)',
                'Double time multiplier (2.0x regular rate)'
            ]
        }
        pd.DataFrame(config_data).to_excel(writer, sheet_name='Configuration', index=False)
    
    print("   ✅ Created sample_timesheet.xlsx")
    print("   ✅ Created sample_revenue.xlsx")
    print("   ✅ Created commission_template.xlsx")

def main():
    """Main demo setup function"""
    
    print("=" * 60)
    print("   🎯 Commission Calculator Pro - Demo Setup")
    print("=" * 60)
    
    try:
        # Create demo data
        calc, db_manager = create_demo_data()
        
        # Create sample files
        create_sample_excel_files()
        
        print("\n" + "=" * 60)
        print("   🎉 Demo setup completed successfully!")
        print("=" * 60)
        
        print("\n📋 Next Steps:")
        print("   1. Run: python run.py")
        print("   2. Open browser to: http://localhost:8501")
        print("   3. Login with admin/admin123")
        print("   4. Explore the different pages and features")
        print("   5. Try importing the sample Excel files")
        
        print("\n🔍 Features to Explore:")
        print("   • Data Management: Upload and edit data")
        print("   • System Configuration: Set rates and periods")
        print("   • Analytics Dashboard: View performance metrics")
        print("   • Commission Reports: Generate various reports")
        print("   • Advanced Settings: User management and audit trails")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during demo setup: {str(e)}")
        print("\nPlease check that all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)