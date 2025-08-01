"""
Real-time notification system for commission updates
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
try:
    from typing import Literal  # Python 3.8+
except ImportError:
    try:
        from typing_extensions import Literal  # Python 3.7
    except ImportError:
        # Fallback for older Python versions
        Literal = None
from enum import Enum
import json
from pathlib import Path
import time
from collections import deque

class NotificationType(Enum):
    """Types of notifications"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    COMMISSION_UPDATE = "commission_update"
    APPROVAL_REQUIRED = "approval_required"
    REPORT_READY = "report_ready"

class NotificationPriority(Enum):
    """Priority levels for notifications"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Notification:
    """Individual notification object"""
    def __init__(
        self,
        title: str,
        message: str,
        type: NotificationType,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        persistent: bool = False,
        action_url: Optional[str] = None
    ):
        self.id = f"notif_{int(time.time() * 1000)}"
        self.title = title
        self.message = message
        self.type = type
        self.priority = priority
        self.user_id = user_id
        self.metadata = metadata or {}
        self.persistent = persistent
        self.action_url = action_url
        self.created_at = datetime.now()
        self.read = False
        self.dismissed = False

    def to_dict(self) -> Dict:
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "persistent": self.persistent,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat(),
            "read": self.read,
            "dismissed": self.dismissed
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Notification':
        """Create notification from dictionary"""
        notif = cls(
            title=data["title"],
            message=data["message"],
            type=NotificationType(data["type"]),
            priority=NotificationPriority(data["priority"]),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
            persistent=data.get("persistent", False),
            action_url=data.get("action_url")
        )
        notif.id = data["id"]
        notif.created_at = datetime.fromisoformat(data["created_at"])
        notif.read = data.get("read", False)
        notif.dismissed = data.get("dismissed", False)
        return notif

class NotificationManager:
    """Manages notifications across the application"""
    
    def __init__(self, max_notifications: int = 100):
        self.max_notifications = max_notifications
        self.notifications_file = Path("data/notifications.json")
        self.notifications_file.parent.mkdir(exist_ok=True)
        self._load_notifications()
        
        # Initialize session state for real-time updates
        if 'notifications' not in st.session_state:
            st.session_state.notifications = deque(maxlen=max_notifications)
        if 'unread_count' not in st.session_state:
            st.session_state.unread_count = 0
            
    def _load_notifications(self):
        """Load notifications from file"""
        if self.notifications_file.exists():
            try:
                with open(self.notifications_file, 'r') as f:
                    data = json.load(f)
                    self.notifications = deque(
                        [Notification.from_dict(n) for n in data],
                        maxlen=self.max_notifications
                    )
            except Exception:
                self.notifications = deque(maxlen=self.max_notifications)
        else:
            self.notifications = deque(maxlen=self.max_notifications)
    
    def _save_notifications(self):
        """Save notifications to file"""
        try:
            data = [n.to_dict() for n in self.notifications]
            with open(self.notifications_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save notifications: {str(e)}")
    
    def add_notification(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        persistent: bool = False,
        action_url: Optional[str] = None,
        show_toast: bool = True
    ) -> Notification:
        """Add a new notification"""
        notification = Notification(
            title=title,
            message=message,
            type=type,
            priority=priority,
            user_id=user_id,
            metadata=metadata,
            persistent=persistent,
            action_url=action_url
        )
        
        # Add to deque
        self.notifications.appendleft(notification)
        
        # Update session state
        if 'notifications' in st.session_state:
            st.session_state.notifications.appendleft(notification)
            st.session_state.unread_count = self.get_unread_count()
        
        # Save to file
        self._save_notifications()
        
        # Show toast notification
        if show_toast:
            self._show_toast(notification)
        
        return notification
    
    def _show_toast(self, notification: Notification):
        """Display a toast notification"""
        icon_map = {
            NotificationType.SUCCESS: "✅",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.INFO: "ℹ️",
            NotificationType.COMMISSION_UPDATE: "💰",
            NotificationType.APPROVAL_REQUIRED: "🔔",
            NotificationType.REPORT_READY: "📊"
        }
        
        icon = icon_map.get(notification.type, "ℹ️")
        
        if notification.type in [NotificationType.SUCCESS, NotificationType.COMMISSION_UPDATE]:
            st.success(f"{icon} {notification.title}: {notification.message}")
        elif notification.type == NotificationType.WARNING:
            st.warning(f"{icon} {notification.title}: {notification.message}")
        elif notification.type == NotificationType.ERROR:
            st.error(f"{icon} {notification.title}: {notification.message}")
        else:
            st.info(f"{icon} {notification.title}: {notification.message}")
    
    def mark_as_read(self, notification_id: str):
        """Mark a notification as read"""
        for notif in self.notifications:
            if notif.id == notification_id:
                notif.read = True
                break
        
        # Update session state
        if 'notifications' in st.session_state:
            for notif in st.session_state.notifications:
                if notif.id == notification_id:
                    notif.read = True
                    break
            st.session_state.unread_count = self.get_unread_count()
        
        self._save_notifications()
    
    def mark_all_as_read(self, user_id: Optional[str] = None):
        """Mark all notifications as read"""
        for notif in self.notifications:
            if user_id is None or notif.user_id == user_id:
                notif.read = True
        
        # Update session state
        if 'notifications' in st.session_state:
            for notif in st.session_state.notifications:
                if user_id is None or notif.user_id == user_id:
                    notif.read = True
            st.session_state.unread_count = self.get_unread_count()
        
        self._save_notifications()
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss a notification"""
        self.notifications = deque(
            [n for n in self.notifications if n.id != notification_id],
            maxlen=self.max_notifications
        )
        
        # Update session state
        if 'notifications' in st.session_state:
            st.session_state.notifications = deque(
                [n for n in st.session_state.notifications if n.id != notification_id],
                maxlen=self.max_notifications
            )
            st.session_state.unread_count = self.get_unread_count()
        
        self._save_notifications()
    
    def get_notifications(
        self,
        user_id: Optional[str] = None,
        type: Optional[NotificationType] = None,
        unread_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Notification]:
        """Get notifications with filters"""
        notifications = list(self.notifications)
        
        # Filter by user
        if user_id:
            notifications = [n for n in notifications if n.user_id == user_id]
        
        # Filter by type
        if type:
            notifications = [n for n in notifications if n.type == type]
        
        # Filter by read status
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        # Apply limit
        if limit:
            notifications = notifications[:limit]
        
        return notifications
    
    def get_unread_count(self, user_id: Optional[str] = None) -> int:
        """Get count of unread notifications"""
        notifications = self.get_notifications(user_id=user_id, unread_only=True)
        return len(notifications)
    
    def clear_old_notifications(self, days: int = 30):
        """Clear notifications older than specified days"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        self.notifications = deque(
            [n for n in self.notifications if n.created_at.timestamp() > cutoff_date or n.persistent],
            maxlen=self.max_notifications
        )
        
        # Update session state
        if 'notifications' in st.session_state:
            st.session_state.notifications = self.notifications.copy()
            st.session_state.unread_count = self.get_unread_count()
        
        self._save_notifications()

def display_notification_center():
    """Display notification center in the UI"""
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader("🔔 Notifications")
        
        with col2:
            if st.button("Mark All Read", use_container_width=True):
                notification_manager = NotificationManager()
                notification_manager.mark_all_as_read()
                st.rerun()
        
        with col3:
            if st.button("Clear Old", use_container_width=True):
                notification_manager = NotificationManager()
                notification_manager.clear_old_notifications(days=7)
                st.rerun()
        
        notification_manager = NotificationManager()
        notifications = notification_manager.get_notifications(limit=50)
        
        if not notifications:
            st.info("No notifications")
            return
        
        # Group notifications by date
        from itertools import groupby
        from datetime import date
        
        for notif_date, group in groupby(notifications, key=lambda x: x.created_at.date()):
            if notif_date == date.today():
                date_label = "Today"
            elif notif_date == date.today().replace(day=date.today().day - 1):
                date_label = "Yesterday"
            else:
                date_label = notif_date.strftime("%B %d, %Y")
            
            st.caption(f"**{date_label}**")
            
            for notif in group:
                icon_map = {
                    NotificationType.SUCCESS: "✅",
                    NotificationType.WARNING: "⚠️",
                    NotificationType.ERROR: "❌",
                    NotificationType.INFO: "ℹ️",
                    NotificationType.COMMISSION_UPDATE: "💰",
                    NotificationType.APPROVAL_REQUIRED: "🔔",
                    NotificationType.REPORT_READY: "📊"
                }
                
                icon = icon_map.get(notif.type, "ℹ️")
                
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        # Highlight unread notifications
                        if not notif.read:
                            st.markdown(f"**{icon} {notif.title}**")
                            st.caption(f"**{notif.message}**")
                        else:
                            st.markdown(f"{icon} {notif.title}")
                            st.caption(notif.message)
                        
                        # Show action button if available
                        if notif.action_url:
                            st.caption(f"[View Details]({notif.action_url})")
                        
                        st.caption(notif.created_at.strftime("%I:%M %p"))
                    
                    with col2:
                        if not notif.read:
                            if st.button("✓", key=f"read_{notif.id}", help="Mark as read"):
                                notification_manager.mark_as_read(notif.id)
                                st.rerun()
                        
                        if st.button("×", key=f"dismiss_{notif.id}", help="Dismiss"):
                            notification_manager.dismiss_notification(notif.id)
                            st.rerun()
                    
                    st.divider()

def display_notification_badge():
    """Display notification badge with unread count"""
    notification_manager = NotificationManager()
    unread_count = notification_manager.get_unread_count()
    
    if unread_count > 0:
        st.markdown(
            f"""
            <div style="
                display: inline-block;
                background-color: #ff4b4b;
                color: white;
                border-radius: 50%;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 8px;
            ">
                {unread_count if unread_count < 100 else '99+'}
            </div>
            """,
            unsafe_allow_html=True
        )

# Commission-specific notification functions
def notify_commission_calculated(employee_name: str, amount: float, period: str):
    """Send notification when commission is calculated"""
    notification_manager = NotificationManager()
    notification_manager.add_notification(
        title="Commission Calculated",
        message=f"Commission of ${amount:,.2f} calculated for {employee_name} for {period}",
        type=NotificationType.COMMISSION_UPDATE,
        priority=NotificationPriority.MEDIUM,
        metadata={
            "employee_name": employee_name,
            "amount": amount,
            "period": period
        }
    )

def notify_approval_required(employee_name: str, amount: float, approver: str):
    """Send notification when commission needs approval"""
    notification_manager = NotificationManager()
    notification_manager.add_notification(
        title="Approval Required",
        message=f"Commission of ${amount:,.2f} for {employee_name} requires approval",
        type=NotificationType.APPROVAL_REQUIRED,
        priority=NotificationPriority.HIGH,
        user_id=approver,
        metadata={
            "employee_name": employee_name,
            "amount": amount,
            "approver": approver
        },
        persistent=True
    )

def notify_report_ready(report_type: str, user_id: str):
    """Send notification when report is ready"""
    notification_manager = NotificationManager()
    notification_manager.add_notification(
        title="Report Ready",
        message=f"Your {report_type} report has been generated and is ready for download",
        type=NotificationType.REPORT_READY,
        priority=NotificationPriority.LOW,
        user_id=user_id,
        metadata={
            "report_type": report_type
        }
    )

def notify_data_import_complete(file_name: str, records: int, status: str):
    """Send notification when data import is complete"""
    notification_manager = NotificationManager()
    
    if status == "success":
        notification_manager.add_notification(
            title="Import Successful",
            message=f"Successfully imported {records} records from {file_name}",
            type=NotificationType.SUCCESS,
            priority=NotificationPriority.LOW,
            metadata={
                "file_name": file_name,
                "records": records
            }
        )
    else:
        notification_manager.add_notification(
            title="Import Failed",
            message=f"Failed to import {file_name}: {status}",
            type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH,
            metadata={
                "file_name": file_name,
                "error": status
            }
        )