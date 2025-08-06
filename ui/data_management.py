"""
Data Management UI Module
Handles viewing and managing timesheet and revenue data
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from .utils import (
    safe_session_get,
    safe_session_check,
    safe_session_init,
    format_currency,
    show_progress,
    get_revenue_column,
    get_safe_revenue_data,
    validate_file_size,
    validate_file_content
)

def display_data_management_tab():
    """Data Management - Upload, view and manage data"""
    st.markdown("## 📊 Data Management")
    st.markdown("Upload new data and manage your existing timesheet and revenue data")
    
    # Debug: Check what data is available
    revenue_available = safe_session_check('saved_revenue_data') and safe_session_get('saved_revenue_data') is not None
    timesheet_available = safe_session_check('saved_timesheet_data') and safe_session_get('saved_timesheet_data') is not None
    
    # Data status summary
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        if revenue_available:
            revenue_df = safe_session_get('saved_revenue_data')
            st.success(f"✅ Revenue data loaded: {len(revenue_df)} rows")
        else:
            st.info("ℹ️ No revenue data loaded yet")
    
    with status_col2:        
        if timesheet_available:
            timesheet_df = safe_session_get('saved_timesheet_data')
            st.success(f"✅ Timesheet data loaded: {len(timesheet_df)} rows")
        else:
            st.info("ℹ️ No timesheet data loaded yet")
    
    # Three sub-tabs: Upload, then view data
    data_tab1, data_tab2, data_tab3 = st.tabs([
        "📤 Upload Data",
        "💰 Revenue Data", 
        "⏰ Timesheet Data"
    ])
    
    with data_tab1:
        try:
            display_data_upload()
        except Exception as e:
            st.error(f"Error loading upload section: {str(e)}")
    
    with data_tab2:
        try:
            display_revenue_view()
        except Exception as e:
            st.error(f"Error loading revenue section: {str(e)}")
    
    with data_tab3:
        try:
            display_timesheet_management_view()
        except Exception as e:
            st.error(f"Error loading timesheet section: {str(e)}")
            import traceback
            st.text("Full traceback:")
            st.text(traceback.format_exc())

def display_timesheet_management_view():
    """Enhanced timesheet data view with employee totals"""
    st.markdown("### ⏰ Timesheet Data Management")
    
    timesheet_data = safe_session_get('saved_timesheet_data')
    if timesheet_data is None:
        st.info("📤 No timesheet data loaded. Please upload timesheet data first in the Company Setup → Upload Data section.")
        return
    
    raw_timesheet = timesheet_data.copy()
    
    # Debug: Show raw data info
    with st.expander("🔍 Debug: Raw Data Info", expanded=False):
        st.write(f"Raw columns: {list(raw_timesheet.columns)}")
        st.write(f"Raw data shape: {raw_timesheet.shape}")
        st.write(f"Sample raw data:")
        st.dataframe(raw_timesheet.head(3))
    
    # Group by employee and sum hours
    if 'Employee Name' not in raw_timesheet.columns:
        st.error("❌ No 'Employee Name' column found in timesheet data")
        return
    
    # Find hour columns (handle both naming conventions)
    hour_columns = []
    if 'Reg Hours' in raw_timesheet.columns:
        hour_columns.append('Reg Hours')
    elif 'Regular Hours' in raw_timesheet.columns:
        hour_columns.append('Regular Hours')
    
    if 'OT Hours' in raw_timesheet.columns:
        hour_columns.append('OT Hours')
    if 'DT Hours' in raw_timesheet.columns:
        hour_columns.append('DT Hours')
    
    if not hour_columns:
        st.error("❌ No hour columns found in timesheet data")
        return
    
    # Create employee totals
    try:
        # Ensure hour columns are numeric
        for col in hour_columns:
            raw_timesheet[col] = pd.to_numeric(raw_timesheet[col], errors='coerce').fillna(0)
        
        # Group by employee and sum hours
        employee_totals = raw_timesheet.groupby('Employee Name')[hour_columns].sum().reset_index()
        
        # Add total hours column
        employee_totals['Total Hours'] = employee_totals[hour_columns].sum(axis=1)
        
        # Round to 2 decimal places
        for col in hour_columns + ['Total Hours']:
            employee_totals[col] = employee_totals[col].round(2)
        
        st.success(f"✅ Aggregated {len(raw_timesheet)} individual entries into {len(employee_totals)} employee totals")
        
    except Exception as e:
        st.error(f"❌ Error aggregating timesheet data: {str(e)}")
        return
    
    # Display editable employee totals
    st.markdown("#### 📋 Employee Hour Totals")
    st.info("💡 **Tip**: Edit employee hour totals directly. This shows aggregated hours per employee, not individual time entries.")
    
    # Configure columns for better display
    column_config = {}
    for col in hour_columns + ['Total Hours']:
        column_config[col] = st.column_config.NumberColumn(
            col,
            format="%.2f",
            min_value=0,
            help=f"Total {col.lower()} for this employee"
        )
    
    column_config['Employee Name'] = st.column_config.TextColumn(
        "Employee Name",
        help="Employee full name",
        disabled=True  # Don't allow editing employee names
    )
    
    edited_totals = st.data_editor(
        employee_totals,
        hide_index=True,
        use_container_width=True,
        column_config=column_config,
        disabled=False
    )
    
    # Save changes with hour override functionality
    if st.button("💾 Save Changes", type="primary", key="timesheet_mgmt_save"):
        try:
            # Recalculate Total Hours before saving
            edited_totals['Total Hours'] = edited_totals[hour_columns].sum(axis=1)
            
            # Create hour overrides from edited totals
            safe_session_init('timesheet_hour_overrides', {})
            
            # Update hour overrides based on edited totals
            for _, row in edited_totals.iterrows():
                employee_name = row['Employee Name']
                
                # Determine regular hours column name
                regular_hours = 0
                if 'Reg Hours' in row.index:
                    regular_hours = float(row['Reg Hours'])
                elif 'Regular Hours' in row.index:
                    regular_hours = float(row['Regular Hours'])
                
                ot_hours = float(row.get('OT Hours', 0))
                dt_hours = float(row.get('DT Hours', 0))
                
                st.session_state.timesheet_hour_overrides[employee_name] = {
                    'regular_hours': regular_hours,
                    'ot_hours': ot_hours,
                    'dt_hours': dt_hours,
                    'total_hours': regular_hours + ot_hours + dt_hours,
                    'last_updated': datetime.now().isoformat()
                }
            
            st.success("✅ Employee hour totals saved successfully! These totals will override original timesheet data in all calculations.")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error saving changes: {str(e)}")
    
    # Hour Overrides Management Section
    st.markdown("---")
    st.markdown("#### ⚙️ Hour Overrides Management")
    
    overrides = safe_session_get('timesheet_hour_overrides', {})
    if overrides:
        st.markdown("**Active Hour Overrides:**")
        st.info("💡 These edited hour totals override the original timesheet data in all commission calculations.")
        
        # Display current overrides in a summary
        override_summary = []
        for emp_name, hours in overrides.items():
            override_summary.append({
                'Employee': emp_name,
                'Regular Hours': f"{hours.get('regular_hours', 0):.2f}",
                'OT Hours': f"{hours.get('ot_hours', 0):.2f}",
                'DT Hours': f"{hours.get('dt_hours', 0):.2f}",
                'Total Hours': f"{hours.get('total_hours', 0):.2f}",
                'Last Updated': hours.get('last_updated', 'Unknown')[:19].replace('T', ' ')
            })
        
        override_df = pd.DataFrame(override_summary)
        st.dataframe(override_df, use_container_width=True, hide_index=True)
        
        # Clear overrides button
        if st.button("🗑️ Clear All Hour Overrides", key="clear_hour_overrides"):
            st.session_state.timesheet_hour_overrides = {}
            st.success("✅ All hour overrides cleared. Original timesheet data will be used.")
            st.rerun()
    else:
        st.info("No hour overrides active. Edit the table above and save to create overrides.")
    
    # Summary statistics
    st.markdown("---")
    st.markdown("#### 📊 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Employees", len(employee_totals))
    
    with col2:
        total_regular = employee_totals[hour_columns[0]].sum() if hour_columns else 0
        st.metric("Total Regular Hours", f"{total_regular:,.2f}")
    
    with col3:
        total_ot = employee_totals['OT Hours'].sum() if 'OT Hours' in employee_totals.columns else 0
        st.metric("Total OT Hours", f"{total_ot:,.2f}")
    
    with col4:
        total_all = employee_totals['Total Hours'].sum()
        st.metric("Total All Hours", f"{total_all:,.2f}")

def display_revenue_view():
    """Display and manage revenue data"""
    st.markdown("### 💰 Revenue Data Management")
    
    revenue_data = safe_session_get('saved_revenue_data')
    if revenue_data is None:
        st.info("📤 No revenue data loaded. Please upload revenue data first in the Company Setup → Upload Data section.")
        return
    
    # Data overview
    st.markdown("#### 📊 Data Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", len(revenue_data))
    
    with col2:
        revenue_column = get_revenue_column(revenue_data)
        if revenue_column:
            revenue_series = get_safe_revenue_data(revenue_data, revenue_column)
            total_revenue = revenue_series.sum()
            st.metric("Total Revenue", format_currency(total_revenue))
        else:
            st.metric("Total Revenue", "$0")
    
    with col3:
        if 'Business Unit' in revenue_data.columns:
            unique_units = revenue_data['Business Unit'].nunique()
            st.metric("Business Units", unique_units)
        else:
            st.metric("Business Units", 0)
    
    # Display editable revenue data
    st.markdown("#### 📋 Revenue Data")
    
    # Add search/filter
    search_col1, search_col2 = st.columns([2, 1])
    
    with search_col1:
        search_term = st.text_input("🔍 Search revenue data", placeholder="Search by any field...")
    
    with search_col2:
        filter_column = st.selectbox("Filter by column", ["All"] + list(revenue_data.columns))
    
    # Apply search filter
    if search_term:
        if filter_column == "All":
            mask = revenue_data.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)
        else:
            mask = revenue_data[filter_column].astype(str).str.contains(search_term, case=False, na=False)
        filtered_data = revenue_data[mask].copy()
    else:
        filtered_data = revenue_data.copy()
    
    st.info(f"Showing {len(filtered_data)} of {len(revenue_data)} rows")
    
    # Configure columns for better display
    column_config = {}
    
    # Format revenue column
    revenue_column = get_revenue_column(filtered_data)
    if revenue_column:
        column_config[revenue_column] = st.column_config.NumberColumn(
            revenue_column,
            format="$%.2f",
            min_value=0,
            help="Job revenue amount"
        )
    
    # Format date columns
    date_columns = ['Date', 'Job Date', 'Created Date', 'Modified Date']
    for col in date_columns:
        if col in filtered_data.columns:
            column_config[col] = st.column_config.DateColumn(
                col,
                help=f"{col} field"
            )
    
    # Add column for splitting technicians
    if 'Assigned Technicians' in filtered_data.columns:
        # Create individual technician columns
        tech_data = filtered_data.copy()
        
        # Split technicians
        max_techs = 0
        for idx, row in tech_data.iterrows():
            if pd.notna(row.get('Assigned Technicians')):
                techs = str(row['Assigned Technicians']).replace('&', ',').split(',')
                techs = [t.strip() for t in techs if t.strip()]
                max_techs = max(max_techs, len(techs))
                
                # Add individual technician columns
                for i, tech in enumerate(techs):
                    tech_data.loc[idx, f'Technician {i+1}'] = tech
        
        # Fill empty technician columns
        for i in range(max_techs):
            col_name = f'Technician {i+1}'
            if col_name not in tech_data.columns:
                tech_data[col_name] = ''
            
            # Configure technician columns
            column_config[col_name] = st.column_config.TextColumn(
                col_name,
                help=f"Technician #{i+1} assigned to this job"
            )
        
        # Drop the original combined column for editing
        if 'Assigned Technicians' in tech_data.columns:
            tech_data = tech_data.drop(columns=['Assigned Technicians'])
        
        # Display editable data
        edited_data = st.data_editor(
            tech_data,
            hide_index=True,
            use_container_width=True,
            column_config=column_config,
            num_rows="dynamic"
        )
        
        # Save button with technician recombination
        if st.button("💾 Save Revenue Changes", type="primary", key="revenue_save"):
            try:
                # Recombine technician columns
                tech_columns = [col for col in edited_data.columns if col.startswith('Technician ')]
                
                if tech_columns:
                    # Combine technicians back into single column
                    edited_data['Assigned Technicians'] = edited_data[tech_columns].apply(
                        lambda row: ', '.join([str(val) for val in row if pd.notna(val) and str(val).strip()]), 
                        axis=1
                    )
                    
                    # Drop individual technician columns
                    edited_data = edited_data.drop(columns=tech_columns)
                
                # Save to session state
                st.session_state.saved_revenue_data = edited_data
                st.success("✅ Revenue data saved successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving revenue data: {str(e)}")
    else:
        # Display regular editable data without technician splitting
        edited_data = st.data_editor(
            filtered_data,
            hide_index=True,
            use_container_width=True,
            column_config=column_config,
            num_rows="dynamic"
        )
        
        # Save button
        if st.button("💾 Save Revenue Changes", type="primary", key="revenue_save_regular"):
            st.session_state.saved_revenue_data = edited_data
            st.success("✅ Revenue data saved successfully!")
            st.rerun()
    
    # Export functionality
    st.markdown("---")
    st.markdown("#### 📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export to CSV", use_container_width=True):
            csv = revenue_data.to_csv(index=False)
            st.download_button(
                label="Download Revenue CSV",
                data=csv,
                file_name=f"revenue_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 Export to Excel", use_container_width=True):
            # Create Excel file in memory
            from io import BytesIO
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                revenue_data.to_excel(writer, sheet_name='Revenue Data', index=False)
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="Download Revenue Excel",
                data=excel_data,
                file_name=f"revenue_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ========== DATA UPLOAD FUNCTIONS ==========
# Moved from company_setup.py for better organization

def display_data_upload():
    """Data upload interface"""
    st.markdown("### 📤 Upload Data")
    st.markdown("Upload your timesheet, revenue, and employee data files to get started.")
    
    # Create tabs for different data types
    upload_tabs = st.tabs(["⏰ Timesheet Data", "💰 Revenue Data", "👥 Employee Data"])
    
    with upload_tabs[0]:
        display_timesheet_upload()
    
    with upload_tabs[1]:
        display_revenue_upload()
    
    with upload_tabs[2]:
        display_employee_upload()

def display_timesheet_upload():
    """Upload timesheet data"""
    st.markdown("#### 📤 Upload Timesheet Data")
    st.markdown("Upload employee timesheet data containing hours worked for commission calculations.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Timesheet File",
        type=['xlsx', 'xls', 'csv'],
        help="Upload employee timesheet data with hours worked",
        key="timesheet_uploader"
    )
    
    if uploaded_file:
        # Validate file size and content
        size_valid, size_msg = validate_file_size(uploaded_file, max_size_mb=25)
        content_valid, content_msg = validate_file_content(uploaded_file)
        
        if not size_valid:
            st.error(f"❌ {size_msg}")
            return
        
        if not content_valid:
            st.error(f"❌ {content_msg}")
            return
        
        # Show validation success
        if size_msg:
            st.info(f"✅ {size_msg}")
        if content_msg:
            st.info(f"✅ {content_msg}")
        
        try:
            # Read file
            file_ext = uploaded_file.name.lower()
            if file_ext.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Validate DataFrame
            if df.empty:
                st.error("❌ The uploaded timesheet file is empty")
                return
            
            st.success(f"✅ Timesheet data loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Show preview
            st.markdown("**📋 Data Preview:**")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Save button
            if st.button("💾 Save Timesheet Data", type="primary", key="save_timesheet"):
                st.session_state.saved_timesheet_data = df
                st.session_state.timesheet_file_name = uploaded_file.name
                st.success("✅ Timesheet data saved successfully!")
                st.balloons()
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error reading timesheet file: {str(e)}")

def display_revenue_upload():
    """Upload revenue data"""
    st.markdown("#### 📤 Upload Revenue Data")
    st.markdown("Upload business unit revenue data for commission calculations.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Revenue File",
        type=['xlsx', 'xls', 'csv'],
        help="Upload business unit revenue data",
        key="revenue_uploader"
    )
    
    if uploaded_file:
        # Validate file size and content
        size_valid, size_msg = validate_file_size(uploaded_file, max_size_mb=25)
        content_valid, content_msg = validate_file_content(uploaded_file)
        
        if not size_valid:
            st.error(f"❌ {size_msg}")
            return
        
        if not content_valid:
            st.error(f"❌ {content_msg}")
            return
        
        # Show validation success
        if size_msg:
            st.info(f"✅ {size_msg}")
        if content_msg:
            st.info(f"✅ {content_msg}")
        
        try:
            # Read file
            file_ext = uploaded_file.name.lower()
            if file_ext.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            # Validate DataFrame
            if df.empty:
                st.error("❌ The uploaded revenue file is empty")
                return
            
            st.success(f"✅ Revenue data loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Show preview
            st.markdown("**📋 Data Preview:**")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Save button
            if st.button("💾 Save Revenue Data", type="primary", key="save_revenue"):
                st.session_state.saved_revenue_data = df
                st.session_state.revenue_file_name = uploaded_file.name
                st.success("✅ Revenue data saved successfully!")
                st.balloons()
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error reading revenue file: {str(e)}")

def display_employee_upload():
    """Upload employee data"""
    st.markdown("#### 📤 Upload Employee Data")
    st.markdown("Upload employee data in CSV or Excel format to bulk import employee records.")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Employee Data File",
        type=['csv', 'xlsx', 'xls'],
        help="Upload employee data in CSV or Excel format",
        key="employee_uploader"
    )
    
    if uploaded_file:
        # Validate file size and content
        size_valid, size_msg = validate_file_size(uploaded_file, max_size_mb=25)
        content_valid, content_msg = validate_file_content(uploaded_file)
        
        if not size_valid:
            st.error(f"❌ {size_msg}")
            return
        
        if not content_valid:
            st.error(f"❌ {content_msg}")
            return
        
        # Show validation success
        if size_msg:
            st.info(f"✅ {size_msg}")
        if content_msg:
            st.info(f"✅ {content_msg}")
        
        try:
            # Read file
            file_ext = uploaded_file.name.lower()
            if file_ext.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ Employee file loaded: {len(df)} employees found")
            
            # Show preview
            st.markdown("**📋 Data Preview:**")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Save button
            if st.button("💾 Import Employee Data", type="primary", key="save_employees"):
                st.session_state.employee_data = df
                st.success("✅ Employee data imported successfully!")
                st.balloons()
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error reading employee file: {str(e)}")