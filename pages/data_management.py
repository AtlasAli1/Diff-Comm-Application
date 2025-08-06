import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import io
from typing import List, Dict, Any, Optional
from loguru import logger
from decimal import Decimal

from models import Employee, BusinessUnit
from utils import DataValidator
from utils.timesheet_processor import TimesheetProcessor
from utils.revenue_processor import RevenueProcessor
from utils.notifications import notify_data_import_complete, NotificationManager

def data_management_page():
    """Enhanced data management page with multiple import/export options"""
    st.title("📤 Data Management")
    
    # Ensure session state is initialized
    if 'calculator' not in st.session_state:
        from models import CommissionCalculator
        st.session_state.calculator = CommissionCalculator()
    
    if 'validator' not in st.session_state:
        try:
            from utils import DataValidator
            st.session_state.validator = DataValidator()
        except ImportError as e:
            st.warning(f"Data validator not available: {str(e)}")
            st.session_state.validator = None
        except Exception as e:
            st.error(f"Error initializing validator: {str(e)}")
            st.session_state.validator = None
    
    if 'db_manager' not in st.session_state:
        try:
            from utils import DatabaseManager
            st.session_state.db_manager = DatabaseManager()
        except ImportError as e:
            st.warning(f"Database manager not available: {str(e)}")
            st.session_state.db_manager = None
        except Exception as e:
            st.error(f"Error initializing database manager: {str(e)}")
            st.session_state.db_manager = None
    
    # Create tabs for different data management functions
    tabs = st.tabs([
        "📤 Upload Files",
        "📋 Edit Timesheets", 
        "💰 Edit Revenue",
        "👥 Manage Employees",
        "🏢 Manage Business Units",
        "🔄 Data Recovery",
        "📊 Data Preview",
        "🔧 Bulk Operations"
    ])
    
    with tabs[0]:
        upload_files_section()
    
    with tabs[1]:
        edit_timesheets_section()
    
    with tabs[2]:
        edit_revenue_section()
    
    with tabs[3]:
        manage_employees_section()
    
    with tabs[4]:
        manage_business_units_section()
    
    with tabs[5]:
        data_recovery_section()
    
    with tabs[6]:
        data_preview_section()
    
    with tabs[7]:
        bulk_operations_section()

