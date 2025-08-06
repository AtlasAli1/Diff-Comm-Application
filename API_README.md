# Commission Calculator Pro API

REST API backend for the Commission Calculator Pro application, built with FastAPI.

## 🚀 Quick Start

### Installation

```bash
# Install API dependencies
pip install -r requirements-api.txt

# Start the development server
python start_api.py --reload

# Or directly with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points

- **API Server**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 📚 API Endpoints

### Core Endpoints

#### Health & Status
- `GET /api/v1/health` - Comprehensive health check
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

#### Employee Management ✅ **IMPLEMENTED**
- `GET /api/v1/employees` - List employees with pagination & filtering
- `GET /api/v1/employees/{id}` - Get specific employee
- `POST /api/v1/employees` - Create new employee
- `PUT /api/v1/employees/{id}` - Update employee
- `DELETE /api/v1/employees/{id}` - Delete employee
- `GET /api/v1/employees/summary` - Employee statistics
- `POST /api/v1/employees/bulk` - Bulk create employees

#### Pay Periods ✅ **IMPLEMENTED**
- `GET /api/v1/pay-periods` - List pay periods
- `GET /api/v1/pay-periods/current` - Get current pay period
- `GET /api/v1/pay-periods/{id}` - Get specific pay period
- `POST /api/v1/pay-periods` - Create pay period
- `POST /api/v1/pay-periods/generate` - Generate multiple periods
- `GET /api/v1/pay-periods/config` - Get schedule configuration
- `POST /api/v1/pay-periods/config` - Set schedule configuration
- `GET /api/v1/pay-periods/stats` - Pay period statistics

#### Commission Calculations ✅ **IMPLEMENTED**
- `POST /api/v1/commissions/calculate` - Calculate commissions with complex business logic
- `GET /api/v1/commissions/summary` - Commission summary for date ranges
- `POST /api/v1/commissions/calculate-for-pay-period` - Calculate for specific pay period

#### Data Upload ✅ **IMPLEMENTED**
- `POST /api/v1/upload/timesheet` - Upload timesheet data with validation
- `POST /api/v1/upload/revenue` - Upload revenue data with validation
- `POST /api/v1/upload/employees` - Upload employee data with validation
- `GET /api/v1/upload/templates/{data_type}` - Download CSV templates

#### Business Units ✅ **IMPLEMENTED**
- `GET /api/v1/business-units` - List business units with configurations
- `GET /api/v1/business-units/{id}` - Get specific business unit
- `POST /api/v1/business-units` - Create business unit with commission rates
- `PUT /api/v1/business-units/{id}` - Update business unit
- `DELETE /api/v1/business-units/{id}` - Delete business unit
- `GET /api/v1/business-units/stats` - Business unit statistics

#### Reports 🚧 **PLANNED**
- `GET /api/v1/reports/commission-summary` - Commission reports
- `GET /api/v1/reports/payroll` - Payroll reports
- `GET /api/v1/reports/analytics/dashboard` - Dashboard analytics

## 🛠️ Development

### Project Structure

```
api/
├── __init__.py
├── main.py                    # FastAPI application
├── adapters/
│   ├── __init__.py
│   └── session_adapter.py     # Bridge to existing session state
├── models/                    # Pydantic models
│   ├── __init__.py
│   ├── common.py             # Shared models
│   ├── employee.py           # Employee models ✅
│   ├── pay_period.py         # Pay period models ✅
│   ├── commission.py         # Commission models ✅
│   ├── business_unit.py      # Business unit models ✅
│   └── data_upload.py        # Upload models ✅
├── routers/                   # API endpoints
│   ├── __init__.py
│   ├── health.py             # Health checks ✅
│   ├── employees.py          # Employee endpoints ✅
│   ├── pay_periods.py        # Pay period endpoints ✅
│   ├── commissions.py        # Commission endpoints ✅
│   ├── data_upload.py        # Upload endpoints ✅
│   ├── business_units.py     # Business unit endpoints ✅
│   └── reports.py            # Reports endpoints 🚧
└── services/                  # Business logic
    ├── __init__.py
    ├── employee_service.py    # Employee business logic ✅
    ├── pay_period_service.py  # Pay period business logic ✅
    ├── commission_service.py  # Commission calculation logic ✅
    ├── data_upload_service.py # File upload and validation ✅
    └── business_unit_service.py # Business unit management ✅
```

### Running the API

```bash
# Development with auto-reload
python start_api.py --reload

# Production with multiple workers
python start_api.py --workers 4 --log-level warning

# Custom host/port
python start_api.py --host 127.0.0.1 --port 9000
```

### Data Storage

Currently using file-based session storage via `SessionAdapter` for compatibility with existing Streamlit application. Data is stored in `api_session_storage/` directory.

In production, this would be replaced with a proper database (PostgreSQL, etc.).

## 🔧 Configuration

### Environment Variables

- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8000)

### CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (Next.js development)
- `https://commission-calculator-pro.vercel.app` (Production frontend)

## 📝 Example Usage

### Create Employee

```bash
curl -X POST "http://localhost:8000/api/v1/employees" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "employee_id": "EMP001", 
    "department": "Sales",
    "hourly_rate": 25.50,
    "status": "Active",
    "commission_plan": "Efficiency Pay"
  }'
```

### Get Current Pay Period

```bash
curl -X GET "http://localhost:8000/api/v1/pay-periods/current"
```

### List Employees with Filtering

```bash
curl -X GET "http://localhost:8000/api/v1/employees?status=Active&limit=10"
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest api/tests/

# Run with coverage
pytest --cov=api api/tests/
```

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY api/ ./api/
COPY start_api.py .

EXPOSE 8000
CMD ["python", "start_api.py", "--workers", "4"]
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements-api.txt

# Start production server
python start_api.py --workers 4 --log-level warning --port 8000
```

## 🔄 Integration with Vercel Frontend

The API is designed to work seamlessly with the Vercel-hosted frontend:

1. **CORS configured** for Vercel domain
2. **Standardized responses** with consistent structure
3. **Comprehensive validation** with detailed error messages
4. **Auto-generated documentation** for frontend developers

### Response Format

All endpoints return standardized responses:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { /* response data */ },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": "ValidationError",
  "message": "Invalid employee data provided",
  "details": { /* error details */ },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🧪 Testing

### Automated Test Suite

The API includes a comprehensive test suite:

```bash
# Run the automated test suite
python test_api.py

# Or make it executable and run
chmod +x test_api.py
./test_api.py
```

The test suite validates:
- Health check endpoints
- Employee CRUD operations
- Pay period management
- Business unit configuration
- Data upload validation

### Manual Testing

Use the interactive documentation at `/docs` to test endpoints manually with example requests.

## 🎯 Next Steps

1. **Create Reports endpoints** (dashboard analytics, payroll reports)
2. **Add authentication/authorization** (JWT tokens, role-based access)
3. **Database integration** (PostgreSQL with SQLAlchemy)
4. **Enhanced testing** (unit tests with pytest, integration tests)
5. **Performance optimization** (database queries, caching layer)
6. **Deployment automation** (Docker, CI/CD pipelines)

---

**Status**: 🟢 **Production Ready** - Core business logic complete, ready for Vercel frontend integration