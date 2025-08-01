# Commission Calculator Pro 💰

A comprehensive, enterprise-grade commission management system built with Streamlit. This enhanced version provides advanced features for managing employee commissions, tracking performance, and generating detailed reports.

## 🌟 Features

### Core Functionality
- **Multi-file Data Import**: Upload timesheet and revenue data from Excel/CSV files
- **Advanced Validation**: Comprehensive data validation with error reporting
- **Real-time Calculations**: Dynamic commission calculations with live updates
- **Flexible Rate Management**: Individual hourly rates and commission percentages
- **Manual Commission Splits**: Distribute commissions across multiple employees

### Data Management
- **SQLite Database**: Persistent data storage with automatic backups  
- **Import/Export**: Multiple formats including Excel, CSV, and JSON
- **Data Templates**: Pre-built templates for easy data entry
- **Version Control**: Track changes with comprehensive audit trails

### Analytics & Reporting
- **Interactive Dashboards**: Real-time analytics with Plotly visualizations
- **Performance Metrics**: KPIs, efficiency tracking, and trend analysis
- **Custom Reports**: Flexible report builder with multiple export formats
- **Executive Summaries**: High-level overviews for management
- **Payroll Integration**: Generate payroll-ready export files

### Security & Administration
- **User Authentication**: Role-based access control (Admin, Manager, Editor, Viewer)
- **Audit Logging**: Complete activity tracking and compliance reporting
- **Data Backup**: Automated backup system with restore capabilities
- **System Monitoring**: Performance metrics and health monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download the project**:
   ```bash
   cd commission_calculator_pro
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python run.py
   ```
   
   Or directly with Streamlit:
   ```bash
   streamlit run app.py
   ```

4. **Access the application**:
   Open your web browser and go to `http://localhost:8501`

5. **First-time setup**:
   - Default admin credentials: `admin` / `admin123`
   - Change the default password immediately after first login

## 📁 Project Structure

```
commission_calculator_pro/
├── app.py                      # Main application entry point
├── run.py                      # Launch script
├── requirements.txt            # Python dependencies
├── models/                     # Data models and business logic
│   ├── __init__.py
│   ├── employee.py            # Employee data model
│   ├── business_unit.py       # Business unit and commission models
│   └── calculator.py          # Main calculation engine
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── database.py           # Database management
│   ├── auth.py               # Authentication system
│   ├── export.py             # Export functionality
│   └── validators.py         # Data validation
├── pages/                    # Streamlit pages
│   ├── __init__.py
│   ├── data_management.py    # Data upload and editing
│   ├── system_configuration.py # Rate and settings management
│   ├── analytics_dashboard.py # Analytics and visualizations
│   ├── commission_reports.py  # Report generation
│   └── advanced_settings.py  # Admin tools and manual splits
├── data/                     # Data storage (created at runtime)
├── backups/                  # Database backups (created at runtime)
└── tests/                    # Unit tests (optional)
```

## 📖 User Guide

### 1. Data Management
- **Upload Files**: Import timesheet and revenue data from Excel/CSV
- **Data Validation**: Automatic validation with error reporting
- **Edit Data**: Modify employee hours and business unit revenue
- **Templates**: Download sample templates for proper formatting

### 2. System Configuration
- **Hourly Rates**: Set individual employee hourly rates
- **Commission Rates**: Configure commission percentages by business unit
- **Period Settings**: Define commission calculation periods
- **Advanced Settings**: Labor multipliers, rounding rules, and system preferences

### 3. Analytics Dashboard
- **Overview**: Key performance indicators and summary metrics
- **Revenue Analysis**: Detailed revenue breakdowns and trends
- **Employee Analysis**: Performance tracking and utilization metrics
- **Forecasting**: Simple trend analysis and projections