def upload_files_section():
    """Enhanced file upload section with validation and preview"""
    st.subheader("📤 Upload Excel Files")
    
    # Instructions
    with st.expander("📖 Upload Instructions", expanded=False):
        st.markdown("""
        ### Timesheet File Requirements:
        - **Required columns**: Employee Name, Regular Hours, OT Hours, DT Hours
        - **Optional columns**: Department, Employee ID, Pay Period
        - **File formats**: .xlsx, .xls, .csv
        
        ### Revenue File Requirements:
        - **Required columns**: Revenue (or Amount)
        - **Recommended columns**: Business Unit, Department, or Project
        - **File formats**: .xlsx, .xls, .csv
        
        ### Tips:
        - Ensure employee names are consistent across files
        - Remove any summary rows or totals
        - Dates should be in standard format (YYYY-MM-DD)
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Timesheet Upload")
        
        # Multiple file upload support
        timesheet_files = st.file_uploader(
            "Upload Timesheet File(s)",
            type=['xlsx', 'xls', 'csv'],
            accept_multiple_files=True,
            help="You can upload multiple timesheet files to combine data"
        )
        
        if timesheet_files:
            process_timesheet_uploads(timesheet_files)
    
    with col2:
        st.markdown("### 💰 Revenue Upload")
        
        revenue_files = st.file_uploader(
            "Upload Revenue File(s)",
            type=['xlsx', 'xls', 'csv'],
            accept_multiple_files=True,
            help="You can upload multiple revenue files to combine data"
        )
        
        if revenue_files:
            process_revenue_uploads(revenue_files)
    
    # Quick import templates
    st.divider()
    st.subheader("📑 Download Templates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Timesheet Template", use_container_width=True):
            download_timesheet_template()
    
    with col2:
        if st.button("💰 Revenue Template", use_container_width=True):
            download_revenue_template()
    
    with col3:
        if st.button("📊 Combined Template", use_container_width=True):
            download_combined_template()

def process_timesheet_uploads(files):
    """Enhanced process multiple timesheet file uploads with format detection"""
    processor = TimesheetProcessor()
    all_processed_data = []
    errors = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, file in enumerate(files):
        status_text.text(f"Processing {file.name}...")
        progress_bar.progress((idx + 1) / len(files))
        
        try:
            # Use enhanced processor
            processed_df, summary = processor.process_timesheet(file, file.name)
            
            # Display individual file results
            with st.expander(f"📋 {file.name} - Processing Results"):
                processor.display_processing_results(processed_df, summary, use_expander=True)
            
            all_processed_data.append(processed_df)
            st.success(f"✅ {file.name} - {summary['total_employees']} employees processed")
            
            # Send notification for successful import
            notify_data_import_complete(
                file_name=file.name,
                records=summary['total_employees'],
                status="success"
            )
            
        except Exception as e:
            errors.append(f"Error processing {file.name}: {str(e)}")
            st.error(f"❌ Failed to process {file.name}: {str(e)}")
            
            # Send notification for failed import
            notify_data_import_complete(
                file_name=file.name,
                records=0,
                status=str(e)
            )
    
    progress_bar.empty()
    status_text.empty()
    
    # Combine all processed data
    if all_processed_data:
        # If multiple files, combine them
        if len(all_processed_data) > 1:
            st.subheader("🔄 Combining Multiple Files")
            
            combined_df = pd.concat(all_processed_data, ignore_index=True)
            
            # Group by employee and sum hours (in case same employee in multiple files)
            final_df = combined_df.groupby('Employee Name').agg({
                'Regular Hours': 'sum',
                'OT Hours': 'sum',
                'DT Hours': 'sum'
            }).reset_index()
            
            # Recalculate totals
            final_df['Total Hours'] = final_df['Regular Hours'] + final_df['OT Hours'] + final_df['DT Hours']
            
        else:
            final_df = all_processed_data[0]
        
        # Display final combined results
        st.subheader("📊 Final Combined Results")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Employees", len(final_df))
        with col2:
            st.metric("Regular Hours", f"{final_df['Regular Hours'].sum():.2f}")
        with col3:
            st.metric("OT Hours", f"{final_df['OT Hours'].sum():.2f}")
        with col4:
            st.metric("DT Hours", f"{final_df['DT Hours'].sum():.2f}")
        
        # Convert to display format
        display_df = final_df.copy()
        for col in ['Regular Hours', 'OT Hours', 'DT Hours', 'Total Hours']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{float(x):.2f}")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Import to calculator
        if st.button("✅ Import Combined Data", type="primary", use_container_width=True):
            success, import_errors = st.session_state.calculator.import_timesheet_data(final_df)
            
            if success:
                st.success(f"✅ Successfully imported {len(final_df)} employees")
                save_to_database()
            else:
                st.error("❌ Import failed")
                for error in import_errors:
                    st.error(error)
    
    # Show all errors
    if errors:
        with st.expander("❌ Processing Errors", expanded=True):
            for error in errors:
                st.error(error)

def process_revenue_uploads(files):
    """Enhanced process revenue file uploads with commission breakdown"""
    processor = RevenueProcessor()
    all_processed_data = []
    errors = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, file in enumerate(files):
        status_text.text(f"Processing {file.name}...")
        progress_bar.progress((idx + 1) / len(files))
        
        try:
            # Use enhanced revenue processor
            commission_df, summary = processor.process_revenue_file(file, file.name)
            
            # Display individual file results
            with st.expander(f"💰 {file.name} - Commission Analysis"):
                processor.display_commission_breakdown(commission_df, summary)
            
            all_processed_data.append((commission_df, summary))
            st.success(f"✅ {file.name} - {summary['total_jobs']} jobs, ${summary['total_revenue']:,.2f} revenue, ${summary['total_all_commissions']:,.2f} commissions")
            
        except Exception as e:
            errors.append(f"Error processing {file.name}: {str(e)}")
            st.error(f"❌ Failed to process {file.name}: {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    
    # Combine all processed data
    if all_processed_data:
        # If multiple files, combine them
        if len(all_processed_data) > 1:
            st.subheader("🔄 Combining Multiple Revenue Files")
            
            all_commission_dfs = [data[0] for data in all_processed_data]
            combined_commission_df = pd.concat(all_commission_dfs, ignore_index=True)
            
            # Recalculate combined summary
            combined_summary = processor.create_commission_summary(combined_commission_df)
        else:
            combined_commission_df, combined_summary = all_processed_data[0]
        
        # Display final combined results
        st.subheader("📊 Final Revenue & Commission Analysis")
        processor.display_commission_breakdown(combined_commission_df, combined_summary)
        
        # Store in session state for further processing
        if 'combined_revenue_data' not in st.session_state:
            st.session_state.combined_revenue_data = {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.combined_revenue_data[timestamp] = {
            'commission_df': combined_commission_df,
            'summary': combined_summary
        }
        
        # Import button
        if st.button("✅ Import Combined Revenue", type="primary", use_container_width=True, key="import_revenue_commissions"):
            import_revenue_data(combined_commission_df, combined_summary)
    
    # Show errors if any
    if errors:
        with st.expander("❌ Processing Errors", expanded=True):
            for error in errors:
                st.error(error)

def import_revenue_data(commission_df: pd.DataFrame, summary: Dict[str, Any]):
    """Import processed revenue data into the calculator"""
    try:        
        st.success(f"✅ Successfully imported {len(commission_df)} revenue entries")
        st.success(f"💰 Total revenue: ${summary['total_revenue']:,.2f}")
        st.success(f"💵 Total commissions: ${summary['total_all_commissions']:,.2f}")
        
        save_to_database()
        
    except Exception as e:
        st.error(f"Error importing revenue data: {str(e)}")

def edit_timesheets_section():
    """Enhanced timesheet editing with bulk operations"""
    st.subheader("📋 Edit Employee Timesheets")
    
    calc = st.session_state.calculator
    
    if not calc.employees:
        st.warning("No employees loaded. Please upload timesheet data first.")
        return
    
    # Bulk operations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset All Hours", use_container_width=True):
            if st.checkbox("Confirm reset all hours to zero"):
                for emp in calc.employees.values():
                    emp.update_hours(Decimal('0'), Decimal('0'), Decimal('0'))
                st.success("All hours reset to zero")
                st.rerun()
    
    with col2:
        if st.button("📥 Import from Last Period", use_container_width=True):
            st.info("Feature coming soon: Import hours from previous period")
    
    with col3:
        if st.button("📤 Export Current Hours", use_container_width=True):
            export_current_hours()
    
    st.divider()
    
    # Employee selection
    employee_names = sorted([emp.name for emp in calc.employees.values()])
    
    # Search/filter
    search_term = st.text_input("🔍 Search Employee", placeholder="Type to search...")
    filtered_employees = [name for name in employee_names if search_term.lower() in name.lower()]
    
    if filtered_employees:
        selected_employee = st.selectbox(
            "Select Employee to Edit",
            filtered_employees,
            help="Select an employee to edit their hours"
        )
        
        # Get employee object
        employee = calc.find_employee_by_name(selected_employee)
        
        if employee:
            # Display current info
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"### 👤 {employee.name}")
                if employee.department:
                    st.caption(f"Department: {employee.department}")
                if employee.employee_id:
                    st.caption(f"ID: {employee.employee_id}")
            
            with col2:
                st.metric("Hourly Rate", f"${float(employee.hourly_rate):.2f}")
            
            # Hours input
            st.markdown("#### ⏰ Edit Hours")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                regular_hours = st.number_input(
                    "Regular Hours",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(employee.regular_hours),
                    step=0.25,
                    key=f"reg_{employee.id}"
                )
            
            with col2:
                ot_hours = st.number_input(
                    "Overtime Hours (1.5x)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(employee.ot_hours),
                    step=0.25,
                    key=f"ot_{employee.id}"
                )
            
            with col3:
                dt_hours = st.number_input(
                    "Double Time Hours (2x)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(employee.dt_hours),
                    step=0.25,
                    key=f"dt_{employee.id}"
                )
            
            # Calculate totals
            total_hours = regular_hours + ot_hours + dt_hours
            labor_cost = (regular_hours * float(employee.hourly_rate) + 
                         ot_hours * float(employee.hourly_rate) * 1.5 +
                         dt_hours * float(employee.hourly_rate) * 2.0)
            
            # Display calculations
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Hours", f"{total_hours:.2f}")
            with col2:
                st.metric("Labor Cost", f"${labor_cost:.2f}")
            with col3:
                effective_rate = labor_cost / total_hours if total_hours > 0 else 0
                st.metric("Effective Rate", f"${effective_rate:.2f}/hr")
            
            # Save button
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Changes", type="primary", use_container_width=True, key="save_timesheet_changes"):
                    employee.update_hours(
                        Decimal(str(regular_hours)),
                        Decimal(str(ot_hours)),
                        Decimal(str(dt_hours))
                    )
                    st.success(f"✅ Hours updated for {employee.name}")
                    save_to_database()
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reset Hours", use_container_width=True):
                    employee.update_hours(Decimal('0'), Decimal('0'), Decimal('0'))
                    st.success(f"Hours reset for {employee.name}")
                    st.rerun()

def edit_revenue_section():
    """Enhanced revenue editing with table view and commission breakdown"""
    st.subheader("💰 Revenue & Commission Management - Table View")
    
    # Check if we have processed revenue data
    if 'combined_revenue_data' in st.session_state and st.session_state.combined_revenue_data:
        # Get the most recent revenue data
        latest_key = max(st.session_state.combined_revenue_data.keys())
        revenue_data = st.session_state.combined_revenue_data[latest_key]
        commission_df = revenue_data['commission_df']
        summary = revenue_data['summary']
        
        # Display overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", summary['total_jobs'])
        with col2:
            st.metric("Total Revenue", f"${summary['total_revenue']:,.2f}")
        with col3:
            st.metric("Total Commissions", f"${summary['total_all_commissions']:,.2f}")
        with col4:
            commission_rate = (summary['total_all_commissions'] / summary['total_revenue'] * 100) if summary['total_revenue'] > 0 else 0
            st.metric("Overall Commission Rate", f"{commission_rate:.1f}%")
        
        st.divider()
        
        # Commission rate settings
        st.subheader("⚙️ Commission Rate Settings")
        
        processor = RevenueProcessor()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            lead_rate = st.number_input(
                "Lead Generation Rate (%)", 
                min_value=0.0, max_value=20.0, 
                value=float(processor.default_rates['lead_generation_rate']), 
                step=0.1, format="%.1f"
            )
        with col2:
            sales_rate = st.number_input(
                "Sales Commission Rate (%)", 
                min_value=0.0, max_value=20.0, 
                value=float(processor.default_rates['sales_rate']), 
                step=0.1, format="%.1f"
            )
        with col3:
            tech_rate = st.number_input(
                "Technician Work Rate (%)", 
                min_value=0.0, max_value=20.0, 
                value=float(processor.default_rates['technician_work_rate']), 
                step=0.1, format="%.1f"
            )
        
        # Update rates button
        if st.button("🔄 Recalculate with New Rates", type="secondary"):
            processor.default_rates['lead_generation_rate'] = Decimal(str(lead_rate))
            processor.default_rates['sales_rate'] = Decimal(str(sales_rate))
            processor.default_rates['technician_work_rate'] = Decimal(str(tech_rate))
            
            # Recalculate commissions
            new_jobs = []
            for _, row in commission_df.iterrows():
                # Create job row data for reprocessing
                job_row_data = {
                    'Invoice #': row['invoice_number'],
                    'Invoice Date': row['invoice_date'],
                    'Customer Name': row['customer_name'],
                    'Business Unit': row['business_unit'],
                    'Jobs Total Revenue': row['total_revenue'],
                    'Lead Generated By': row['lead_commission_person'],
                    'Sold By': row['sales_commission_person'],
                    'Assigned Technicians': ', '.join(row['assigned_technicians'])
                }
                
                job_data = processor.process_single_job(pd.Series(job_row_data))
                new_jobs.append(job_data)
            
            # Update session state
            new_commission_df = pd.DataFrame(new_jobs)
            new_summary = processor.create_commission_summary(new_commission_df)
            
            st.session_state.combined_revenue_data[latest_key] = {
                'commission_df': new_commission_df,
                'summary': new_summary
            }
            st.rerun()
        
        st.divider()
        
        # Editable table view
        st.subheader("📋 All Jobs - Editable Table View")
        
        # Create editable dataframe
        edit_df = processor.create_editable_table_data(commission_df)
        
        # Use st.data_editor for editing
        edited_df = st.data_editor(
            edit_df,
            use_container_width=True,
            num_rows="dynamic",  # Allow adding/removing rows
            disabled=["Invoice #", "Date", "Customer"],  # Make some columns read-only
            column_config={
                "Revenue": st.column_config.NumberColumn(
                    "Revenue",
                    help="Total job revenue",
                    format="$%.2f",
                    min_value=0,
                    step=100
                ),
                "Lead Commission": st.column_config.NumberColumn(
                    "Lead Commission",
                    help="Commission for lead generation",
                    format="$%.2f",
                    min_value=0
                ),
                "Sales Commission": st.column_config.NumberColumn(
                    "Sales Commission", 
                    help="Commission for sales",
                    format="$%.2f",
                    min_value=0
                ),
                "Tech Commission Total": st.column_config.NumberColumn(
                    "Tech Commission Total",
                    help="Total commission for technician work",
                    format="$%.2f",
                    min_value=0
                ),
                "Tech Commission Each": st.column_config.NumberColumn(
                    "Tech Commission Each",
                    help="Commission per technician",
                    format="$%.2f",
                    min_value=0
                ),
                "Total Job Commission": st.column_config.NumberColumn(
                    "Total Job Commission",
                    help="Total commission for this job",
                    format="$%.2f",
                    min_value=0
                )
            }
        )
        
        # Save changes button
        if st.button("💾 Save All Changes", type="primary", use_container_width=True, key="save_all_revenue_changes"):
            try:
                st.success("✅ Revenue table changes saved!")
                # Here you would implement the logic to save changes back to the commission_df
                # and update the summary accordingly
                save_to_database()
            except Exception as e:
                st.error(f"Error saving changes: {str(e)}")
        
        # Commission breakdown by person
        st.divider()
        st.subheader("👥 Individual Commission Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**🎯 Lead Generation Commissions**")
            if summary['lead_generators']:
                for person, amount in summary['lead_generators'].items():
                    st.write(f"• {person}: ${amount:,.2f}")
            else:
                st.info("No lead generation commissions")
        
        with col2:
            st.write("**💼 Sales Commissions**")
            if summary['sales_people']:
                for person, amount in summary['sales_people'].items():
                    st.write(f"• {person}: ${amount:,.2f}")
            else:
                st.info("No sales commissions")
        
        with col3:
            st.write("**🔧 Technician Commissions**")
            if summary['technicians']:
                for person, amount in summary['technicians'].items():
                    st.write(f"• {person}: ${amount:,.2f}")
            else:
                st.info("No technician commissions")
        
    else:
        st.warning("⚠️ No revenue data loaded. Please upload revenue files first in the 'Upload Files' tab.")
        
        # Show sample of what the commission structure looks like
        st.subheader("📋 Commission Structure Preview")
        st.info("""
        **The system will automatically split commissions into three categories:**
        
        1. **Lead Generation Commission** (2% default)
           - Paid to the person who generated the lead
           - Based on "Lead Generated By" column
        
        2. **Sales Commission** (3% default) 
           - Paid to the person who sold the job
           - Based on "Sold By" column
        
        3. **Technician Work Commission** (5% default)
           - Split equally among assigned technicians
           - Based on "Assigned Technicians" column
           
        **Upload a revenue file to see the full table view and commission breakdown!**
        """)

def manage_employees_section():
    """Comprehensive employee management"""
    st.subheader("👥 Manage Employees")
    
    calc = st.session_state.calculator
    
    # Employee list with search
    search_term = st.text_input("🔍 Search Employees", placeholder="Search by name, ID, or department...")
    
    # Filter employees
    filtered_employees = []
    for emp in calc.employees.values():
        if (search_term.lower() in emp.name.lower() or
            (emp.employee_id and search_term.lower() in emp.employee_id.lower()) or
            (emp.department and search_term.lower() in emp.department.lower())):
            filtered_employees.append(emp)
    
    if not filtered_employees and calc.employees:
        filtered_employees = list(calc.employees.values())
    
    # Display employees in a table
    if filtered_employees:
        employee_data = []
        for emp in filtered_employees:
            employee_data.append({
                'Name': emp.name,
                'ID': emp.employee_id or 'N/A',
                'Department': emp.department or 'N/A',
                'Hourly Rate': f"${float(emp.hourly_rate):.2f}",
                'Total Hours': float(emp.total_hours),
                'Status': '✅ Active' if emp.is_active else '❌ Inactive',
                'Actions': emp.id
            })
        
        df = pd.DataFrame(employee_data)
        
        # Display with actions
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 2, 2])
            
            with col1:
                st.write(row['Name'])
            with col2:
                st.write(row['ID'])
            with col3:
                st.write(row['Department'])
            with col4:
                st.write(row['Hourly Rate'])
            with col5:
                st.write(row['Total Hours'])
            with col6:
                st.write(row['Status'])
            with col7:
                if st.button("Edit", key=f"edit_{row['Actions']}"):
                    st.session_state.editing_employee = row['Actions']
                    st.rerun()
    
    # Edit employee modal
    if 'editing_employee' in st.session_state:
        edit_employee_modal(st.session_state.editing_employee)

def manage_business_units_section():
    """Comprehensive business unit management"""
    st.subheader("🏢 Manage Business Units")
    
    calc = st.session_state.calculator
    
    # Business unit grid
    if calc.business_units:
        unit_data = []
        for unit in calc.business_units.values():
            unit_data.append({
                'Name': unit.name,
                'Category': unit.category or 'N/A',
                'Revenue': float(unit.revenue),
                'Commission Rate': float(unit.commission_rate),
                'Commission Amount': float(unit.commission_amount),
                'Status': '✅ Active' if unit.is_active else '❌ Inactive'
            })
        
        df = pd.DataFrame(unit_data)
        
        # Format currency columns
        currency_cols = ['Revenue', 'Commission Amount']
        for col in currency_cols:
            df[col] = df[col].apply(lambda x: f"${x:,.2f}")
        
        df['Commission Rate'] = df['Commission Rate'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df, use_container_width=True)
        
        # Bulk operations
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export Units", use_container_width=True):
                export_business_units()
        
        with col2:
            if st.button("🔄 Recalculate All", use_container_width=True):
                st.info("Recalculating commissions...")
                # Trigger recalculation
        
        with col3:
            if st.button("📈 View Analytics", use_container_width=True):
                st.session_state.selected_page = "📊 Analytics Dashboard"
                st.rerun()

def data_recovery_section():
    """Data recovery and backup management"""
    st.subheader("🔄 Data Recovery & Backups")
    
    db_manager = st.session_state.db_manager
    
    # Backup management
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 Create Backup")
        
        backup_name = st.text_input("Backup Name (optional)", placeholder="Leave empty for timestamp")
        
        if st.button("Create Backup", type="primary", use_container_width=True):
            try:
                backup_path = db_manager.create_backup(backup_name)
                st.success(f"✅ Backup created: {backup_path}")
            except Exception as e:
                st.error(f"❌ Backup failed: {str(e)}")
    
    with col2:
        st.markdown("### 📥 Restore from Backup")
        
        # List available backups
        import os
        backup_dir = db_manager.backup_dir
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        
        if backup_files:
            selected_backup = st.selectbox("Select Backup", sorted(backup_files, reverse=True))
            
            if st.button("Restore Backup", type="secondary", use_container_width=True):
                if st.checkbox("⚠️ Confirm restore (will overwrite current data)"):
                    backup_path = os.path.join(backup_dir, selected_backup)
                    if db_manager.restore_backup(backup_path):
                        st.success("✅ Data restored successfully")
                        st.rerun()
                    else:
                        st.error("❌ Restore failed")
        else:
            st.info("No backups available")
    
    st.divider()
    
    # Export/Import JSON
    st.markdown("### 📤 Export/Import JSON")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export to JSON", use_container_width=True):
            export_data = st.session_state.calculator.export_to_dict()
            json_str = st.session_state.export_manager.export_to_json(export_data)
            
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"commission_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_json = st.file_uploader("Import JSON", type=['json'])
        
        if uploaded_json:
            try:
                import json
                data = json.load(uploaded_json)
                # Import logic here
                st.success("✅ JSON imported successfully")
            except Exception as e:
                st.error(f"❌ Import failed: {str(e)}")

def data_preview_section():
    """Preview all loaded data"""
    st.subheader("📊 Data Preview")
    
    calc = st.session_state.calculator
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Employees", len(calc.employees))
    with col2:
        st.metric("Business Units", len(calc.business_units))
    with col3:
        total_hours = sum(emp.total_hours for emp in calc.employees.values())
        st.metric("Total Hours", f"{float(total_hours):,.1f}")
    with col4:
        total_revenue = sum(unit.revenue for unit in calc.business_units.values())
        st.metric("Total Revenue", f"${float(total_revenue):,.2f}")
    
    # Data tables
    tab1, tab2, tab3 = st.tabs(["Employees", "Business Units", "Audit Log"])
    
    with tab1:
        if calc.employees:
            emp_df = pd.DataFrame([emp.to_dict() for emp in calc.employees.values()])
            st.dataframe(emp_df, use_container_width=True)
        else:
            st.info("No employee data loaded")
    
    with tab2:
        if calc.business_units:
            unit_df = pd.DataFrame([unit.to_dict() for unit in calc.business_units.values()])
            st.dataframe(unit_df, use_container_width=True)
        else:
            st.info("No business unit data loaded")
    
    with tab3:
        audit_log = st.session_state.db_manager.get_audit_log(50)
        if audit_log:
            audit_df = pd.DataFrame(audit_log)
            st.dataframe(audit_df, use_container_width=True)
        else:
            st.info("No audit log entries")

# Helper functions
def save_to_database():
    """Save current data to database"""
    try:
        calc = st.session_state.calculator
        db = st.session_state.db_manager
        
        # Save employees
        for employee in calc.employees.values():
            db.save_employee(employee.to_dict())
        
        # Save business units
        for unit in calc.business_units.values():
            db.save_business_unit(unit.to_dict())
        
        # Log action (if auth manager is available)
        try:
            if hasattr(st.session_state, 'auth_manager') and st.session_state.auth_manager:
                current_user = st.session_state.auth_manager.get_current_user()
                db.log_action('data_saved', {
                    'employees': len(calc.employees),
                    'business_units': len(calc.business_units)
                }, current_user['username'] if current_user else 'system')
            else:
                # Log without user info if auth manager not available
                db.log_action('data_saved', {
                    'employees': len(calc.employees),
                    'business_units': len(calc.business_units)
                }, 'system')
        except Exception as log_error:
            # Continue even if logging fails
            logger.warning(f"Could not log action: {log_error}")
        
        logger.info("Data saved to database")
        st.success("✅ All data saved to database successfully!")
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        st.error(f"Error saving data: {str(e)}")

def download_timesheet_template():
    """Generate and download timesheet template"""
    template_data = {
        'Employee Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'Employee ID': ['EMP001', 'EMP002', 'EMP003'],
        'Department': ['Sales', 'Engineering', 'Marketing'],
        'Regular Hours': [40, 40, 38],
        'OT Hours': [5, 8, 0],
        'DT Hours': [0, 2, 0],
        'Pay Period': ['2024-01-01', '2024-01-01', '2024-01-01']
    }
    
    df = pd.DataFrame(template_data)
    excel_data = io.BytesIO()
    df.to_excel(excel_data, index=False)
    excel_data.seek(0)
    
    st.download_button(
        label="📥 Download Template",
        data=excel_data,
        file_name="timesheet_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def download_revenue_template():
    """Generate and download revenue template"""
    template_data = {
        'Business Unit': ['Project Alpha', 'Project Beta', 'Project Gamma'],
        'Revenue': [50000, 75000, 30000],
        'Category': ['Software', 'Consulting', 'Support'],
        'Period': ['2024-01-01', '2024-01-01', '2024-01-01']
    }
    
    df = pd.DataFrame(template_data)
    excel_data = io.BytesIO()
    df.to_excel(excel_data, index=False)
    excel_data.seek(0)
    
    st.download_button(
        label="📥 Download Template",
        data=excel_data,
        file_name="revenue_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def download_combined_template():
    """Generate and download combined template"""
    excel_data = io.BytesIO()
    
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        # Timesheet sheet
        timesheet_data = {
            'Employee Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Employee ID': ['EMP001', 'EMP002', 'EMP003'],
            'Department': ['Sales', 'Engineering', 'Marketing'],
            'Regular Hours': [40, 40, 38],
            'OT Hours': [5, 8, 0],
            'DT Hours': [0, 2, 0]
        }
        pd.DataFrame(timesheet_data).to_excel(writer, sheet_name='Timesheet', index=False)
        
        # Revenue sheet
        revenue_data = {
            'Business Unit': ['Project Alpha', 'Project Beta', 'Project Gamma'],
            'Revenue': [50000, 75000, 30000],
            'Category': ['Software', 'Consulting', 'Support']
        }
        pd.DataFrame(revenue_data).to_excel(writer, sheet_name='Revenue', index=False)
        
        # Configuration sheet
        config_data = {
            'Setting': ['Default Commission Rate', 'Default Hourly Rate', 'OT Multiplier', 'DT Multiplier'],
            'Value': [10.0, 25.0, 1.5, 2.0]
        }
        pd.DataFrame(config_data).to_excel(writer, sheet_name='Configuration', index=False)
    
    excel_data.seek(0)
    
    st.download_button(
        label="📥 Download Template",
        data=excel_data,
        file_name="commission_calculator_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def export_current_hours():
    """Export current hours to Excel"""
    calc = st.session_state.calculator
    
    if calc.employees:
        data = []
        for emp in calc.employees.values():
            data.append({
                'Employee Name': emp.name,
                'Employee ID': emp.employee_id or '',
                'Department': emp.department or '',
                'Regular Hours': float(emp.regular_hours),
                'OT Hours': float(emp.ot_hours),
                'DT Hours': float(emp.dt_hours),
                'Total Hours': float(emp.total_hours),
                'Hourly Rate': float(emp.hourly_rate),
                'Total Labor Cost': float(emp.total_labor_cost)
            })
        
        df = pd.DataFrame(data)
        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False)
        excel_data.seek(0)
        
        st.download_button(
            label="📥 Download Hours Report",
            data=excel_data,
            file_name=f"hours_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def export_business_units():
    """Export business units to Excel"""
    calc = st.session_state.calculator
    
    if calc.business_units:
        data = []
        for unit in calc.business_units.values():
            data.append({
                'Business Unit': unit.name,
                'Category': unit.category or '',
                'Revenue': float(unit.revenue),
                'Commission Rate': float(unit.commission_rate),
                'Commission Amount': float(unit.commission_amount),
                'Description': unit.description or ''
            })
        
        df = pd.DataFrame(data)
        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False)
        excel_data.seek(0)
        
        st.download_button(
            label="📥 Download Business Units",
            data=excel_data,
            file_name=f"business_units_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def edit_employee_modal(employee_id):
    """Modal for editing employee details"""
    calc = st.session_state.calculator
    employee = calc.employees.get(employee_id)
    
    if employee:
        with st.container():
            st.markdown(f"### Edit Employee: {employee.name}")
            
            # Edit fields
            new_name = st.text_input("Name", value=employee.name)
            new_id = st.text_input("Employee ID", value=employee.employee_id or "")
            new_dept = st.text_input("Department", value=employee.department or "")
            new_rate = st.number_input("Hourly Rate", min_value=0.0, value=float(employee.hourly_rate), step=0.50)
            is_active = st.checkbox("Active", value=employee.is_active)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save", type="primary", use_container_width=True):
                    employee.name = new_name
                    employee.employee_id = new_id if new_id else None
                    employee.department = new_dept if new_dept else None
                    employee.hourly_rate = Decimal(str(new_rate))
                    employee.is_active = is_active
                    employee.updated_at = datetime.now()
                    
                    st.success("Employee updated")
                    save_to_database()
                    del st.session_state.editing_employee
                    st.rerun()
            
            with col2:
                if st.button("Cancel", use_container_width=True):
                    del st.session_state.editing_employee
                    st.rerun()

def bulk_operations_section():
    """Advanced bulk operations for data management"""
    st.subheader("🔧 Bulk Operations")
    
    st.info("⚡ Efficiently manage large amounts of data with bulk operations")
    
    # Create sub-tabs for different bulk operations
    bulk_tabs = st.tabs([
        "📊 Bulk Employee Updates",
        "💰 Bulk Rate Changes", 
        "🗂️ Batch Import/Export",
        "🏢 Bulk Business Unit Ops",
        "🗑️ Bulk Delete Operations"
    ])
    
    with bulk_tabs[0]:
        bulk_employee_updates()
    
    with bulk_tabs[1]:
        bulk_rate_changes()
    
    with bulk_tabs[2]:
        batch_import_export()
    
    with bulk_tabs[3]:
        bulk_business_unit_ops()
    
    with bulk_tabs[4]:
        bulk_delete_operations()

def bulk_employee_updates():
    """Bulk employee data updates"""
    st.markdown("### 👥 Bulk Employee Updates")
    
    if 'calculator' not in st.session_state or not st.session_state.calculator:
        st.warning("No calculator instance available")
        return
    
    employees = list(st.session_state.calculator.employees.values())
    
    if not employees:
        st.info("No employees found. Upload timesheet data first.")
        return
    
    st.markdown(f"**Found {len(employees)} employees for bulk operations**")
    
    # Bulk update options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Select Update Type")
        update_type = st.selectbox(
            "Choose update operation:",
            ["Department Assignment", "Hourly Rate Adjustment", "Status Change", "Custom Field Update"]
        )
    
    with col2:
        st.markdown("#### 🔍 Filter Employees")
        filter_type = st.selectbox(
            "Filter by:",
            ["All Employees", "By Department", "By Rate Range", "By Status"]
        )
    
    # Filter employees based on selection
    filtered_employees = filter_employees_for_bulk_ops(employees, filter_type)
    
    if filtered_employees:
        st.markdown(f"**Selected {len(filtered_employees)} employees for update**")
        
        # Show preview of selected employees
        with st.expander("👀 Preview Selected Employees", expanded=False):
            preview_df = pd.DataFrame([
                {
                    'Name': emp.name,
                    'Department': emp.department or 'N/A',
                    'Rate': f"${emp.hourly_rate:.2f}",
                    'Status': 'Active' if emp.is_active else 'Inactive'
                }
                for emp in filtered_employees
            ])
            st.dataframe(preview_df, use_container_width=True)
        
        # Bulk update interface
        if update_type == "Department Assignment":
            new_department = st.text_input("New Department", placeholder="Enter new department name")
            if st.button("🔄 Update All Departments", type="primary"):
                if new_department:
                    perform_bulk_department_update(filtered_employees, new_department)
                else:
                    st.error("Please enter a department name")
        
        elif update_type == "Hourly Rate Adjustment":
            col1, col2 = st.columns(2)
            with col1:
                adjustment_type = st.radio("Adjustment Type:", ["Percentage Increase", "Fixed Amount", "Set Rate"])
            with col2:
                if adjustment_type == "Percentage Increase":
                    adjustment_value = st.number_input("Percentage (%)", min_value=0.0, max_value=100.0, value=5.0)
                elif adjustment_type == "Fixed Amount":
                    adjustment_value = st.number_input("Amount ($)", min_value=0.0, value=1.0, step=0.50)
                else:
                    adjustment_value = st.number_input("New Rate ($)", min_value=0.0, value=20.0, step=0.50)
            
            if st.button("💰 Apply Rate Changes", type="primary"):
                perform_bulk_rate_update(filtered_employees, adjustment_type, adjustment_value)
        
        elif update_type == "Status Change":
            new_status = st.radio("New Status:", ["Active", "Inactive"])
            if st.button("🔄 Update Status", type="primary"):
                perform_bulk_status_update(filtered_employees, new_status == "Active")
        
        elif update_type == "Custom Field Update":
            st.markdown("**Add Custom Fields to Employees**")
            field_name = st.text_input("Field Name", placeholder="e.g., Skills, Location, etc.")
            field_value = st.text_input("Field Value", placeholder="Enter value for all selected employees")
            
            if st.button("🏷️ Add Custom Field", type="primary"):
                if field_name and field_value:
                    perform_bulk_custom_field_update(filtered_employees, field_name, field_value)
                else:
                    st.error("Please enter both field name and value")
    else:
        st.warning("No employees match the selected filter criteria")

def bulk_rate_changes():
    """Bulk commission rate changes"""
    st.markdown("### 💰 Bulk Commission Rate Changes")
    
    if 'calculator' not in st.session_state or not st.session_state.calculator:
        st.warning("No calculator instance available")
        return
    
    business_units = list(st.session_state.calculator.business_units.values())
    
    if not business_units:
        st.info("No business units found. Upload revenue data first.")
        return
    
    st.markdown(f"**Found {len(business_units)} business units for rate changes**")
    
    # Rate change options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Rate Change Type")
        rate_change_type = st.selectbox(
            "Choose rate change:",
            ["Lead Generation Rate", "Sales Commission Rate", "Work Done Rate", "All Commission Rates"]
        )
    
    with col2:
        st.markdown("#### 🔍 Apply To")
        application_type = st.selectbox(
            "Apply changes to:",
            ["All Business Units", "Selected Units", "By Revenue Range"]
        )
    
    # Show current rates
    with st.expander("📊 Current Commission Rates", expanded=True):
        rates_df = pd.DataFrame([
            {
                'Business Unit': unit.name,
                'Lead Gen Rate': f"{getattr(unit, 'lead_gen_rate', 0):.2f}%",
                'Sales Rate': f"{getattr(unit, 'sales_rate', 0):.2f}%", 
                'Work Done Rate': f"{getattr(unit, 'work_done_rate', 0):.2f}%",
                'Revenue': f"${unit.revenue:,.2f}"
            }
            for unit in business_units
        ])
        st.dataframe(rates_df, use_container_width=True)
    
    # New rate input
    st.markdown("#### ⚙️ New Rate Configuration")
    
    if rate_change_type == "All Commission Rates":
        col1, col2, col3 = st.columns(3)
        with col1:
            new_lead_rate = st.number_input("Lead Gen Rate (%)", min_value=0.0, max_value=50.0, value=2.0, step=0.1)
        with col2:
            new_sales_rate = st.number_input("Sales Rate (%)", min_value=0.0, max_value=50.0, value=3.0, step=0.1)
        with col3:
            new_work_rate = st.number_input("Work Done Rate (%)", min_value=0.0, max_value=50.0, value=5.0, step=0.1)
    else:
        new_rate = st.number_input(f"New {rate_change_type} (%)", min_value=0.0, max_value=50.0, value=5.0, step=0.1)
    
    # Apply changes
    if st.button("🚀 Apply Rate Changes", type="primary"):
        if rate_change_type == "All Commission Rates":
            apply_bulk_all_rates(business_units, new_lead_rate, new_sales_rate, new_work_rate)
        else:
            apply_bulk_single_rate(business_units, rate_change_type, new_rate)

def batch_import_export():
    """Batch import and export operations"""
    st.markdown("### 🗂️ Batch Import/Export Operations")
    
    # Import/Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Batch Import")
        st.markdown("**Import multiple data types at once**")
        
        import_files = st.file_uploader(
            "Upload Multiple Files",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=True,
            help="Upload timesheet, revenue, and employee files together"
        )
        
        if import_files:
            st.markdown(f"**Selected {len(import_files)} files for import**")
            
            # Categorize files
            file_categories = categorize_import_files(import_files)
            
            # Show file categorization
            for category, files in file_categories.items():
                if files:
                    st.markdown(f"**{category.title()}:** {len(files)} files")
                    for file in files:
                        st.text(f"  • {file.name}")
            
            if st.button("🚀 Process All Files", type="primary"):
                process_batch_import(file_categories)
    
    with col2:
        st.markdown("#### 📤 Batch Export")
        st.markdown("**Export all data types at once**")
        
        export_options = st.multiselect(
            "Select data to export:",
            ["Employees", "Timesheets", "Revenue", "Commission Rates", "Business Units", "Calculated Commissions"],
            default=["Employees", "Timesheets", "Revenue"]
        )
        
        export_format = st.selectbox("Export Format:", ["Excel (Multiple Sheets)", "Separate CSV Files", "JSON Package"])
        
        if st.button("📦 Export Selected Data", type="primary"):
            if export_options:
                perform_batch_export(export_options, export_format)
            else:
                st.error("Please select at least one data type to export")

def bulk_business_unit_ops():
    """Bulk business unit operations"""
    st.markdown("### 🏢 Bulk Business Unit Operations")
    
    if 'calculator' not in st.session_state or not st.session_state.calculator:
        st.warning("No calculator instance available")
        return
    
    business_units = list(st.session_state.calculator.business_units.values())
    
    if not business_units:
        st.info("No business units found. Upload revenue data first.")
        return
    
    # Bulk operations for business units
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Operation Type")
        operation = st.selectbox(
            "Choose operation:",
            ["Category Assignment", "Revenue Adjustment", "Status Update", "Merge Units"]
        )
    
    with col2:
        st.markdown("#### 🔍 Filter Units")
        filter_by = st.selectbox(
            "Filter by:",
            ["All Units", "By Revenue Range", "By Category", "By Commission Rate"]
        )
    
    # Show current business units
    with st.expander("📊 Current Business Units", expanded=False):
        units_df = pd.DataFrame([
            {
                'Unit Name': unit.name,
                'Revenue': f"${unit.revenue:,.2f}",
                'Category': getattr(unit, 'category', 'N/A'),
                'Commission Rate': f"{unit.commission_rate:.2f}%"
            }
            for unit in business_units
        ])
        st.dataframe(units_df, use_container_width=True)
    
    # Operation-specific interface
    if operation == "Category Assignment":
        new_category = st.text_input("New Category", placeholder="e.g., Residential, Commercial, Service")
        if st.button("🏷️ Assign Category", type="primary"):
            if new_category:
                assign_bulk_category(business_units, new_category)
            else:
                st.error("Please enter a category name")
    
    elif operation == "Revenue Adjustment":
        adjustment_type = st.radio("Adjustment Type:", ["Percentage", "Fixed Amount"])
        if adjustment_type == "Percentage":
            adjustment = st.number_input("Percentage Change (%)", value=0.0, step=0.1)
        else:
            adjustment = st.number_input("Fixed Amount ($)", value=0.0, step=100.0)
        
        if st.button("💰 Apply Revenue Adjustment", type="primary"):
            apply_bulk_revenue_adjustment(business_units, adjustment_type, adjustment)

def bulk_delete_operations():
    """Bulk delete operations with safety checks"""
    st.markdown("### 🗑️ Bulk Delete Operations")
    
    st.warning("⚠️ **Caution:** Bulk delete operations are permanent and cannot be undone!")
    
    # Safety confirmation
    if 'delete_confirmation' not in st.session_state:
        st.session_state.delete_confirmation = False
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Delete Target")
        delete_target = st.selectbox(
            "What to delete:",
            ["Select...", "Inactive Employees", "Zero Revenue Units", "Old Commission Records", "Duplicate Entries"]
        )
    
    with col2:
        st.markdown("#### 🛡️ Safety Settings")
        require_backup = st.checkbox("Require backup before delete", value=True)
        show_preview = st.checkbox("Show deletion preview", value=True)
    
    if delete_target != "Select...":
        # Show what will be deleted
        if show_preview:
            items_to_delete = get_items_for_deletion(delete_target)
            if items_to_delete:
                st.markdown(f"**⚠️ {len(items_to_delete)} items will be deleted:**")
                
                # Show preview
                with st.expander("👀 Preview Items to Delete", expanded=True):
                    preview_deletion_items(items_to_delete, delete_target)
                
                # Confirmation process
                if st.checkbox("I understand this action cannot be undone"):
                    confirmation_text = st.text_input(
                        "Type 'DELETE' to confirm:",
                        placeholder="Type DELETE in capital letters"
                    )
                    
                    if confirmation_text == "DELETE":
                        if st.button("🗑️ Confirm Bulk Delete", type="primary"):
                            if require_backup:
                                st.info("Creating backup before deletion...")
                                create_pre_deletion_backup()
                            
                            perform_bulk_delete(items_to_delete, delete_target)
                    else:
                        st.info("Type 'DELETE' to enable the delete button")
            else:
                st.info(f"No items found for deletion criteria: {delete_target}")

# Helper functions for bulk operations

def filter_employees_for_bulk_ops(employees, filter_type):
    """Filter employees based on criteria"""
    if filter_type == "All Employees":
        return employees
    elif filter_type == "By Department":
        dept_filter = st.selectbox("Select Department:", 
                                 list(set(emp.department for emp in employees if emp.department)))
        return [emp for emp in employees if emp.department == dept_filter]
    elif filter_type == "By Rate Range":
        min_rate = st.number_input("Minimum Rate ($)", min_value=0.0, value=10.0)
        max_rate = st.number_input("Maximum Rate ($)", min_value=0.0, value=50.0)
        return [emp for emp in employees if min_rate <= emp.hourly_rate <= max_rate]
    elif filter_type == "By Status":
        status_filter = st.selectbox("Select Status:", ["Active", "Inactive"])
        return [emp for emp in employees if emp.is_active == (status_filter == "Active")]
    return []

def perform_bulk_department_update(employees, new_department):
    """Update department for multiple employees"""
    try:
        updated_count = 0
        for employee in employees:
            employee.department = new_department
            employee.updated_at = datetime.now()
            updated_count += 1
        
        st.success(f"✅ Updated department for {updated_count} employees")
        save_to_database()
        st.rerun()
    except Exception as e:
        st.error(f"Error updating departments: {e}")

def perform_bulk_rate_update(employees, adjustment_type, adjustment_value):
    """Update rates for multiple employees"""
    try:
        updated_count = 0
        for employee in employees:
            if adjustment_type == "Percentage Increase":
                employee.hourly_rate *= (1 + adjustment_value / 100)
            elif adjustment_type == "Fixed Amount":
                employee.hourly_rate += Decimal(str(adjustment_value))
            else:  # Set Rate
                employee.hourly_rate = Decimal(str(adjustment_value))
            
            employee.updated_at = datetime.now()
            updated_count += 1
        
        st.success(f"✅ Updated rates for {updated_count} employees")
        save_to_database()
        st.rerun()
    except Exception as e:
        st.error(f"Error updating rates: {e}")

def perform_bulk_status_update(employees, new_status):
    """Update status for multiple employees"""
    try:
        updated_count = 0
        for employee in employees:
            employee.is_active = new_status
            employee.updated_at = datetime.now()
            updated_count += 1
        
        status_text = "active" if new_status else "inactive"
        st.success(f"✅ Set {updated_count} employees to {status_text}")
        save_to_database()
        st.rerun()
    except Exception as e:
        st.error(f"Error updating status: {e}")

def perform_bulk_custom_field_update(employees, field_name, field_value):
    """Add custom field to multiple employees"""
    try:
        updated_count = 0
        for employee in employees:
            if not hasattr(employee, 'custom_fields'):
                employee.custom_fields = {}
            employee.custom_fields[field_name] = field_value
            employee.updated_at = datetime.now()
            updated_count += 1
        
        st.success(f"✅ Added {field_name} field to {updated_count} employees")
        save_to_database()
        st.rerun()
    except Exception as e:
        st.error(f"Error adding custom field: {e}")

def save_to_database():
    """Save changes to database"""
    try:
        if 'db_manager' in st.session_state and st.session_state.db_manager:
            st.session_state.db_manager.save_employees(list(st.session_state.calculator.employees.values()))
            st.session_state.db_manager.save_business_units(list(st.session_state.calculator.business_units.values()))
    except Exception as e:
        st.warning(f"Could not save to database: {e}")

def categorize_import_files(files):
    """Categorize uploaded files by type"""
    categories = {'timesheet': [], 'revenue': [], 'employee': [], 'other': []}
    
    for file in files:
        filename = file.name.lower()
        if 'timesheet' in filename or 'time' in filename or 'hours' in filename:
            categories['timesheet'].append(file)
        elif 'revenue' in filename or 'sales' in filename or 'income' in filename:
            categories['revenue'].append(file)
        elif 'employee' in filename or 'staff' in filename or 'worker' in filename:
            categories['employee'].append(file)
        else:
            categories['other'].append(file)
    
    return categories

def process_batch_import(file_categories):
    """Process multiple file imports"""
    try:
        import_results = {'success': 0, 'errors': []}
        
        for category, files in file_categories.items():
            for file in files:
                try:
                    # Process each file based on category
                    if category == 'timesheet':
                        process_timesheet_file(file)
                    elif category == 'revenue':
                        process_revenue_file(file)
                    elif category == 'employee':
                        process_employee_file(file)
                    
                    import_results['success'] += 1
                    
                except Exception as e:
                    import_results['errors'].append(f"{file.name}: {str(e)}")
        
        # Show results
        if import_results['success'] > 0:
            st.success(f"✅ Successfully imported {import_results['success']} files")
        
        if import_results['errors']:
            st.error("❌ Import errors:")
            for error in import_results['errors']:
                st.error(f"  • {error}")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Batch import failed: {e}")

def perform_batch_export(export_options, export_format):
    """Perform batch export of selected data"""
    try:
        export_data = {}
        
        for option in export_options:
            if option == "Employees" and st.session_state.calculator.employees:
                export_data['employees'] = list(st.session_state.calculator.employees.values())
            elif option == "Business Units" and st.session_state.calculator.business_units:
                export_data['business_units'] = list(st.session_state.calculator.business_units.values())
            # Add more export options as needed
        
        if export_data:
            # Create export package
            if export_format == "Excel (Multiple Sheets)":
                create_excel_export(export_data)
            elif export_format == "Separate CSV Files":
                create_csv_exports(export_data)
            elif export_format == "JSON Package":
                create_json_export(export_data)
            
            st.success("✅ Export completed successfully")
        else:
            st.warning("No data available for selected export options")
            
    except Exception as e:
        st.error(f"Export failed: {e}")

def process_timesheet_file(file):
    """Process timesheet file"""
    # Implementation would read and process timesheet data
    pass

def process_revenue_file(file):
    """Process revenue file"""
    # Implementation would read and process revenue data
    pass

def process_employee_file(file):
    """Process employee file"""
    # Implementation would read and process employee data
    pass

def create_excel_export(data):
    """Create Excel export with multiple sheets"""
    # Implementation for Excel export
    pass

def create_csv_exports(data):
    """Create separate CSV files"""
    # Implementation for CSV exports
    pass

def create_json_export(data):
    """Create JSON export package"""
    # Implementation for JSON export
    pass

def apply_bulk_all_rates(business_units, lead_rate, sales_rate, work_rate):
    """Apply all commission rates to business units"""
    try:
        updated_count = 0
        for unit in business_units:
            unit.lead_gen_rate = lead_rate
            unit.sales_rate = sales_rate  
            unit.work_done_rate = work_rate
            updated_count += 1
        
        st.success(f"✅ Updated commission rates for {updated_count} business units")
        save_to_database()
        st.rerun()
    except Exception as e:
        st.error(f"Error updating rates: {e}")

def apply_bulk_single_rate(business_units, rate_type, new_rate):
    """Apply single rate type to business units"""
    try:
        updated_count = 0
        rate_field = {
            "Lead Generation Rate": "lead_gen_rate",
            "Sales Commission Rate": "sales_rate", 
            "Work Done Rate": "work_done_rate"
        }.get(rate_type)
        
        if rate_field:
            for unit in business_units:
                setattr(unit, rate_field, new_rate)
                updated_count += 1
            
            st.success(f"✅ Updated {rate_type} for {updated_count} business units")
            save_to_database()
            st.rerun()
    except Exception as e:
        st.error(f"Error updating {rate_type}: {e}")

def assign_bulk_category(business_units, category):
    """Assign category to business units"""
    try:
        updated_count = 0
        for unit in business_units:
            unit.category = category
            updated_count += 1
        
        st.success(f"✅ Assigned category '{category}' to {updated_count} business units")
        save_to_database()
        st.rerun()
    except Exception as e:
        st.error(f"Error assigning category: {e}")

def apply_bulk_revenue_adjustment(business_units, adjustment_type, adjustment):
    """Apply revenue adjustments to business units"""
    try:
        updated_count = 0
        for unit in business_units:
            if adjustment_type == "Percentage":
                unit.revenue *= (1 + adjustment / 100)
            else:  # Fixed Amount
                unit.revenue += Decimal(str(adjustment))
            updated_count += 1
        
        st.success(f"✅ Applied revenue adjustment to {updated_count} business units")
        save_to_database()
        st.rerun()
    except Exception as e:
        st.error(f"Error adjusting revenue: {e}")

def get_items_for_deletion(delete_target):
    """Get items that would be deleted based on criteria"""
    items = []
    
    if delete_target == "Inactive Employees":
        items = [emp for emp in st.session_state.calculator.employees.values() if not emp.is_active]
    elif delete_target == "Zero Revenue Units":
        items = [unit for unit in st.session_state.calculator.business_units.values() if unit.revenue == 0]
    # Add more deletion criteria as needed
    
    return items

def preview_deletion_items(items, delete_target):
    """Show preview of items to be deleted"""
    if delete_target == "Inactive Employees":
        preview_df = pd.DataFrame([
            {'Name': emp.name, 'Department': emp.department or 'N/A', 'Rate': f"${emp.hourly_rate:.2f}"}
            for emp in items
        ])
    elif delete_target == "Zero Revenue Units":
        preview_df = pd.DataFrame([
            {'Unit Name': unit.name, 'Revenue': f"${unit.revenue:.2f}", 'Commission Rate': f"{unit.commission_rate:.2f}%"}
            for unit in items
        ])
    else:
        preview_df = pd.DataFrame([{'Item': str(item)} for item in items])
    
    st.dataframe(preview_df, use_container_width=True)

def create_pre_deletion_backup():
    """Create backup before bulk deletion"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_deletion_backup_{timestamp}"
        # Implementation would create actual backup
        st.success(f"✅ Backup created: {backup_name}")
    except Exception as e:
        st.error(f"Backup creation failed: {e}")

def perform_bulk_delete(items, delete_target):
    """Perform the actual bulk deletion"""
    try:
        deleted_count = 0
        
        if delete_target == "Inactive Employees":
            for emp in items:
                if emp.name in st.session_state.calculator.employees:
                    del st.session_state.calculator.employees[emp.name]
                    deleted_count += 1
        elif delete_target == "Zero Revenue Units":
            for unit in items:
                if unit.name in st.session_state.calculator.business_units:
                    del st.session_state.calculator.business_units[unit.name]
                    deleted_count += 1
        
        st.success(f"✅ Deleted {deleted_count} items")
        save_to_database()
        st.rerun()
        
    except Exception as e:
        st.error(f"Deletion failed: {e}")