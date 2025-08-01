"""
Commission approval workflow system
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field
import json
from pathlib import Path
import uuid

from utils.notifications import notify_approval_required, NotificationManager, NotificationType, NotificationPriority

class ApprovalStatus(str, Enum):
    """Approval status states"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    AUTO_APPROVED = "auto_approved"

class ApprovalLevel(str, Enum):
    """Approval hierarchy levels"""
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"

class ApprovalRule(BaseModel):
    """Defines approval rules based on amount thresholds"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    min_amount: float
    max_amount: Optional[float] = None
    required_level: ApprovalLevel
    auto_approve_below: Optional[float] = None
    escalation_days: int = 3
    active: bool = True

class ApprovalRequest(BaseModel):
    """Individual approval request"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    commission_id: str
    employee_id: str
    employee_name: str
    business_unit_id: str
    business_unit_name: str
    amount: float
    period: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.now)
    approver_id: Optional[str] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    comments: List[Dict[str, str]] = Field(default_factory=list)
    required_level: ApprovalLevel
    
    def add_comment(self, user: str, comment: str):
        """Add a comment to the approval request"""
        self.comments.append({
            "user": user,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        })

class ApprovalWorkflow:
    """Manages the commission approval workflow"""
    
    def __init__(self):
        self.approvals_file = Path("data/approvals.json")
        self.rules_file = Path("data/approval_rules.json")
        self.approvals_file.parent.mkdir(exist_ok=True)
        
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.approval_rules: List[ApprovalRule] = []
        
        self._load_data()
        self._initialize_default_rules()
    
    def _load_data(self):
        """Load approval data from files"""
        # Load approval requests
        if self.approvals_file.exists():
            try:
                with open(self.approvals_file, 'r') as f:
                    data = json.load(f)
                    self.approval_requests = {
                        req['id']: ApprovalRequest(**req) 
                        for req in data
                    }
            except Exception:
                self.approval_requests = {}
        
        # Load approval rules
        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)
                    self.approval_rules = [
                        ApprovalRule(**rule) for rule in rules_data
                    ]
            except Exception:
                self.approval_rules = []
    
    def _save_data(self):
        """Save approval data to files"""
        try:
            # Save approval requests
            requests_data = [
                req.model_dump(mode='json') for req in self.approval_requests.values()
            ]
            with open(self.approvals_file, 'w') as f:
                json.dump(requests_data, f, indent=2, default=str)
            
            # Save approval rules
            rules_data = [rule.model_dump() for rule in self.approval_rules]
            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save approval data: {str(e)}")
    
    def _initialize_default_rules(self):
        """Initialize default approval rules if none exist"""
        if not self.approval_rules:
            default_rules = [
                ApprovalRule(
                    name="Auto-approve small amounts",
                    min_amount=0,
                    max_amount=500,
                    required_level=ApprovalLevel.SUPERVISOR,
                    auto_approve_below=500
                ),
                ApprovalRule(
                    name="Supervisor approval",
                    min_amount=500,
                    max_amount=2000,
                    required_level=ApprovalLevel.SUPERVISOR
                ),
                ApprovalRule(
                    name="Manager approval",
                    min_amount=2000,
                    max_amount=5000,
                    required_level=ApprovalLevel.MANAGER
                ),
                ApprovalRule(
                    name="Director approval",
                    min_amount=5000,
                    max_amount=10000,
                    required_level=ApprovalLevel.DIRECTOR
                ),
                ApprovalRule(
                    name="Executive approval",
                    min_amount=10000,
                    max_amount=None,
                    required_level=ApprovalLevel.EXECUTIVE
                )
            ]
            self.approval_rules = default_rules
            self._save_data()
    
    def get_required_approval_level(self, amount: float) -> Optional[ApprovalLevel]:
        """Determine required approval level based on amount"""
        for rule in sorted(self.approval_rules, key=lambda r: r.min_amount):
            if not rule.active:
                continue
            if rule.min_amount <= amount:
                if rule.max_amount is None or amount <= rule.max_amount:
                    return rule.required_level
        return None
    
    def is_auto_approvable(self, amount: float) -> bool:
        """Check if amount can be auto-approved"""
        for rule in self.approval_rules:
            if not rule.active:
                continue
            if rule.auto_approve_below and amount < rule.auto_approve_below:
                return True
        return False
    
    def create_approval_request(
        self,
        commission_data: Dict,
        requested_by: str
    ) -> ApprovalRequest:
        """Create a new approval request"""
        amount = commission_data['amount']
        required_level = self.get_required_approval_level(amount)
        
        if not required_level:
            required_level = ApprovalLevel.SUPERVISOR
        
        # Check if auto-approvable
        if self.is_auto_approvable(amount):
            status = ApprovalStatus.AUTO_APPROVED
        else:
            status = ApprovalStatus.PENDING
        
        request = ApprovalRequest(
            commission_id=commission_data.get('commission_id', str(uuid.uuid4())),
            employee_id=commission_data['employee_id'],
            employee_name=commission_data['employee_name'],
            business_unit_id=commission_data['business_unit_id'],
            business_unit_name=commission_data['business_unit_name'],
            amount=amount,
            period=commission_data['period'],
            status=status,
            requested_by=requested_by,
            required_level=required_level
        )
        
        self.approval_requests[request.id] = request
        self._save_data()
        
        # Send notification if not auto-approved
        if status == ApprovalStatus.PENDING:
            self._send_approval_notification(request)
        
        return request
    
    def _send_approval_notification(self, request: ApprovalRequest):
        """Send notification for approval required"""
        # Get approvers based on level
        approvers = self.get_approvers_for_level(request.required_level)
        
        for approver in approvers:
            notify_approval_required(
                employee_name=request.employee_name,
                amount=request.amount,
                approver=approver
            )
    
    def get_approvers_for_level(self, level: ApprovalLevel) -> List[str]:
        """Get list of approvers for a given level"""
        # This would typically integrate with your user management system
        # For now, returning mock data
        approvers_map = {
            ApprovalLevel.SUPERVISOR: ["supervisor1", "supervisor2"],
            ApprovalLevel.MANAGER: ["manager1", "manager2"],
            ApprovalLevel.DIRECTOR: ["director1"],
            ApprovalLevel.EXECUTIVE: ["executive1"]
        }
        return approvers_map.get(level, ["admin"])
    
    def approve_request(
        self,
        request_id: str,
        approver_id: str,
        approver_name: str,
        comments: Optional[str] = None
    ) -> bool:
        """Approve a request"""
        request = self.approval_requests.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approver_id = approver_id
        request.approver_name = approver_name
        request.approved_at = datetime.now()
        
        if comments:
            request.add_comment(approver_name, comments)
        
        self._save_data()
        
        # Send notification
        notification_manager = NotificationManager()
        notification_manager.add_notification(
            title="Commission Approved",
            message=f"Commission of ${request.amount:,.2f} for {request.employee_name} has been approved",
            type=NotificationType.SUCCESS,
            priority=NotificationPriority.MEDIUM,
            metadata={
                "request_id": request_id,
                "employee_name": request.employee_name,
                "amount": request.amount
            }
        )
        
        return True
    
    def reject_request(
        self,
        request_id: str,
        approver_id: str,
        approver_name: str,
        reason: str
    ) -> bool:
        """Reject a request"""
        request = self.approval_requests.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.approver_id = approver_id
        request.approver_name = approver_name
        request.approved_at = datetime.now()
        request.rejection_reason = reason
        
        self._save_data()
        
        # Send notification
        notification_manager = NotificationManager()
        notification_manager.add_notification(
            title="Commission Rejected",
            message=f"Commission of ${request.amount:,.2f} for {request.employee_name} has been rejected: {reason}",
            type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            metadata={
                "request_id": request_id,
                "employee_name": request.employee_name,
                "amount": request.amount,
                "reason": reason
            }
        )
        
        return True
    
    def escalate_request(self, request_id: str) -> bool:
        """Escalate a request to higher level"""
        request = self.approval_requests.get(request_id)
        if not request:
            return False
        
        # Determine next level
        level_hierarchy = [
            ApprovalLevel.SUPERVISOR,
            ApprovalLevel.MANAGER,
            ApprovalLevel.DIRECTOR,
            ApprovalLevel.EXECUTIVE
        ]
        
        current_index = level_hierarchy.index(request.required_level)
        if current_index < len(level_hierarchy) - 1:
            request.required_level = level_hierarchy[current_index + 1]
            request.status = ApprovalStatus.ESCALATED
            self._save_data()
            
            # Send escalation notification
            self._send_approval_notification(request)
            return True
        
        return False
    
    def get_pending_approvals(
        self,
        approver_id: Optional[str] = None,
        level: Optional[ApprovalLevel] = None
    ) -> List[ApprovalRequest]:
        """Get pending approval requests"""
        pending = [
            req for req in self.approval_requests.values()
            if req.status in [ApprovalStatus.PENDING, ApprovalStatus.ESCALATED]
        ]
        
        if level:
            pending = [req for req in pending if req.required_level == level]
        
        return sorted(pending, key=lambda r: r.requested_at, reverse=True)
    
    def get_approval_history(
        self,
        employee_id: Optional[str] = None,
        status: Optional[ApprovalStatus] = None,
        limit: int = 100
    ) -> List[ApprovalRequest]:
        """Get approval history with filters"""
        history = list(self.approval_requests.values())
        
        if employee_id:
            history = [req for req in history if req.employee_id == employee_id]
        
        if status:
            history = [req for req in history if req.status == status]
        
        return sorted(history, key=lambda r: r.requested_at, reverse=True)[:limit]
    
    def get_approval_metrics(self) -> Dict:
        """Get approval workflow metrics"""
        requests = list(self.approval_requests.values())
        
        if not requests:
            return {
                "total_requests": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "auto_approved": 0,
                "average_approval_time": 0,
                "approval_rate": 0
            }
        
        # Calculate metrics
        pending = len([r for r in requests if r.status == ApprovalStatus.PENDING])
        approved = len([r for r in requests if r.status == ApprovalStatus.APPROVED])
        rejected = len([r for r in requests if r.status == ApprovalStatus.REJECTED])
        auto_approved = len([r for r in requests if r.status == ApprovalStatus.AUTO_APPROVED])
        
        # Calculate average approval time
        approval_times = []
        for req in requests:
            if req.status == ApprovalStatus.APPROVED and req.approved_at:
                time_diff = (req.approved_at - req.requested_at).total_seconds() / 3600  # hours
                approval_times.append(time_diff)
        
        avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
        
        total_decided = approved + rejected + auto_approved
        approval_rate = ((approved + auto_approved) / total_decided * 100) if total_decided > 0 else 0
        
        return {
            "total_requests": len(requests),
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "auto_approved": auto_approved,
            "average_approval_time": round(avg_approval_time, 1),
            "approval_rate": round(approval_rate, 1)
        }