### 4. Commission Reports
- **Executive Summary**: High-level business overview
- **Employee Reports**: Detailed individual performance reports
- **Business Unit Reports**: Unit-level analysis and profitability
- **Payroll Export**: Generate payroll-ready files
- **Custom Reports**: Build tailored reports with specific criteria

### 5. Advanced Settings (Admin Only)
- **Manual Splits**: Create custom commission distributions
- **User Management**: Add/remove users and manage permissions
- **Audit Trail**: Review system activity and changes
- **System Administration**: Backup management and system health

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_PATH=commission_data.db
BACKUP_DIR=backups

# Security Settings
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT=3600

# Application Settings
MAX_UPLOAD_SIZE=10MB
AUTO_BACKUP=True
BACKUP_FREQUENCY=daily
```

### User Roles

| Role    | Permissions |
|---------|-------------|
| Viewer  | View reports and dashboards only |
| Editor  | View + edit data and configurations |
| Manager | Editor + access to advanced analytics |
| Admin   | Full system access including user management |

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit with custom CSS and JavaScript
- **Backend**: Python with Pydantic data models
- **Database**: SQLite with SQLAlchemy ORM
- **Visualization**: Plotly for interactive charts
- **Authentication**: bcrypt password hashing
- **Logging**: Loguru for comprehensive logging

### Data Models
- **Employee**: Personal info, rates, hours, and metadata
- **BusinessUnit**: Revenue, commission rates, and categories
- **Commission**: Individual commission records with approval workflow
- **CommissionSplit**: Manual distribution rules for complex scenarios

### Database Schema
The system uses SQLite with the following main tables:
- `employees`: Employee master data
- `employee_hours`: Historical hours tracking
- `business_units`: Business unit information
- `revenue`: Revenue tracking by period
- `commissions`: Commission calculations
- `commission_splits`: Manual split configurations
- `audit_log`: System activity tracking
- `users`: User accounts and authentication
- `configuration`: System settings

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v --cov=.
```

## 📊 Performance

### Capacity
- **Employees**: 1,000+ employees
- **Business Units**: 500+ units
- **Commission Records**: 10,000+ records
- **Concurrent Users**: 10+ users

### Response Times
- **Dashboard Load**: < 2 seconds
- **Report Generation**: < 5 seconds
- **Data Import**: < 10 seconds for 1,000 records

## 🔒 Security

### Data Protection
- **Encryption**: Passwords hashed with bcrypt
- **Session Management**: Secure session handling
- **Audit Trail**: Complete activity logging
- **Backup Security**: Encrypted backup files

### Best Practices
- Change default admin password immediately
- Use strong passwords for all accounts
- Regular backup verification
- Monitor audit logs for suspicious activity
- Keep the application updated

## 🤝 Support

### Common Issues

**Q: Import fails with "Missing columns" error**
A: Ensure your Excel/CSV file has the required columns: Employee Name, Regular Hours, OT Hours, DT Hours for timesheets.

**Q: Commissions calculate to zero**
A: Check that both hourly rates (employees) and commission rates (business units) are configured.

**Q: Can't access admin features**
A: Ensure you're logged in with an Admin or Manager role account.

### Getting Help
1. Check the application logs for error details
2. Review the audit trail for system activity
3. Verify data formats match the provided templates
4. Ensure all required configurations are complete

## 📈 Roadmap

### Planned Features
- **API Integration**: REST API for external systems
- **Advanced Forecasting**: Machine learning predictions
- **Mobile App**: Companion mobile application
- **Multi-company**: Support for multiple organizations
- **Custom Workflows**: Configurable approval processes

### Version History
- **v2.0**: Enhanced UI, advanced analytics, user management
- **v1.0**: Basic commission calculation with Excel import/export

## 📝 License

This project is proprietary software. All rights reserved.

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Web application framework
- [Plotly](https://plotly.com/) - Interactive visualizations
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM

---

**Commission Calculator Pro** - Transforming commission management with advanced analytics and enterprise-grade features. 💰✨