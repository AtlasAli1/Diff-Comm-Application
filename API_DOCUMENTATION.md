# 📡 Commission Calculator Pro - API Documentation

## Overview
The Commission Calculator Pro provides a REST API for external integrations, allowing third-party systems to interact with commission data programmatically.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_api.txt
```

### 2. Start API Server
```bash
python api_server.py
```

### 3. API Base URL
```
http://127.0.0.1:8504
```

### 4. Interactive Documentation
- **Swagger UI**: http://127.0.0.1:8504/docs
- **ReDoc**: http://127.0.0.1:8504/redoc

## 🔐 Authentication

All API endpoints require authentication using Bearer tokens.

**Header Format:**
```
Authorization: Bearer api_your_token_here
```

**Note**: For demo purposes, any token starting with `api_` is accepted. In production, implement proper JWT or API key authentication.

## 📚 API Endpoints

### System Endpoints

#### GET `/`
Get API status and version information.

**Response:**
```json
{
  "message": "Commission Calculator Pro API",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2025-08-02T10:30:00"
}
```

#### GET `/health`
Health check endpoint for monitoring.

### Employee Management

#### GET `/api/employees`
Get all employees.

**Response:**
```json
[
  {
    "employee_id": "EMP001",
    "name": "John Doe",
    "department": "Sales",
    "role": "Sales Rep",
    "hourly_rate": 25.0,
    "commission_rate": 5.0,
    "start_date": "2025-01-01",
    "status": "Active"
  }
]
```

#### POST `/api/employees`
Create a new employee.

**Request Body:**
```json
{
  "employee_id": "EMP002",
  "name": "Jane Smith",
  "department": "Sales",
  "role": "Senior Sales Rep",
  "hourly_rate": 30.0,
  "start_date": "2025-02-01",
  "status": "Active"
}
```

#### PUT `/api/employees/{employee_id}`
Update an existing employee.

#### DELETE `/api/employees/{employee_id}`
Delete an employee.

### Timesheet Management

#### GET `/api/timesheet`
Get all timesheet entries.

#### POST `/api/timesheet/bulk`
Bulk upload timesheet entries.

**Request Body:**
```json
[
  {
    "employee_name": "John Doe",
    "regular_hours": 40.0,
    "ot_hours": 5.0,
    "dt_hours": 0.0,
    "date": "2025-08-01"
  },
  {
    "employee_name": "Jane Smith",
    "regular_hours": 38.0,
    "ot_hours": 10.0,
    "dt_hours": 2.0,
    "date": "2025-08-01"
  }
]
```

### Revenue Management

#### GET `/api/revenue`
Get all revenue entries.

#### POST `/api/revenue/bulk`
Bulk upload revenue entries.

**Request Body:**
```json
[
  {
    "business_unit": "East Coast",
    "revenue": 150000.0,
    "period": "Q1 2025",
    "date": "2025-03-31"
  }
]
```

### Lead Management

#### GET `/api/leads`
Get all leads.

#### POST `/api/leads`
Create a new lead.

**Request Body:**
```json
{
  "employee_name": "John Doe",
  "lead_value": 50000.0,
  "commission_rate": 3.0,
  "status": "Closed Won",
  "date": "2025-08-01",
  "description": "Large enterprise client"
}
```

### Commission Calculations

#### POST `/api/commissions/calculate`
Calculate revenue-based commissions for all employees.

**Request Body:**
```json
{
  "start_date": "2025-08-01",
  "end_date": "2025-08-31",
  "business_units": ["East Coast", "West Coast"]
}
```

**Response:**
```json
[
  {
    "employee": "John Doe",
    "lead_gen_commission": 5000.00,
    "sales_commission": 0.00,
    "work_done_commission": 0.00,
    "total_commission": 5000.00,
    "details": {
      "hours": 45.0,
      "hourly_rate": 25.0,
      "commission_rate": 5.0,
      "closed_leads": 1,
      "lead_value": 50000.0
    }
  }
]
```

#### GET `/api/commissions/summary`
Get commission summary for date range.

**Parameters:**
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD

**Example:**
```
GET /api/commissions/summary?start_date=2025-08-01&end_date=2025-08-31
```

**Response:**
```json
{
  "period": "2025-08-01 to 2025-08-31",
  "total_employees": 25,
  "total_hours": 4500.0,
  "total_leads": 12,
  "total_lead_value": 500000.0,
  "generated_at": "2025-08-02T10:30:00"
}
```

## 💻 Usage Examples

### Python Client Example

```python
import requests
import json

