"""
Data upload service - handles file uploads and data validation
"""

from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import io
import logging
from datetime import datetime, date
from decimal import Decimal

from ..models.data_upload import (
    UploadResponse,
    UploadStats,
    UploadValidationError,
    TimesheetData,
    RevenueData,
    EmployeeImportData
)

logger = logging.getLogger(__name__)


class DataUploadService:
    """Service class for data upload and validation"""
    
    def __init__(self):
        pass
    
    async def upload_timesheet_data(self, file_content: bytes, filename: str) -> UploadResponse:
        """
        Process uploaded timesheet data
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            UploadResponse with validation results
        """
        logger.info(f"Processing timesheet upload: {filename}")
        
        try:
            # Read file
            df = self._read_file(file_content, filename)
            
            # Validate and process timesheet data
            validated_data, validation_errors = self._validate_timesheet_data(df)
            
            # Generate stats
            stats = self._generate_upload_stats(df, filename, validation_errors)
            
            # Save data if valid
            if validated_data is not None and len(validation_errors) == 0:
                await self._save_timesheet_data(validated_data)
                logger.info(f"Successfully saved {len(validated_data)} timesheet records")
            
            # Generate preview
            preview_data = df.head(5).fillna('').to_dict('records')
            
            return UploadResponse(
                success=len(validation_errors) == 0,
                message=f"Processed timesheet file: {stats.valid_rows} valid rows, {stats.invalid_rows} invalid rows",
                stats=stats,
                validation_errors=validation_errors,
                preview_data=preview_data
            )
            
        except Exception as e:
            logger.error(f"Failed to process timesheet upload: {str(e)}")
            raise ValueError(f"Failed to process timesheet file: {str(e)}")
    
    async def upload_revenue_data(self, file_content: bytes, filename: str) -> UploadResponse:
        """Process uploaded revenue data"""
        logger.info(f"Processing revenue upload: {filename}")
        
        try:
            # Read file
            df = self._read_file(file_content, filename)
            
            # Validate and process revenue data
            validated_data, validation_errors = self._validate_revenue_data(df)
            
            # Generate stats
            stats = self._generate_upload_stats(df, filename, validation_errors)
            
            # Save data if valid
            if validated_data is not None and len(validation_errors) == 0:
                await self._save_revenue_data(validated_data)
                logger.info(f"Successfully saved {len(validated_data)} revenue records")
            
            # Generate preview
            preview_data = df.head(5).fillna('').to_dict('records')
            
            return UploadResponse(
                success=len(validation_errors) == 0,
                message=f"Processed revenue file: {stats.valid_rows} valid rows, {stats.invalid_rows} invalid rows",
                stats=stats,
                validation_errors=validation_errors,
                preview_data=preview_data
            )
            
        except Exception as e:
            logger.error(f"Failed to process revenue upload: {str(e)}")
            raise ValueError(f"Failed to process revenue file: {str(e)}")
    
    async def upload_employee_data(self, file_content: bytes, filename: str) -> UploadResponse:
        """Process uploaded employee data"""
        logger.info(f"Processing employee upload: {filename}")
        
        try:
            # Read file
            df = self._read_file(file_content, filename)
            
            # Validate and process employee data
            validated_data, validation_errors = self._validate_employee_data(df)
            
            # Generate stats
            stats = self._generate_upload_stats(df, filename, validation_errors)
            
            # Save data if valid
            if validated_data is not None and len(validation_errors) == 0:
                await self._save_employee_data(validated_data)
                logger.info(f"Successfully saved {len(validated_data)} employee records")
            
            # Generate preview
            preview_data = df.head(5).fillna('').to_dict('records')
            
            return UploadResponse(
                success=len(validation_errors) == 0,
                message=f"Processed employee file: {stats.valid_rows} valid rows, {stats.invalid_rows} invalid rows",
                stats=stats,
                validation_errors=validation_errors,
                preview_data=preview_data
            )
            
        except Exception as e:
            logger.error(f"Failed to process employee upload: {str(e)}")
            raise ValueError(f"Failed to process employee file: {str(e)}")
    
    def _read_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Read file content into DataFrame"""
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(io.BytesIO(file_content))
        elif file_ext == 'csv':
            # Try different encodings
            try:
                df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.StringIO(file_content.decode('latin1')))
                except UnicodeDecodeError:
                    df = pd.read_csv(io.StringIO(file_content.decode('cp1252')))
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        if df.empty:
            raise ValueError("The uploaded file is empty")
        
        return df
    
    def _validate_timesheet_data(self, df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], List[UploadValidationError]]:
        """Validate timesheet data"""
        validation_errors = []
        
        # Check required columns
        required_columns = ['Employee Name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation_errors.append(UploadValidationError(
                error_type="MissingColumns",
                message=f"Required columns missing: {', '.join(missing_columns)}",
                value=missing_columns
            ))
            return None, validation_errors
        
        # Find hour columns
        hour_columns = []
        for col in df.columns:
            if 'hour' in col.lower() and any(keyword in col.lower() for keyword in ['reg', 'regular', 'ot', 'overtime', 'dt', 'double']):
                hour_columns.append(col)
        
        if not hour_columns:
            validation_errors.append(UploadValidationError(
                error_type="MissingHourColumns",
                message="No hour columns found (expecting columns with 'hours' and 'reg', 'ot', or 'dt')",
                value=list(df.columns)
            ))
            return None, validation_errors
        
        # Validate each row
        for idx, row in df.iterrows():
            # Check employee name
            if pd.isna(row['Employee Name']) or str(row['Employee Name']).strip() == '':
                validation_errors.append(UploadValidationError(
                    row=idx + 1,
                    column='Employee Name',
                    error_type="RequiredField",
                    message="Employee name is required",
                    value=row.get('Employee Name')
                ))
            
            # Validate hour columns
            for hour_col in hour_columns:
                hour_value = row.get(hour_col)
                if pd.notna(hour_value):
                    try:
                        hour_float = float(hour_value)
                        if hour_float < 0:
                            validation_errors.append(UploadValidationError(
                                row=idx + 1,
                                column=hour_col,
                                error_type="InvalidValue",
                                message="Hours cannot be negative",
                                value=hour_value
                            ))
                    except (ValueError, TypeError):
                        validation_errors.append(UploadValidationError(
                            row=idx + 1,
                            column=hour_col,
                            error_type="InvalidFormat",
                            message="Hours must be a valid number",
                            value=hour_value
                        ))
        
        return df if len(validation_errors) == 0 else None, validation_errors
    
    def _validate_revenue_data(self, df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], List[UploadValidationError]]:
        """Validate revenue data"""
        validation_errors = []
        
        # Check for business unit column
        business_unit_cols = [col for col in df.columns if 'business' in col.lower() and 'unit' in col.lower()]
        if not business_unit_cols:
            validation_errors.append(UploadValidationError(
                error_type="MissingColumns",
                message="Business Unit column not found",
                value=list(df.columns)
            ))
            return None, validation_errors
        
        business_unit_col = business_unit_cols[0]
        
        # Check for revenue column
        revenue_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['revenue', 'total', 'amount'])]
        if not revenue_cols:
            validation_errors.append(UploadValidationError(
                error_type="MissingColumns", 
                message="Revenue column not found (looking for columns containing 'revenue', 'total', or 'amount')",
                value=list(df.columns)
            ))
            return None, validation_errors
        
        revenue_col = revenue_cols[0]
        
        # Validate each row
        for idx, row in df.iterrows():
            # Check business unit
            if pd.isna(row[business_unit_col]) or str(row[business_unit_col]).strip() == '':
                validation_errors.append(UploadValidationError(
                    row=idx + 1,
                    column=business_unit_col,
                    error_type="RequiredField",
                    message="Business unit is required",
                    value=row.get(business_unit_col)
                ))
            
            # Check revenue amount
            revenue_value = row.get(revenue_col)
            if pd.notna(revenue_value):
                try:
                    revenue_float = float(revenue_value)
                    if revenue_float < 0:
                        validation_errors.append(UploadValidationError(
                            row=idx + 1,
                            column=revenue_col,
                            error_type="InvalidValue",
                            message="Revenue cannot be negative",
                            value=revenue_value
                        ))
                except (ValueError, TypeError):
                    validation_errors.append(UploadValidationError(
                        row=idx + 1,
                        column=revenue_col,
                        error_type="InvalidFormat",
                        message="Revenue must be a valid number",
                        value=revenue_value
                    ))
        
        return df if len(validation_errors) == 0 else None, validation_errors
    
    def _validate_employee_data(self, df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], List[UploadValidationError]]:
        """Validate employee data"""
        validation_errors = []
        
        # Check required columns
        required_columns = ['Name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation_errors.append(UploadValidationError(
                error_type="MissingColumns",
                message=f"Required columns missing: {', '.join(missing_columns)}",
                value=missing_columns
            ))
            return None, validation_errors
        
        # Find hourly rate column
        rate_cols = [col for col in df.columns if 'rate' in col.lower() or 'hourly' in col.lower()]
        if not rate_cols:
            validation_errors.append(UploadValidationError(
                error_type="MissingColumns",
                message="Hourly rate column not found",
                value=list(df.columns)
            ))
            return None, validation_errors
        
        rate_col = rate_cols[0]
        
        # Validate each row
        for idx, row in df.iterrows():
            # Check name
            if pd.isna(row['Name']) or str(row['Name']).strip() == '':
                validation_errors.append(UploadValidationError(
                    row=idx + 1,
                    column='Name',
                    error_type="RequiredField",
                    message="Employee name is required",
                    value=row.get('Name')
                ))
            
            # Check hourly rate
            rate_value = row.get(rate_col)
            if pd.notna(rate_value):
                try:
                    rate_float = float(rate_value)
                    if rate_float < 0:
                        validation_errors.append(UploadValidationError(
                            row=idx + 1,
                            column=rate_col,
                            error_type="InvalidValue",
                            message="Hourly rate cannot be negative",
                            value=rate_value
                        ))
                except (ValueError, TypeError):
                    validation_errors.append(UploadValidationError(
                        row=idx + 1,
                        column=rate_col,
                        error_type="InvalidFormat",
                        message="Hourly rate must be a valid number",
                        value=rate_value
                    ))
            
            # Validate status if present
            if 'Status' in df.columns and pd.notna(row.get('Status')):
                status = str(row['Status']).strip()
                valid_statuses = ['Active', 'Inactive', 'Helper/Apprentice', 'Excluded from Payroll']
                if status and status not in valid_statuses:
                    validation_errors.append(UploadValidationError(
                        row=idx + 1,
                        column='Status',
                        error_type="InvalidValue",
                        message=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                        value=status
                    ))
            
            # Validate commission plan if present
            if 'Commission Plan' in df.columns and pd.notna(row.get('Commission Plan')):
                plan = str(row['Commission Plan']).strip()
                valid_plans = ['Hourly + Commission', 'Efficiency Pay']
                if plan and plan not in valid_plans:
                    validation_errors.append(UploadValidationError(
                        row=idx + 1,
                        column='Commission Plan',
                        error_type="InvalidValue",
                        message=f"Invalid commission plan. Must be one of: {', '.join(valid_plans)}",
                        value=plan
                    ))
        
        return df if len(validation_errors) == 0 else None, validation_errors
    
    def _generate_upload_stats(self, df: pd.DataFrame, filename: str, validation_errors: List[UploadValidationError]) -> UploadStats:
        """Generate upload statistics"""
        
        # Count errors by row
        rows_with_errors = set()
        for error in validation_errors:
            if error.row:
                rows_with_errors.add(error.row)
        
        file_size_mb = len(str(df)) / (1024 * 1024)  # Rough estimation
        
        return UploadStats(
            total_rows=len(df),
            valid_rows=len(df) - len(rows_with_errors),
            invalid_rows=len(rows_with_errors),
            duplicate_rows=0,  # TODO: Implement duplicate detection
            columns_found=list(df.columns),
            file_size_mb=round(file_size_mb, 2)
        )
    
    async def _save_timesheet_data(self, df: pd.DataFrame):
        """Save validated timesheet data"""
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        session.save_timesheet_data(df)
    
    async def _save_revenue_data(self, df: pd.DataFrame):
        """Save validated revenue data"""
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        session.save_revenue_data(df)
    
    async def _save_employee_data(self, df: pd.DataFrame):
        """Save validated employee data"""
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        session.save_employee_data(df)