import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd
from loguru import logger
from contextlib import contextmanager
import threading

class DatabaseManager:
    """Enhanced database manager with SQLite and automatic backups"""
    
    def __init__(self, db_path: str = "commission_data.db", backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.lock = threading.Lock()
        
        # Create backup directory
        Path(backup_dir).mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Run migrations for existing databases
        self._run_migrations()
        
        # Create initial backup
        self.create_backup("initial")
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection context manager"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                conn.close()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Employees table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    hourly_rate REAL DEFAULT 0,
                    department TEXT,
                    employee_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    is_helper INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
            ''')
            
            # Employee hours table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employee_hours (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    regular_hours REAL DEFAULT 0,
                    ot_hours REAL DEFAULT 0,
                    dt_hours REAL DEFAULT 0,
                    period_start TEXT,
                    period_end TEXT,
                    created_at TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            ''')
            
            # Business units table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS business_units (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    commission_rate REAL DEFAULT 0,
                    category TEXT,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
            ''')
            
            # Revenue table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS revenue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_unit_id TEXT NOT NULL,
                    amount REAL DEFAULT 0,
                    period_start TEXT,
                    period_end TEXT,
                    created_at TEXT,
                    FOREIGN KEY (business_unit_id) REFERENCES business_units(id)
                )
            ''')
            
            # Commissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commissions (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    business_unit_id TEXT NOT NULL,
                    amount REAL DEFAULT 0,
                    percentage REAL DEFAULT 100,
                    period_start TEXT,
                    period_end TEXT,
                    status TEXT DEFAULT 'pending',
                    notes TEXT,
                    approved_by TEXT,
                    approved_at TEXT,
                    paid_at TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (business_unit_id) REFERENCES business_units(id)
                )
            ''')
            
            # Commission splits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commission_splits (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    employee_splits TEXT,
                    total_amount REAL,
                    created_by TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    action TEXT,
                    details TEXT,
                    user TEXT,
                    created_at TEXT
                )
            ''')
            
            # Configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuration (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_employee_hours_employee ON employee_hours(employee_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_revenue_unit ON revenue(business_unit_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commissions_employee ON commissions(employee_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commissions_unit ON commissions(business_unit_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commissions_period ON commissions(period_start, period_end)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)')
    
    def _run_migrations(self):
        """Run database migrations for existing databases"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check current table structure
            cursor.execute("PRAGMA table_info(employees)")
            columns_info = cursor.fetchall()
            columns = [column[1] for column in columns_info]
            column_types = {column[1]: column[2] for column in columns_info}
            
            # Add is_helper column if missing
            if 'is_helper' not in columns:
                logger.info("Adding is_helper column to employees table")
                cursor.execute("ALTER TABLE employees ADD COLUMN is_helper INTEGER DEFAULT 0")
                
                # Update any existing Helper/Apprentice employees based on metadata
                cursor.execute("""
                    UPDATE employees 
                    SET is_helper = 1 
                    WHERE metadata LIKE '%"Helper/Apprentice": true%' 
                       OR metadata LIKE '%helper%' 
                       OR metadata LIKE '%apprentice%'
                """)
                
                logger.info("Migration completed: is_helper column added")
            
            # Check if employee_id column needs to be converted to INTEGER
            if 'employee_id' in columns and column_types.get('employee_id') == 'TEXT':
                logger.info("Converting employee_id column from TEXT to INTEGER")
                
                # Create new table with correct schema
                cursor.execute('''
                    CREATE TABLE employees_new (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        hourly_rate REAL DEFAULT 0,
                        department TEXT,
                        employee_id INTEGER,
                        is_active INTEGER DEFAULT 1,
                        is_helper INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT,
                        metadata TEXT
                    )
                ''')
                
                # Copy data, converting employee_id to INTEGER where possible
                cursor.execute('''
                    INSERT INTO employees_new 
                    SELECT id, name, hourly_rate, department, 
                           CASE 
                               WHEN employee_id GLOB '[0-9]*' THEN CAST(employee_id AS INTEGER)
                               ELSE NULL 
                           END as employee_id,
                           is_active, is_helper, created_at, updated_at, metadata
                    FROM employees
                ''')
                
                # Replace old table
                cursor.execute('DROP TABLE employees')
                cursor.execute('ALTER TABLE employees_new RENAME TO employees')
                
                logger.info("Migration completed: employee_id column converted to INTEGER")
    
    def save_employee(self, employee_data: Dict[str, Any]) -> bool:
        """Save or update employee"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO employees 
                    (id, name, hourly_rate, department, employee_id, is_active, is_helper,
                     created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_data['id'],
                    employee_data['name'],
                    employee_data.get('hourly_rate', 0),
                    employee_data.get('department'),
                    employee_data.get('employee_id'),
                    1 if employee_data.get('is_active', True) else 0,
                    1 if employee_data.get('is_helper', False) else 0,
                    employee_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat(),
                    json.dumps(employee_data.get('metadata', {}))
                ))
                
                # Save current hours
                if any(key in employee_data for key in ['regular_hours', 'ot_hours', 'dt_hours']):
                    cursor.execute('''
                        INSERT INTO employee_hours 
                        (employee_id, regular_hours, ot_hours, dt_hours, period_start, period_end, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        employee_data['id'],
                        employee_data.get('regular_hours', 0),
                        employee_data.get('ot_hours', 0),
                        employee_data.get('dt_hours', 0),
                        employee_data.get('period_start', datetime.now().isoformat()),
                        employee_data.get('period_end', datetime.now().isoformat()),
                        datetime.now().isoformat()
                    ))
                
                return True
        except Exception as e:
            logger.error(f"Error saving employee: {e}")
            return False
    
    def save_business_unit(self, unit_data: Dict[str, Any]) -> bool:
        """Save or update business unit"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO business_units
                    (id, name, commission_rate, category, description, is_active,
                     created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    unit_data['id'],
                    unit_data['name'],
                    unit_data.get('commission_rate', 0),
                    unit_data.get('category'),
                    unit_data.get('description'),
                    1 if unit_data.get('is_active', True) else 0,
                    unit_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat(),
                    json.dumps(unit_data.get('metadata', {}))
                ))
                
                # Save revenue if provided
                if 'revenue' in unit_data:
                    cursor.execute('''
                        INSERT INTO revenue
                        (business_unit_id, amount, period_start, period_end, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        unit_data['id'],
                        unit_data['revenue'],
                        unit_data.get('period_start', datetime.now().isoformat()),
                        unit_data.get('period_end', datetime.now().isoformat()),
                        datetime.now().isoformat()
                    ))
                
                return True
        except Exception as e:
            logger.error(f"Error saving business unit: {e}")
            return False
    
    def save_commission(self, commission_data: Dict[str, Any]) -> bool:
        """Save commission record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO commissions
                    (id, employee_id, business_unit_id, amount, percentage,
                     period_start, period_end, status, notes, approved_by,
                     approved_at, paid_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    commission_data['id'],
                    commission_data['employee_id'],
                    commission_data['business_unit_id'],
                    commission_data['amount'],
                    commission_data.get('percentage', 100),
                    commission_data['period_start'],
                    commission_data['period_end'],
                    commission_data.get('status', 'pending'),
                    commission_data.get('notes'),
                    commission_data.get('approved_by'),
                    commission_data.get('approved_at'),
                    commission_data.get('paid_at'),
                    commission_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat()
                ))
                
                return True
        except Exception as e:
            logger.error(f"Error saving commission: {e}")
            return False
    
    def log_action(self, action: str, details: Dict[str, Any], user: str = 'system') -> None:
        """Log action to audit table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_log (timestamp, action, details, user, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    action,
                    json.dumps(details),
                    user,
                    datetime.now().isoformat()
                ))
        except Exception as e:
            logger.error(f"Error logging action: {e}")
    
    def get_employees(self) -> List[Dict[str, Any]]:
        """Get all employees with latest hours"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.*, 
                       h.regular_hours, h.ot_hours, h.dt_hours
                FROM employees e
                LEFT JOIN (
                    SELECT employee_id, regular_hours, ot_hours, dt_hours,
                           ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY created_at DESC) as rn
                    FROM employee_hours
                ) h ON e.id = h.employee_id AND h.rn = 1
                WHERE e.is_active = 1
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_business_units(self) -> List[Dict[str, Any]]:
        """Get all business units with latest revenue"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT b.*,
                       r.amount as revenue
                FROM business_units b
                LEFT JOIN (
                    SELECT business_unit_id, amount,
                           ROW_NUMBER() OVER (PARTITION BY business_unit_id ORDER BY created_at DESC) as rn
                    FROM revenue
                ) r ON b.id = r.business_unit_id AND r.rn = 1
                WHERE b.is_active = 1
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_commissions(self, period_start: Optional[str] = None, 
                       period_end: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get commissions for period"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM commissions WHERE 1=1'
            params = []
            
            if period_start:
                query += ' AND period_start >= ?'
                params.append(period_start)
            
            if period_end:
                query += ' AND period_end <= ?'
                params.append(period_end)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            logs = []
            for row in cursor.fetchall():
                log = dict(row)
                log['details'] = json.loads(log['details'])
                logs.append(log)
            
            return logs
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create database backup"""
        if not backup_name:
            backup_name = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_path = os.path.join(self.backup_dir, f'backup_{backup_name}.db')
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            
            # Keep only last 10 backups
            self._cleanup_old_backups()
            
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore from backup"""
        try:
            # Create safety backup first
            self.create_backup('pre_restore')
            
            # Restore
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files"""
        backup_files = sorted(
            Path(self.backup_dir).glob('backup_*.db'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for backup_file in backup_files[keep_count:]:
            backup_file.unlink()
            logger.info(f"Deleted old backup: {backup_file}")
    
    def export_to_excel(self, file_path: str) -> bool:
        """Export all data to Excel"""
        try:
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                # Export employees
                employees_df = pd.DataFrame(self.get_employees())
                employees_df.to_excel(writer, sheet_name='Employees', index=False)
                
                # Export business units
                units_df = pd.DataFrame(self.get_business_units())
                units_df.to_excel(writer, sheet_name='Business Units', index=False)
                
                # Export commissions
                commissions_df = pd.DataFrame(self.get_commissions())
                commissions_df.to_excel(writer, sheet_name='Commissions', index=False)
                
                # Export audit log
                audit_df = pd.DataFrame(self.get_audit_log(1000))
                audit_df.to_excel(writer, sheet_name='Audit Log', index=False)
            
            logger.info(f"Data exported to Excel: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return False