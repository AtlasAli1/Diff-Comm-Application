"""
Email service for automated report delivery
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Dict, Optional, Union
from datetime import datetime
import json
from pathlib import Path
import streamlit as st
from jinja2 import Template
import schedule
import time
import threading
from loguru import logger

class EmailConfig:
    """Email configuration settings"""
    def __init__(self):
        self.config_file = Path("config/email_config.json")
        self.config_file.parent.mkdir(exist_ok=True)
        self.load_config()
    
    def load_config(self):
        """Load email configuration from file or environment"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        else:
            # Default configuration
            config = {
                "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "use_tls": os.getenv("USE_TLS", "true").lower() == "true",
                "sender_email": os.getenv("SENDER_EMAIL", ""),
                "sender_password": os.getenv("SENDER_PASSWORD", ""),
                "sender_name": os.getenv("SENDER_NAME", "Commission Calculator Pro"),
                "reply_to": os.getenv("REPLY_TO_EMAIL", ""),
                "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true"
            }
        
        self.smtp_server = config.get("smtp_server")
        self.smtp_port = config.get("smtp_port")
        self.use_tls = config.get("use_tls")
        self.sender_email = config.get("sender_email")
        self.sender_password = config.get("sender_password")
        self.sender_name = config.get("sender_name")
        self.reply_to = config.get("reply_to")
        self.enabled = config.get("enabled")
    
    def save_config(self, config_data: Dict):
        """Save email configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        self.load_config()
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.enabled and self.sender_email and self.sender_password)

class EmailTemplate:
    """Email templates for different report types"""
    
    COMMISSION_REPORT = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background-color: #2C5F75; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
            .footer { background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #2C5F75; color: white; }
            .highlight { background-color: #e8f4f8; font-weight: bold; }
            .metric { display: inline-block; margin: 10px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Commission Report</h1>
            <p>{{ period }}</p>
        </div>
        <div class="content">
            <p>Dear {{ recipient_name }},</p>
            
            <p>Please find your commission report for the period {{ period_start }} to {{ period_end }}.</p>
            
            <div style="text-align: center;">
                <div class="metric">
                    <h3>Total Commission</h3>
                    <p style="font-size: 24px; color: #2C5F75;">${{ total_commission|round(2) }}</p>
                </div>
                <div class="metric">
                    <h3>Total Hours</h3>
                    <p style="font-size: 24px; color: #2C5F75;">{{ total_hours|round(1) }}</p>
                </div>
                <div class="metric">
                    <h3>Effective Rate</h3>
                    <p style="font-size: 24px; color: #2C5F75;">${{ effective_rate|round(2) }}/hr</p>
                </div>
            </div>
            
            <h2>Commission Details</h2>
            <table>
                <tr>
                    <th>Business Unit</th>
                    <th>Hours</th>
                    <th>Revenue</th>
                    <th>Commission Rate</th>
                    <th>Commission Amount</th>
                </tr>
                {% for detail in commission_details %}
                <tr>
                    <td>{{ detail.business_unit }}</td>
                    <td>{{ detail.hours|round(1) }}</td>
                    <td>${{ detail.revenue|round(2) }}</td>
                    <td>{{ detail.rate }}%</td>
                    <td>${{ detail.amount|round(2) }}</td>
                </tr>
                {% endfor %}
                <tr class="highlight">
                    <td colspan="4">Total</td>
                    <td>${{ total_commission|round(2) }}</td>
                </tr>
            </table>
            
            <p>If you have any questions about this report, please contact your manager.</p>
            
            <p>Best regards,<br>
            {{ sender_name }}</p>
        </div>
        <div class="footer">
            <p>This is an automated email from Commission Calculator Pro. Please do not reply to this email.</p>
            <p>Generated on {{ generated_date }}</p>
        </div>
    </body>
    </html>
    """
    
    SUMMARY_REPORT = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background-color: #2C5F75; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; }
            .metric-box { display: inline-block; margin: 10px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; text-align: center; }
            .metric-value { font-size: 28px; color: #2C5F75; font-weight: bold; }
            .metric-label { font-size: 14px; color: #666; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Executive Commission Summary</h1>
            <p>{{ period }}</p>
        </div>
        <div class="content">
            <p>Dear {{ recipient_name }},</p>
            
            <p>Here is the executive summary for {{ period }}:</p>
            
            <div style="text-align: center;">
                <div class="metric-box">
                    <div class="metric-value">${{ total_revenue|round(0) }}</div>
                    <div class="metric-label">Total Revenue</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">${{ total_commissions|round(0) }}</div>
                    <div class="metric-label">Total Commissions</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{{ commission_rate|round(1) }}%</div>
                    <div class="metric-label">Commission Rate</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{{ employee_count }}</div>
                    <div class="metric-label">Active Employees</div>
                </div>
            </div>
            
            {{ additional_content|safe }}
            
            <p>Best regards,<br>
            {{ sender_name }}</p>
        </div>
    </body>
    </html>
    """

class EmailService:
    """Service for sending automated emails"""
    
    def __init__(self):
        self.config = EmailConfig()
        self.templates = {
            'commission_report': Template(EmailTemplate.COMMISSION_REPORT),
            'summary_report': Template(EmailTemplate.SUMMARY_REPORT)
        }
        self.scheduled_jobs = []
        self.scheduler_thread = None
        self.scheduler_running = False
    
    def test_connection(self) -> tuple[bool, str]:
        """Test email connection"""
        if not self.config.is_configured():
            return False, "Email service not configured"
        
        try:
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.sender_email, self.config.sender_password)
            server.quit()
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def send_email(
        self,
        recipients: Union[str, List[str]],
        subject: str,
        body_html: str,
        attachments: Optional[List[Dict[str, any]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> tuple[bool, str]:
        """Send email with optional attachments"""
        
        if not self.config.is_configured():
            return False, "Email service not configured"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.sender_name} <{self.config.sender_email}>"
            msg['Subject'] = subject
            
            # Handle recipients
            if isinstance(recipients, str):
                recipients = [recipients]
            msg['To'] = ', '.join(recipients)
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            if self.config.reply_to:
                msg['Reply-To'] = self.config.reply_to
            
            # Add HTML body
            msg.attach(MIMEText(body_html, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            if self.config.use_tls:
                server.starttls()
            server.login(self.config.sender_email, self.config.sender_password)
            
            all_recipients = recipients + (cc or []) + (bcc or [])
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()
            
            logger.info(f"Email sent successfully to {recipients}")
            return True, "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
    
    def send_commission_report(
        self,
        recipient_email: str,
        recipient_name: str,
        commission_data: Dict,
        attachment: Optional[bytes] = None
    ) -> tuple[bool, str]:
        """Send commission report email"""
        
        # Prepare template data
        template_data = {
            'recipient_name': recipient_name,
            'period': commission_data.get('period', 'Current Period'),
            'period_start': commission_data.get('period_start', ''),
            'period_end': commission_data.get('period_end', ''),
            'total_commission': commission_data.get('total_commission', 0),
            'total_hours': commission_data.get('total_hours', 0),
            'effective_rate': commission_data.get('effective_rate', 0),
            'commission_details': commission_data.get('details', []),
            'sender_name': self.config.sender_name,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        # Render template
        body_html = self.templates['commission_report'].render(**template_data)
        
        # Prepare attachments
        attachments = []
        if attachment:
            attachments.append({
                'filename': f'commission_report_{datetime.now().strftime("%Y%m%d")}.pdf',
                'content': attachment
            })
        
        # Send email
        subject = f"Commission Report - {template_data['period']}"
        return self.send_email(recipient_email, subject, body_html, attachments)
    
    def send_summary_report(
        self,
        recipients: List[str],
        summary_data: Dict
    ) -> tuple[bool, str]:
        """Send executive summary report"""
        
        # Prepare template data
        template_data = {
            'recipient_name': 'Team',
            'period': summary_data.get('period', 'Current Period'),
            'total_revenue': summary_data.get('total_revenue', 0),
            'total_commissions': summary_data.get('total_commissions', 0),
            'commission_rate': summary_data.get('commission_rate', 0),
            'employee_count': summary_data.get('employee_count', 0),
            'additional_content': summary_data.get('additional_content', ''),
            'sender_name': self.config.sender_name
        }
        
        # Render template
        body_html = self.templates['summary_report'].render(**template_data)
        
        # Send email
        subject = f"Executive Commission Summary - {template_data['period']}"
        return self.send_email(recipients, subject, body_html)
    
    def schedule_report(
        self,
        report_type: str,
        recipients: List[str],
        schedule_time: str,
        frequency: str = 'daily',
        **kwargs
    ):
        """Schedule automated report delivery"""
        
        job_id = f"{report_type}_{datetime.now().timestamp()}"
        
        def job():
            if report_type == 'commission':
                # Generate and send commission reports
                for recipient in recipients:
                    # This would integrate with your report generation
                    pass
            elif report_type == 'summary':
                # Generate and send summary report
                pass
        
        # Schedule based on frequency
        if frequency == 'daily':
            schedule.every().day.at(schedule_time).do(job).tag(job_id)
        elif frequency == 'weekly':
            schedule.every().week.at(schedule_time).do(job).tag(job_id)
        elif frequency == 'monthly':
            schedule.every(30).days.at(schedule_time).do(job).tag(job_id)
        
        self.scheduled_jobs.append({
            'id': job_id,
            'type': report_type,
            'recipients': recipients,
            'schedule': f"{frequency} at {schedule_time}",
            'created': datetime.now()
        })
        
        # Start scheduler if not running
        if not self.scheduler_running:
            self.start_scheduler()
    
    def start_scheduler(self):
        """Start the email scheduler in a separate thread"""
        def run_scheduler():
            self.scheduler_running = True
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the email scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
    
    def get_scheduled_jobs(self) -> List[Dict]:
        """Get list of scheduled email jobs"""
        return self.scheduled_jobs
    
    def cancel_scheduled_job(self, job_id: str):
        """Cancel a scheduled job"""
        schedule.clear(job_id)
        self.scheduled_jobs = [j for j in self.scheduled_jobs if j['id'] != job_id]

def display_email_configuration():
    """Display email configuration interface in Streamlit"""
    st.subheader("📧 Email Configuration")
    
    email_service = EmailService()
    config = email_service.config
    
    with st.form("email_config"):
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input("SMTP Server", value=config.smtp_server)
            smtp_port = st.number_input("SMTP Port", value=config.smtp_port, min_value=1, max_value=65535)
            use_tls = st.checkbox("Use TLS", value=config.use_tls)
        
        with col2:
            sender_email = st.text_input("Sender Email", value=config.sender_email)
            sender_password = st.text_input("Sender Password", type="password", value="")
            sender_name = st.text_input("Sender Name", value=config.sender_name)
        
        reply_to = st.text_input("Reply-To Email", value=config.reply_to or "")
        enabled = st.checkbox("Enable Email Service", value=config.enabled)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Save Configuration", type="primary"):
                config_data = {
                    "smtp_server": smtp_server,
                    "smtp_port": smtp_port,
                    "use_tls": use_tls,
                    "sender_email": sender_email,
                    "sender_password": sender_password if sender_password else config.sender_password,
                    "sender_name": sender_name,
                    "reply_to": reply_to,
                    "enabled": enabled
                }
                config.save_config(config_data)
                st.success("Configuration saved successfully!")
        
        with col2:
            if st.form_submit_button("Test Connection"):
                success, message = email_service.test_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)

def display_email_scheduler():
    """Display email scheduler interface"""
    st.subheader("📅 Email Scheduler")
    
    email_service = EmailService()
    
    # Add new scheduled report
    with st.expander("Schedule New Report"):
        report_type = st.selectbox(
            "Report Type",
            ["commission", "summary"]
        )
        
        recipients = st.text_area(
            "Recipients (one per line)",
            help="Enter email addresses, one per line"
        ).split('\n')
        
        col1, col2 = st.columns(2)
        
        with col1:
            frequency = st.selectbox(
                "Frequency",
                ["daily", "weekly", "monthly"]
            )
        
        with col2:
            schedule_time = st.time_input("Send Time")
        
        if st.button("Schedule Report"):
            email_service.schedule_report(
                report_type=report_type,
                recipients=[r.strip() for r in recipients if r.strip()],
                schedule_time=schedule_time.strftime("%H:%M"),
                frequency=frequency
            )
            st.success("Report scheduled successfully!")
    
    # Display scheduled jobs
    st.markdown("### Scheduled Reports")
    
    jobs = email_service.get_scheduled_jobs()
    if not jobs:
        st.info("No scheduled reports")
    else:
        for job in jobs:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{job['type'].title()} Report**")
                    st.caption(f"Recipients: {', '.join(job['recipients'])}")
                
                with col2:
                    st.write(f"Schedule: {job['schedule']}")
                    st.caption(f"Created: {job['created'].strftime('%Y-%m-%d')}")
                
                with col3:
                    if st.button("Cancel", key=f"cancel_{job['id']}"):
                        email_service.cancel_scheduled_job(job['id'])
                        st.rerun()
                
                st.divider()

def send_test_email():
    """Send a test email"""
    st.subheader("📤 Send Test Email")
    
    email_service = EmailService()
    
    if not email_service.config.is_configured():
        st.warning("Please configure email settings first")
        return
    
    with st.form("test_email"):
        recipient = st.text_input("Recipient Email")
        
        test_type = st.selectbox(
            "Test Type",
            ["Simple Test", "Commission Report", "Summary Report"]
        )
        
        if st.form_submit_button("Send Test Email"):
            if test_type == "Simple Test":
                success, message = email_service.send_email(
                    recipients=recipient,
                    subject="Test Email from Commission Calculator Pro",
                    body_html="<h1>Test Email</h1><p>This is a test email from Commission Calculator Pro.</p>"
                )
            elif test_type == "Commission Report":
                # Sample commission data
                commission_data = {
                    'period': 'Test Period',
                    'period_start': '2024-01-01',
                    'period_end': '2024-01-31',
                    'total_commission': 5000.00,
                    'total_hours': 160,
                    'effective_rate': 31.25,
                    'details': [
                        {
                            'business_unit': 'Test Unit 1',
                            'hours': 80,
                            'revenue': 50000,
                            'rate': 5,
                            'amount': 2500
                        },
                        {
                            'business_unit': 'Test Unit 2',
                            'hours': 80,
                            'revenue': 50000,
                            'rate': 5,
                            'amount': 2500
                        }
                    ]
                }
                success, message = email_service.send_commission_report(
                    recipient_email=recipient,
                    recipient_name="Test User",
                    commission_data=commission_data
                )
            else:  # Summary Report
                summary_data = {
                    'period': 'Test Period',
                    'total_revenue': 100000,
                    'total_commissions': 5000,
                    'commission_rate': 5.0,
                    'employee_count': 10,
                    'additional_content': '<p>This is a test summary report.</p>'
                }
                success, message = email_service.send_summary_report(
                    recipients=[recipient],
                    summary_data=summary_data
                )
            
            if success:
                st.success(message)
            else:
                st.error(message)