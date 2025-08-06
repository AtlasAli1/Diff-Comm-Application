"""
Session adapter to bridge API with Streamlit session state
"""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os


class SessionAdapter:
    """
    Adapter class to work with session data in API context
    
    This bridges the gap between the existing Streamlit session state
    and the new REST API by using file-based storage as an intermediate.
    """
    
    def __init__(self, storage_path: str = "api_session_storage"):
        self.storage_path = storage_path
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for a session key"""
        return os.path.join(self.storage_path, f"{key}.json")
    
    def _save_data(self, key: str, data: Any):
        """Save data to file"""
        file_path = self._get_file_path(key)
        
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to JSON
            data = data.to_json(orient='records', date_format='iso')
        elif not isinstance(data, (str, int, float, bool, list, dict, type(None))):
            # Convert other types to string
            data = str(data)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, default=str, indent=2)
    
    def _load_data(self, key: str, default=None):
        """Load data from file"""
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            return default
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, FileNotFoundError):
            return default
    
    def _load_dataframe(self, key: str) -> pd.DataFrame:
        """Load DataFrame from storage"""
        data = self._load_data(key)
        if data is None:
            return pd.DataFrame()
        
        if isinstance(data, str):
            # JSON string from DataFrame
            try:
                return pd.read_json(data, orient='records')
            except (ValueError, TypeError):
                return pd.DataFrame()
        elif isinstance(data, list):
            # List of records
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    
    def get_employee_data(self) -> pd.DataFrame:
        """Get employee data"""
        return self._load_dataframe('employee_data')
    
    def save_employee_data(self, df: pd.DataFrame):
        """Save employee data"""
        self._save_data('employee_data', df)
    
    def add_employee(self, employee_data: Dict[str, Any]) -> int:
        """Add a new employee and return the ID"""
        df = self.get_employee_data()
        
        # Create new row as DataFrame
        new_row = pd.DataFrame([employee_data])
        
        # Append to existing data
        if df.empty:
            df = new_row
        else:
            df = pd.concat([df, new_row], ignore_index=True)
        
        # Save updated data
        self.save_employee_data(df)
        
        # Return the index of the new row (acts as ID)
        return len(df) - 1
    
    def update_employee(self, employee_id: int, update_data: Dict[str, Any]):
        """Update an employee"""
        df = self.get_employee_data()
        
        if df.empty or employee_id >= len(df):
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Update the row
        for key, value in update_data.items():
            df.at[employee_id, key] = value
        
        # Save updated data
        self.save_employee_data(df)
    
    def delete_employee(self, employee_id: int):
        """Delete an employee"""
        df = self.get_employee_data()
        
        if df.empty or employee_id >= len(df):
            raise ValueError(f"Employee with ID {employee_id} not found")
        
        # Drop the row
        df = df.drop(index=employee_id).reset_index(drop=True)
        
        # Save updated data
        self.save_employee_data(df)
    
    def get_timesheet_data(self) -> pd.DataFrame:
        """Get timesheet data"""
        return self._load_dataframe('saved_timesheet_data')
    
    def save_timesheet_data(self, df: pd.DataFrame):
        """Save timesheet data"""
        self._save_data('saved_timesheet_data', df)
    
    def get_revenue_data(self) -> pd.DataFrame:
        """Get revenue data"""
        return self._load_dataframe('saved_revenue_data')
    
    def save_revenue_data(self, df: pd.DataFrame):
        """Save revenue data"""
        self._save_data('saved_revenue_data', df)
    
    def get_pay_periods(self) -> list:
        """Get pay periods"""
        return self._load_data('pay_periods', [])
    
    def save_pay_periods(self, periods: list):
        """Save pay periods"""
        self._save_data('pay_periods', periods)
    
    def get_business_unit_settings(self) -> dict:
        """Get business unit commission settings"""
        return self._load_data('business_unit_commission_settings', {})
    
    def save_business_unit_settings(self, settings: dict):
        """Save business unit commission settings"""
        self._save_data('business_unit_commission_settings', settings)
    
    def get_employee_overrides(self) -> dict:
        """Get employee commission overrides"""
        return self._load_data('employee_commission_overrides', {})
    
    def save_employee_overrides(self, overrides: dict):
        """Save employee commission overrides"""
        self._save_data('employee_commission_overrides', overrides)
    
    def get_timesheet_hour_overrides(self) -> dict:
        """Get timesheet hour overrides"""
        return self._load_data('timesheet_hour_overrides', {})
    
    def save_timesheet_hour_overrides(self, overrides: dict):
        """Save timesheet hour overrides"""
        self._save_data('timesheet_hour_overrides', overrides)
    
    def clear_all_data(self):
        """Clear all stored data"""
        import shutil
        if os.path.exists(self.storage_path):
            shutil.rmtree(self.storage_path)
        self._ensure_storage_directory()
    
    def list_stored_keys(self) -> list:
        """List all stored session keys"""
        if not os.path.exists(self.storage_path):
            return []
        
        files = os.listdir(self.storage_path)
        return [f.replace('.json', '') for f in files if f.endswith('.json')]