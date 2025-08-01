from .database import DatabaseManager
from .auth import AuthManager
from .export import ExportManager
from .validators import DataValidator
from .timesheet_processor import TimesheetProcessor
from .revenue_processor import RevenueProcessor

# Optional imports with error handling
try:
    from .notifications import NotificationManager
except ImportError:
    NotificationManager = None

try:
    from .approval_workflow import ApprovalWorkflow
except ImportError:
    ApprovalWorkflow = None

try:
    from .email_service import EmailService
except ImportError:
    EmailService = None

__all__ = ['DatabaseManager', 'AuthManager', 'ExportManager', 'DataValidator', 
          'TimesheetProcessor', 'RevenueProcessor', 'NotificationManager', 
          'ApprovalWorkflow', 'EmailService']