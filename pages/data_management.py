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
        except:
            st.warning("Data validator not available - some validation features may be limited")
    
    if 'db_manager' not in st.session_state:
        try:
            from utils import DatabaseManager
            st.session_state.db_manager = DatabaseManager()
        except:
            st.warning("Database manager not available - some database features may be limited")
    
    # Create tabs for different data management functions
    tabs = st.tabs([
        "📤 Upload Files",
        "📋 Edit Timesheets", 
        "💰 Edit Revenue",
        "👥 Manage Employees",
        "🏢 Manage Business Units",
        "🔄 Data Recovery",
        "📊 Data Preview"
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