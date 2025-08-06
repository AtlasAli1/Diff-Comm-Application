# Commission Calculator Pro 💰✨

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-Proprietary-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Web%20%2B%20API-purple.svg)

**A powerful, enterprise-grade commission management system with dual web interface and REST API backend**

[Features](#-features) • [Quick Start](#-quick-start) • [API Documentation](#-api-documentation) • [Architecture](#-architecture) • [Support](#-support)

</div>

---

## 🎯 Overview

**Commission Calculator Pro** is a comprehensive commission management platform featuring both an interactive Streamlit web interface and a production-ready REST API backend. It streamlines complex commission calculations with automated pay periods, multi-technician job handling, and sophisticated business logic.

### 🔥 What Makes It Special?

- **🏗️ Dual Architecture** - Web interface for users + REST API for integrations
- **🧮 Complex Business Logic** - Lead gen, sales, and work done commissions with efficiency pay
- **📅 Automated Pay Periods** - Generate entire year schedules with multiple frequencies
- **👥 Smart Employee Management** - Bulk operations, status tracking, and rate overrides
- **📊 Advanced Analytics** - Real-time dashboards with interactive visualizations
- **🔄 Scalable Design** - From 8,800-line monolith to clean modular architecture
- **🧪 Production Ready** - Comprehensive testing, health monitoring, and deployment tools

## 🌟 Features

### 💰 Commission Engine
- **Three Commission Types**:
  - **Lead Generation** - Commission for generating leads
  - **Sales** - Commission for closing sales  
  - **Work Done** - Commission split among assigned technicians
- **Efficiency Pay Model** - Max of hourly pay vs commission (incentivizes performance)
- **Employee Rate Overrides** - Custom commission rates per employee per business unit
- **Multi-technician Support** - Automatically split work commissions among multiple techs

### 📅 Pay Period Management  
- **Multiple Schedules** - Weekly, Bi-weekly, Semi-monthly, Monthly
- **Automated Generation** - Create entire year of pay periods from configuration
- **Current Period Detection** - Automatically identify active pay period
- **Pay Date Calculation** - Configurable delay between period end and pay date

### 👥 Employee Management
- **Full CRUD Operations** - Create, read, update, delete with validation
- **Status Tracking** - Active, Inactive, Helper/Apprentice, Excluded from Payroll
- **Bulk Import** - CSV/Excel employee data with validation and error reporting
- **Smart Auto-Add** - Automatically detect employees from timesheet data
- **Commission Plans** - Hourly + Commission or Efficiency Pay models

### 📊 Business Intelligence
- **Interactive Dashboard** - KPIs, trends, and performance metrics
- **Revenue Analytics** - Business unit performance with visual charts
- **Employee Insights** - Individual performance tracking and summaries
- **Real-time Calculations** - Live commission previews and adjustments

### 📤 Data Processing
- **Multi-format Support** - CSV, Excel (.xlsx, .xls) with intelligent parsing
- **Advanced Validation** - Comprehensive error checking with detailed reporting
- **Template System** - Download standardized CSV templates
- **Batch Processing** - Optimized handling of large datasets (5,000+ records)

## 🚀 Quick Start

### Web Interface (Streamlit)

```bash
# Clone the repository
git clone https://github.com/AtlasAli1/Diff-Comm-Application.git
cd Diff-Comm-Application

# Install dependencies
pip install -r requirements.txt

# Start the web application  
streamlit run app_modular.py

# Access at http://localhost:8501
```

### REST API Backend

```bash
# Install API dependencies
pip install -r requirements-api.txt

# Start the API server
python start_api.py --reload

# Access API at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### Run Tests

```bash
# Test the API endpoints
python test_api.py

# Test commission calculations
python test_commission_calculator.py

# Display implementation summary
python api_summary.py
```

## 🔗 API Documentation

### Core Endpoints

#### Employee Management
- `GET /api/v1/employees` - List employees with filtering & pagination
- `POST /api/v1/employees` - Create new employee  
- `PUT /api/v1/employees/{id}` - Update employee
- `DELETE /api/v1/employees/{id}` - Delete employee
- `GET /api/v1/employees/summary` - Employee statistics
- `POST /api/v1/employees/bulk` - Bulk create employees

#### Commission Calculations
- `POST /api/v1/commissions/calculate` - Calculate commissions with complex business logic
- `GET /api/v1/commissions/summary` - Commission summary for date ranges
- `POST /api/v1/commissions/calculate-for-pay-period` - Calculate for specific pay period

#### Pay Period Management
- `GET /api/v1/pay-periods` - List pay periods
- `GET /api/v1/pay-periods/current` - Get current active pay period
- `POST /api/v1/pay-periods/generate` - Generate pay periods from schedule
- `GET /api/v1/pay-periods/stats` - Pay period statistics

#### Data Upload
- `POST /api/v1/upload/timesheet` - Upload timesheet data with validation
- `POST /api/v1/upload/revenue` - Upload revenue data with validation
- `POST /api/v1/upload/employees` - Bulk employee import
- `GET /api/v1/upload/templates/{type}` - Download CSV templates

#### Business Unit Configuration
- `GET /api/v1/business-units` - List business units with commission rates
- `POST /api/v1/business-units` - Create business unit with rates
- `PUT /api/v1/business-units/{id}` - Update business unit
- `DELETE /api/v1/business-units/{id}` - Delete business unit

**📚 Complete API documentation:** See [API_README.md](API_README.md)

## 🏗️ Architecture

### Dual Interface Design
```
┌─────────────────────────────────────────────────────────┐
│                Commission Calculator Pro                │
├─────────────────────────────────────────────────────────┤
│  🌐 Streamlit Web App     │    🔗 FastAPI Backend      │
│  ├─ Interactive UI        │    ├─ REST endpoints (32)   │
│  ├─ Dashboard & Reports   │    ├─ Business logic        │
│  ├─ Data management       │    ├─ Data validation       │
│  └─ Configuration         │    └─ Auto-documentation    │
├─────────────────────────────────────────────────────────┤
│                 📊 Shared Business Logic                │
│  ├─ Commission calculations with efficiency pay model   │
│  ├─ Pay period management with automated scheduling     │
│  ├─ Employee management with status & rate tracking     │
│  ├─ Business unit configuration with custom rates       │
│  └─ Data processing with validation & error handling    │
└─────────────────────────────────────────────────────────┘
```

### Modular Structure
```
commission_calculator_pro/
├── 🌐 Web Interface (Streamlit)
│   ├── app_modular.py           # Main Streamlit application  
│   └── ui/                      # Modular UI components
│       ├── dashboard.py         # Analytics dashboard
│       ├── company_setup.py     # Employee & config management
│       ├── data_management.py   # Data upload & management
│       ├── commission_calc.py   # Commission calculations
│       ├── reports.py           # Reports & analytics
│       └── utils.py             # Shared utilities
│
├── 🔗 REST API Backend
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   ├── models/              # Pydantic data models (5 modules)
│   │   ├── routers/             # API endpoints (7 routers)
│   │   ├── services/            # Business logic services (6 services)
│   │   └── adapters/            # Data layer integration
│   ├── start_api.py             # API startup script
│   └── test_api.py              # Automated test suite
│
├── 📊 Legacy & Support
│   ├── working_main_app.py      # Original monolithic app (archived)
│   ├── models/                  # Data models
│   ├── services/                # Business services
│   └── utils/                   # Utility functions
│
└── 📋 Documentation & Config
    ├── API_README.md            # Detailed API documentation
    ├── requirements-api.txt     # API dependencies
    ├── requirements.txt         # Web app dependencies
    └── *.py                     # Test & utility scripts
```

## 💼 Business Logic

### Commission Calculation Types
1. **Lead Generation** - Commission on revenue for leads generated by employee
2. **Sales** - Commission on revenue for sales closed by employee
3. **Work Done** - Commission on revenue split among technicians who performed work

### Pay Models
- **Hourly + Commission** - Employee receives hourly pay plus all commission
- **Efficiency Pay** - Employee receives the higher of hourly pay or commission total

### Advanced Features
- **Rate Overrides** - Set custom commission rates per employee per business unit
- **Multi-technician Jobs** - Automatically split work commissions among assigned technicians
- **Hour Overrides** - Manual timesheet adjustments with tracking and timestamps
- **Smart Detection** - Automatically identify employees and business units from uploaded data

## 🧪 Testing & Quality

### Automated Testing
- **32 API Endpoint Tests** - Comprehensive validation of all endpoints
- **Business Logic Tests** - Commission calculation accuracy verification
- **Data Validation Tests** - File upload and processing validation
- **Health Monitoring** - System performance and status checks

### Quality Assurance
- **Input Validation** - Pydantic models with comprehensive error handling
- **Error Reporting** - Detailed error messages with actionable guidance
- **Performance Monitoring** - System metrics (CPU, memory, disk usage)
- **Security Features** - File validation, size limits, content scanning

## 📈 Performance & Scalability

### Optimizations
- **Caching Layer** - TTL-based caching for expensive operations (up to 88% memory reduction)
- **Batch Processing** - Efficient handling of large datasets (5,000+ records)
- **Memory Optimization** - DataFrame memory usage optimization
- **Async Processing** - Non-blocking API operations with FastAPI

### Scalability Features
- **Service Layer Architecture** - Clean separation of concerns
- **Modular Design** - Easy to extend and maintain
- **Configuration Management** - Adaptive settings based on data size
- **Health Monitoring** - Production-ready observability

## 🚀 Deployment

### Development
```bash
# Web interface
streamlit run app_modular.py

# API backend  
python start_api.py --reload
```

### Production
```bash
# API with multiple workers
python start_api.py --workers 4 --log-level warning

# Docker deployment available
docker build -t commission-calculator-pro .
docker run -p 8000:8000 commission-calculator-pro
```

### Health Checks
- `GET /api/v1/health` - Comprehensive system health
- `GET /api/v1/health/ready` - Kubernetes readiness probe
- `GET /api/v1/health/live` - Kubernetes liveness probe

## 🔒 Security

- **Input Validation** - Comprehensive Pydantic model validation
- **File Upload Security** - Size limits (25MB), type validation, content scanning  
- **Error Handling** - Secure error messages without information leakage
- **Session Management** - Secure session state with automatic cleanup
- **CORS Configuration** - Configured for safe cross-origin requests

## 🎉 Recent Major Updates

### v2.0.0 - Complete API Implementation ✨
- ✅ **32 REST API endpoints** covering all business operations
- ✅ **Modular Streamlit interface** with 7 focused UI modules  
- ✅ **Complex commission calculations** with efficiency pay model
- ✅ **Automated pay period management** with multiple scheduling options
- ✅ **Advanced file upload system** with validation and error reporting
- ✅ **Business unit configuration** with custom commission rates
- ✅ **Employee management** with status tracking and bulk operations
- ✅ **Dashboard analytics** with interactive charts and KPIs
- ✅ **Comprehensive testing** with automated test suite
- ✅ **Production-ready deployment** with health monitoring

### Architecture Transformation 🏗️
- 🔄 **Migrated from 8,800-line monolith** to clean modular architecture
- 🚀 **Added FastAPI backend** for scalable integrations and automation
- 📊 **Enhanced dashboard** with better space utilization and business metrics
- 🔍 **Fixed revenue column detection** for dynamic data handling
- ⚡ **Performance optimizations** for large datasets with caching
- 🧪 **Added comprehensive testing** for reliability and maintainability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python test_api.py`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📞 Support

For questions, issues, or feature requests:

1. **Check Documentation**
   - [API Documentation](API_README.md) - Complete REST API reference
   - [Implementation Summary](api_summary.py) - Run for detailed capabilities overview

2. **Run Diagnostics**
   - `python test_api.py` - Test all API endpoints
   - `python api_summary.py` - Display implementation status
   - Check health endpoint: `GET /api/v1/health`

3. **Get Help**
   - Review comprehensive error logging in the application
   - Check the automated test suite for examples
   - Open an issue with detailed steps to reproduce

## 📄 License

This project is proprietary software. All rights reserved.

---

<div align="center">

**🚀 Ready for production use and frontend team integration!**

Built with ❤️ using Python, Streamlit, and FastAPI

</div>