# Configuration
API_BASE = "http://127.0.0.1:8504"
TOKEN = "api_your_token_here"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Create an employee
employee_data = {
    "employee_id": "EMP003",
    "name": "Bob Johnson",
    "department": "Sales",
    "role": "Sales Manager",
    "hourly_rate": 35.0,
    "commission_rate": 10.0,
    "start_date": "2025-01-15",
    "status": "Active"
}

response = requests.post(
    f"{API_BASE}/api/employees",
    headers=HEADERS,
    json=employee_data
)

if response.status_code == 200:
    print("Employee created successfully!")
else:
    print(f"Error: {response.status_code} - {response.text}")

# Calculate commissions
calc_request = {
    "start_date": "2025-08-01",
    "end_date": "2025-08-31",
    "business_units": ["East Coast", "West Coast"]
}

response = requests.post(
    f"{API_BASE}/api/commissions/calculate",
    headers=HEADERS,
    json=calc_request
)

commissions = response.json()
print(f"Commission results: {json.dumps(commissions, indent=2)}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_BASE = 'http://127.0.0.1:8504';
const TOKEN = 'api_your_token_here';
const headers = { 'Authorization': `Bearer ${TOKEN}` };

// Upload timesheet data
const timesheetData = [
  {
    employee_name: 'Bob Johnson',
    regular_hours: 40.0,
    ot_hours: 8.0,
    dt_hours: 0.0,
    date: '2025-08-01'
  }
];

axios.post(`${API_BASE}/api/timesheet/bulk`, timesheetData, { headers })
  .then(response => {
    console.log('Timesheet uploaded:', response.data);
  })
  .catch(error => {
    console.error('Error:', error.response.data);
  });
```

### cURL Examples

```bash
# Get all employees
curl -X GET "http://127.0.0.1:8504/api/employees" \
  -H "Authorization: Bearer api_your_token_here"

# Create a lead
curl -X POST "http://127.0.0.1:8504/api/leads" \
  -H "Authorization: Bearer api_your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "Bob Johnson",
    "lead_value": 75000.0,
    "commission_rate": 4.0,
    "status": "Closed Won",
    "date": "2025-08-02",
    "description": "New corporate client"
  }'

# Calculate commissions
curl -X POST "http://127.0.0.1:8504/api/commissions/calculate" \
  -H "Authorization: Bearer api_your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-08-01",
    "end_date": "2025-08-31",
    "business_units": ["East Coast", "West Coast"]
  }'
```

## 🔧 Integration Patterns

### 1. **CRM Integration**
Sync lead data from your CRM system to automatically calculate lead-based commissions.

### 2. **HR System Integration**
Import employee data and timesheet information from HR/payroll systems.

### 3. **Accounting System Integration**
Export commission calculations to accounting software for payroll processing.

### 4. **Dashboard Integration**
Build custom dashboards by consuming API data in real-time.

### 5. **Mobile App Integration**
Create mobile apps for managers to view commission data on-the-go.

## 📈 Rate Limiting & Performance

- **Rate Limiting**: Not implemented in demo version (add in production)
- **Pagination**: Large datasets should implement pagination
- **Caching**: API responses are not cached (consider Redis for production)
- **Concurrent Requests**: FastAPI handles concurrent requests efficiently

## 🛡️ Security Considerations

### Production Deployment Checklist:
- [ ] Implement proper JWT authentication
- [ ] Add rate limiting
- [ ] Use HTTPS only
- [ ] Validate and sanitize all inputs
- [ ] Add request logging and monitoring
- [ ] Configure CORS properly
- [ ] Use environment variables for sensitive config
- [ ] Implement role-based access control

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_api.txt .
RUN pip install -r requirements_api.txt

COPY api_server.py .
COPY api_data/ ./api_data/

EXPOSE 8504
CMD ["python", "api_server.py"]
```

### Production Server
```bash
# Install dependencies
pip install -r requirements_api.txt

# Run with Gunicorn for production
pip install gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8504
```

## 📞 Support

For API support and integration assistance:
- Review interactive documentation at `/docs`
- Check error responses for detailed messages
- Monitor server logs for debugging
- Test endpoints with the provided examples

---

**API Version**: 1.0.0  
**Last Updated**: August 2, 2025  
**Compatibility**: Commission Calculator Pro v2.0+