def display_approval_dashboard():
    """Display approval dashboard in Streamlit"""
    st.title("🔔 Commission Approval Workflow")
    
    workflow = ApprovalWorkflow()
    
    # User role (would come from auth system)
    user_role = st.session_state.get('user', {}).get('role', 'viewer')
    user_id = st.session_state.get('user', {}).get('username', 'guest')
    
    # Tabs for different views
    tabs = st.tabs(["📋 Pending Approvals", "📊 Approval Metrics", "⚙️ Approval Rules", "📜 History"])
    
    with tabs[0]:
        display_pending_approvals(workflow, user_id, user_role)
    
    with tabs[1]:
        display_approval_metrics(workflow)
    
    with tabs[2]:
        if user_role in ['admin', 'manager']:
            display_approval_rules(workflow)
        else:
            st.warning("You don't have permission to manage approval rules")
    
    with tabs[3]:
        display_approval_history(workflow)

def display_pending_approvals(workflow: ApprovalWorkflow, user_id: str, user_role: str):
    """Display pending approvals"""
    st.subheader("📋 Pending Approvals")
    
    # Get pending approvals based on user level
    level_map = {
        'supervisor': ApprovalLevel.SUPERVISOR,
        'manager': ApprovalLevel.MANAGER,
        'director': ApprovalLevel.DIRECTOR,
        'executive': ApprovalLevel.EXECUTIVE,
        'admin': None  # Admin can see all
    }
    
    user_level = level_map.get(user_role)
    pending = workflow.get_pending_approvals(level=user_level)
    
    if not pending:
        st.info("No pending approvals")
        return
    
    for request in pending:
        with st.expander(f"🔔 {request.employee_name} - ${request.amount:,.2f}", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Employee:** {request.employee_name}")
                st.write(f"**Business Unit:** {request.business_unit_name}")
                st.write(f"**Period:** {request.period}")
                st.write(f"**Amount:** ${request.amount:,.2f}")
                st.write(f"**Required Level:** {request.required_level.value}")
                st.write(f"**Requested by:** {request.requested_by}")
                st.write(f"**Requested at:** {request.requested_at.strftime('%Y-%m-%d %H:%M')}")
                
                if request.status == ApprovalStatus.ESCALATED:
                    st.warning("⚠️ This request has been escalated")
            
            with col2:
                if user_role in ['admin', 'manager', 'supervisor', 'director', 'executive']:
                    comments = st.text_area(
                        "Comments",
                        key=f"comments_{request.id}",
                        height=100
                    )
                    
                    if st.button("✅ Approve", key=f"approve_{request.id}", type="primary"):
                        if workflow.approve_request(request.id, user_id, user_id, comments):
                            st.success("Approved successfully!")
                            st.rerun()
            
            with col3:
                if user_role in ['admin', 'manager', 'supervisor', 'director', 'executive']:
                    reason = st.text_area(
                        "Rejection Reason",
                        key=f"reason_{request.id}",
                        height=100
                    )
                    
                    if st.button("❌ Reject", key=f"reject_{request.id}"):
                        if reason:
                            if workflow.reject_request(request.id, user_id, user_id, reason):
                                st.success("Rejected successfully!")
                                st.rerun()
                        else:
                            st.error("Please provide a rejection reason")
                    
                    if request.required_level != ApprovalLevel.EXECUTIVE:
                        if st.button("⬆️ Escalate", key=f"escalate_{request.id}"):
                            if workflow.escalate_request(request.id):
                                st.success("Escalated successfully!")
                                st.rerun()
            
            # Show comments
            if request.comments:
                st.divider()
                st.caption("**Comments:**")
                for comment in request.comments:
                    st.caption(f"{comment['user']} ({comment['timestamp']}): {comment['comment']}")

def display_approval_metrics(workflow: ApprovalWorkflow):
    """Display approval metrics"""
    st.subheader("📊 Approval Metrics")
    
    metrics = workflow.get_approval_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", metrics['total_requests'])
    
    with col2:
        st.metric("Pending", metrics['pending'], delta=None, delta_color="normal")
    
    with col3:
        st.metric("Approval Rate", f"{metrics['approval_rate']}%")
    
    with col4:
        st.metric("Avg. Approval Time", f"{metrics['average_approval_time']}h")
    
    # Detailed breakdown
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Status Distribution")
        status_data = {
            "Approved": metrics['approved'],
            "Rejected": metrics['rejected'],
            "Auto-Approved": metrics['auto_approved'],
            "Pending": metrics['pending']
        }
        
        import plotly.express as px
        fig = px.pie(
            values=list(status_data.values()),
            names=list(status_data.keys()),
            color_discrete_map={
                "Approved": "#28a745",
                "Rejected": "#dc3545",
                "Auto-Approved": "#17a2b8",
                "Pending": "#ffc107"
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Approval Trends")
        # This would show approval trends over time
        st.info("Approval trends visualization coming soon")

def display_approval_rules(workflow: ApprovalWorkflow):
    """Display and manage approval rules"""
    st.subheader("⚙️ Approval Rules")
    
    # Add new rule
    with st.expander("➕ Add New Rule"):
        with st.form("new_rule"):
            name = st.text_input("Rule Name")
            col1, col2 = st.columns(2)
            with col1:
                min_amount = st.number_input("Min Amount", min_value=0.0, step=100.0)
            with col2:
                max_amount = st.number_input("Max Amount (0 for no limit)", min_value=0.0, step=100.0)
            
            required_level = st.selectbox(
                "Required Approval Level",
                options=[level.value for level in ApprovalLevel]
            )
            
            auto_approve = st.number_input(
                "Auto-approve below (0 to disable)",
                min_value=0.0,
                step=100.0
            )
            
            if st.form_submit_button("Add Rule"):
                new_rule = ApprovalRule(
                    name=name,
                    min_amount=min_amount,
                    max_amount=max_amount if max_amount > 0 else None,
                    required_level=ApprovalLevel(required_level),
                    auto_approve_below=auto_approve if auto_approve > 0 else None
                )
                workflow.approval_rules.append(new_rule)
                workflow._save_data()
                st.success("Rule added successfully!")
                st.rerun()
    
    # Display existing rules
    st.markdown("### Current Rules")
    
    for rule in sorted(workflow.approval_rules, key=lambda r: r.min_amount):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                st.write(f"**{rule.name}**")
                amount_range = f"${rule.min_amount:,.0f}"
                if rule.max_amount:
                    amount_range += f" - ${rule.max_amount:,.0f}"
                else:
                    amount_range += "+"
                st.caption(amount_range)
            
            with col2:
                st.write(f"Level: {rule.required_level.value}")
                if rule.auto_approve_below:
                    st.caption(f"Auto-approve < ${rule.auto_approve_below:,.0f}")
            
            with col3:
                if rule.active:
                    st.success("Active")
                else:
                    st.error("Inactive")
            
            with col4:
                if st.button("Toggle", key=f"toggle_{rule.id}"):
                    rule.active = not rule.active
                    workflow._save_data()
                    st.rerun()
            
            st.divider()

def display_approval_history(workflow: ApprovalWorkflow):
    """Display approval history"""
    st.subheader("📜 Approval History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "Filter by Status",
            options=["All"] + [status.value for status in ApprovalStatus]
        )
    
    with col2:
        filter_employee = st.text_input("Filter by Employee Name")
    
    with col3:
        limit = st.number_input("Show last N records", min_value=10, max_value=1000, value=100)
    
    # Get filtered history
    status_filter = None if filter_status == "All" else ApprovalStatus(filter_status)
    history = workflow.get_approval_history(status=status_filter, limit=limit)
    
    if filter_employee:
        history = [
            req for req in history 
            if filter_employee.lower() in req.employee_name.lower()
        ]
    
    if not history:
        st.info("No approval history found")
        return
    
    # Display history
    for request in history:
        status_color = {
            ApprovalStatus.APPROVED: "🟢",
            ApprovalStatus.REJECTED: "🔴",
            ApprovalStatus.PENDING: "🟡",
            ApprovalStatus.AUTO_APPROVED: "🔵",
            ApprovalStatus.ESCALATED: "🟠"
        }
        
        icon = status_color.get(request.status, "⚪")
        
        with st.expander(
            f"{icon} {request.employee_name} - ${request.amount:,.2f} - {request.status.value}"
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Employee:** {request.employee_name}")
                st.write(f"**Business Unit:** {request.business_unit_name}")
                st.write(f"**Period:** {request.period}")
                st.write(f"**Amount:** ${request.amount:,.2f}")
                st.write(f"**Status:** {request.status.value}")
            
            with col2:
                st.write(f"**Requested by:** {request.requested_by}")
                st.write(f"**Requested at:** {request.requested_at.strftime('%Y-%m-%d %H:%M')}")
                
                if request.approver_name:
                    st.write(f"**Approver:** {request.approver_name}")
                    st.write(f"**Decision at:** {request.approved_at.strftime('%Y-%m-%d %H:%M')}")
                
                if request.rejection_reason:
                    st.write(f"**Rejection Reason:** {request.rejection_reason}")
            
            if request.comments:
                st.divider()
                st.caption("**Comments:**")
                for comment in request.comments:
                    st.caption(f"{comment['user']}: {comment['comment']}")