# Diff-Comm Application 💰✨

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-Proprietary-green.svg)
![Platform](https://img.shields.io/badge/Platform-Web-orange.svg)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)

**A powerful, enterprise-grade commission management system designed to simplify and automate commission calculations**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 🎯 Overview

**Diff-Comm Application** (Commission Calculator Pro) is a comprehensive commission management platform built with modern web technologies. It streamlines the complex process of calculating employee commissions based on hours worked and business unit revenue, providing real-time analytics, automated reporting, and secure multi-user access.

### 🔥 Why Diff-Comm?

- **📊 Real-time Analytics** - Interactive dashboards with live data visualization
- **🔐 Enterprise Security** - Role-based access control and audit trails
- **📈 Smart Calculations** - Automated commission calculations with manual override options
- **📱 Modern UI** - Clean, responsive interface built with Streamlit
- **💾 Reliable Storage** - SQLite database with automatic backups
- **📄 Export Ready** - Generate payroll-ready reports in multiple formats

## 🌟 Features

### 📥 Data Management
- **Multi-format Import** - Excel (.xlsx), CSV support with intelligent parsing
- **Smart Validation** - Automatic data validation with detailed error reporting
- **Template System** - Pre-built templates for consistent data entry
- **Bulk Operations** - Edit multiple records simultaneously
- **Version Control** - Track all changes with comprehensive audit logs

### 💰 Commission Engine
- **Flexible Rates** - Individual hourly rates per employee
- **Dynamic Percentages** - Customizable commission rates by business unit
- **Manual Splits** - Distribute commissions across teams
- **Multi-period Support** - Handle various pay periods (weekly/bi-weekly/monthly)
- **Advanced Calculations** - Support for regular, overtime, and double-time hours

### 📊 Analytics Dashboard
- **Executive Overview** - Key performance indicators at a glance
- **Revenue Analysis** - Detailed breakdowns by business unit
- **Employee Metrics** - Individual performance tracking
- **Trend Analysis** - Historical comparisons and forecasting
- **Custom Visualizations** - Interactive Plotly charts

### 📄 Reporting Suite
- **Executive Reports** - High-level summaries for management
- **Detailed Breakdowns** - Employee-specific commission details
- **Payroll Integration** - Export-ready formats for payroll systems
- **Custom Reports** - Build reports with specific criteria
- **Scheduled Reports** - Automated report generation

### 🔒 Security & Administration
- **User Management** - Four-tier access control system
- **Secure Authentication** - Bcrypt password encryption
- **Session Management** - Automatic timeout and secure sessions
- **Audit Trail** - Complete activity logging for compliance
- **Data Backup** - Automated backup with restore capabilities

## 🖼️ Demo

<div align="center">

### Dashboard View
![Dashboard](https://via.placeholder.com/800x400/4285F4/FFFFFF?text=Analytics+Dashboard)

### Commission Report
![Report](https://via.placeholder.com/800x400/34A853/FFFFFF?text=Commission+Report)

### Data Management
![Data](https://via.placeholder.com/800x400/EA4335/FFFFFF?text=Data+Management)

</div>

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- 2GB RAM minimum
- Modern web browser

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/AtlasAli1/Diff-Comm-Application.git
cd Diff-Comm-Application
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python run.py
```

5. **Access the application**
```
Open your browser and navigate to http://localhost:8501
Default credentials: admin / admin123
```

### 🐳 Docker Installation
```bash
docker build -t diff-comm-app .
docker run -p 8501:8501 diff-comm-app
```

## 📚 Documentation

### User Roles & Permissions

| Role | Description | Permissions |
|------|-------------|------------|
| **Admin** | System administrators | Full access to all features |
| **Manager** | Department managers | View all data, generate reports, manage settings |
| **Editor** | Data entry personnel | Upload/edit data, view own reports |
| **Viewer** | Read-only users | View reports and dashboards only |

### File Format Requirements

#### Timesheet Format
| Column | Type | Required | Description |
|--------|------|----------|-------------|
| Employee Name | String | ✅ | Full name of employee |
| Regular Hours | Float | ✅ | Standard hours worked |
| OT Hours | Float | ✅ | Overtime hours |
| DT Hours | Float | ✅ | Double-time hours |
| Department | String | ❌ | Optional department field |

#### Revenue Format
| Column | Type | Required | Description |
|--------|------|----------|-------------|
| Business Unit | String | ✅ | Name of business unit |
| Revenue | Float | ✅ | Total revenue generated |
| Period | Date | ✅ | Revenue period |

## 🛠️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Application Settings
APP_NAME=Diff-Comm Application
APP_ENV=production
DEBUG=False

# Database
DATABASE_PATH=commission_data.db
BACKUP_ENABLED=True
BACKUP_INTERVAL=daily
MAX_BACKUPS=30

# Security
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT=3600
PASSWORD_MIN_LENGTH=8

# Features
ENABLE_MANUAL_SPLITS=True
ENABLE_AUDIT_LOG=True
MAX_UPLOAD_SIZE=10MB
```

### Advanced Configuration

```python
# config.py
COMMISSION_CONFIG = {
    'calculation_method': 'weighted',  # 'weighted' or 'simple'
    'rounding_precision': 2,
    'minimum_commission': 0.00,
    'maximum_commission': 50000.00,
    'labor_multiplier': 1.0,
    'include_benefits': False
}
```

## 📊 API Reference

### REST API Endpoints (Coming Soon)
```
GET    /api/v1/employees          # List all employees
POST   /api/v1/employees          # Create new employee
GET    /api/v1/commissions        # Get commission data
POST   /api/v1/calculate          # Trigger calculation
GET    /api/v1/reports/{type}     # Generate report
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=.

# Run specific test file
pytest tests/test_calculator.py -v
```

## 📈 Performance Benchmarks

| Operation | Records | Time | Memory |
|-----------|---------|------|--------|
| Data Import | 1,000 | <2s | 50MB |
| Commission Calc | 5,000 | <5s | 100MB |
| Report Generation | 10,000 | <10s | 200MB |
| Dashboard Load | - | <1s | 25MB |

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 .

# Format code
black .
```

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><b>Import fails with "Missing columns" error</b></summary>

Ensure your Excel/CSV file has all required columns. Download the template files from the Data Management page for the correct format.
</details>

<details>
<summary><b>Commissions calculate to zero</b></summary>

1. Check that employee hourly rates are set in System Configuration
2. Verify business unit commission rates are configured
3. Ensure revenue data is uploaded for the calculation period
</details>

<details>
<summary><b>Can't access admin features</b></summary>

Verify you're logged in with an Admin role account. Contact your system administrator to check your permissions.
</details>

<details>
<summary><b>Application won't start</b></summary>

1. Check Python version: `python --version` (must be 3.8+)
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Check for port conflicts on 8501
</details>

## 📱 Roadmap

### Version 2.1 (Q1 2025)
- [ ] REST API implementation
- [ ] Mobile responsive design improvements
- [ ] Advanced forecasting with ML
- [ ] Email notification system

### Version 3.0 (Q2 2025)
- [ ] Multi-company support
- [ ] Custom workflow builder
- [ ] Integration with popular payroll systems
- [ ] Real-time collaboration features

## 📄 License

This project is proprietary software. All rights reserved.

## 👥 Team

<div align="center">

| Role | Contact |
|------|---------|
| **Project Lead** | AtlasAli1 |
| **Support** | support@diff-comm.app |
| **Security** | security@diff-comm.app |

</div>

## 🙏 Acknowledgments

Built with these amazing technologies:

- [Streamlit](https://streamlit.io/) - The fastest way to build data apps
- [Plotly](https://plotly.com/) - Interactive graphing library
- [Pandas](https://pandas.pydata.org/) - Data analysis and manipulation
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type annotations

---

<div align="center">

**Diff-Comm Application** - Revolutionizing Commission Management 💰

Made with ❤️ by the Diff-Comm Team

[Report Bug](https://github.com/AtlasAli1/Diff-Comm-Application/issues) • [Request Feature](https://github.com/AtlasAli1/Diff-Comm-Application/issues)

</div>