# 📋 VERCEL UI SPECIFICATION - Commission Calculator Pro

## 🎯 Project Overview

You are building a modern, responsive web interface for a commission calculation system that serves construction/service companies. The application manages employee commissions, tracks revenue, processes timesheets, and generates detailed reports. This UI will connect to our FastAPI backend running at `http://localhost:8000` (development) or your production API URL.

## 🏗️ Application Architecture

### Navigation Structure
The application has 5 main sections, presented as tabs in this exact order:
1. **🏠 Dashboard** - Overview and analytics
2. **⚙️ Company Setup** - Employee and commission configuration
3. **📊 Data Management** - Upload and view data
4. **🧮 Commission Calc** - Calculate commissions
5. **📈 Reports** - View and export reports

### Global State Management
The application maintains global state for:
- Current pay period selection
- Loaded employee data
- Loaded revenue data
- Loaded timesheet data
- Commission calculation results
- Business unit configurations
- Company settings

## 📑 Detailed Page Specifications

### 1. 🏠 Dashboard Page

#### Purpose
Provide a quick overview of business health, employee status, and recent activity.

#### Layout
```
┌─────────────────────────────────────────────────────────────┐
│                    Commission Calculator Pro                 │
├─────────────────────────────────────────────────────────────┤
│  Current Pay Period: [Dropdown] | Status: Active/Completed   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Total       │ │ Active      │ │ Revenue     │           │
│  │ Employees   │ │ Employees   │ │ This Period │           │
│  │    25       │ │    22       │ │  $125,430   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │          Revenue Trend (Last 6 Periods)         │        │
│  │                 [Line Chart]                     │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │         Top Performers This Period              │        │
│  │  1. John Smith      - $12,450 commission        │        │
│  │  2. Jane Doe        - $10,230 commission        │        │
│  │  3. Bob Johnson     - $9,850 commission         │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

#### Components & Logic

**1. Pay Period Selector (Global Component)**
- Dropdown populated from `GET /api/v1/pay-periods`
- Shows format: "Jan 1-14, 2024 (Bi-Weekly)"
- On change: Updates global state, refreshes all data
- Default: Current pay period from `GET /api/v1/pay-periods/current`

**2. Metric Cards**
- **Total Employees**: Count from `GET /api/v1/employees` 
- **Active Employees**: Filter where status = "Active"
- **Revenue This Period**: Sum from revenue data for current period dates

**3. Revenue Trend Chart**
- Fetch last 6 pay periods
- For each period, calculate total revenue
- Display as line chart with period labels on X-axis
- Y-axis: Revenue in dollars

**4. Top Performers**
- Only show if commission calculations exist
- Sort employees by total commission descending
- Show top 5 with name and commission amount

#### API Calls on Load
```javascript
// 1. Get current pay period
const currentPeriod = await fetch('/api/v1/pay-periods/current');

// 2. Get all employees
const employees = await fetch('/api/v1/employees');

// 3. Get pay period statistics
const stats = await fetch('/api/v1/pay-periods/stats');

// 4. Get commission summary if available
const commissions = await fetch(`/api/v1/commissions/summary?start_date=${currentPeriod.start_date}&end_date=${currentPeriod.end_date}`);
```

### 2. ⚙️ Company Setup Page

#### Purpose
Configure employees, business units, commission rates, and pay periods.

#### Sub-tabs Structure
```
Company Setup
├── 📅 Pay Periods
├── 👥 Employees  
├── 🏢 Business Units
└── 🔧 Advanced Settings
```

#### 2.1 📅 Pay Periods Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Pay Period Setup                        │
├─────────────────────────────────────────────────────────────┤
│  Schedule Configuration                                      │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Schedule Type: [Weekly|Bi-Weekly|Semi-Monthly|Monthly] ▼ │
│  │ First Period Start: [Date Picker - Jan 1, 2024]         │
│  │ Pay Delay Days: [5] (days after period ends)            │
│  │                                                          │
│  │ [Generate Year Schedule]                                 │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  Generated Pay Periods                                       │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Period          │ Start Date │ End Date  │ Pay Date    │
│  │ 1 (Current)    │ Jan 1      │ Jan 14    │ Jan 19     │
│  │ 2              │ Jan 15     │ Jan 28    │ Feb 2      │
│  │ ...            │            │           │            │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**Logic:**
- **Schedule Type**: Determines period length
  - Weekly: 7 days
  - Bi-Weekly: 14 days  
  - Semi-Monthly: 1st-15th and 16th-end
  - Monthly: Full calendar month
- **Generate Year Schedule**: POST to `/api/v1/pay-periods/generate`
  ```javascript
  const payload = {
    schedule_type: "bi-weekly",
    first_period_start: "2024-01-01",
    pay_delay_days: 5
  };
  ```
- Table shows all generated periods with current period highlighted
- Pay Date = End Date + Pay Delay Days

#### 2.2 👥 Employees Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Employee Management                       │
├─────────────────────────────────────────────────────────────┤
│  [Add Employee] [Import from CSV] [Smart Add from Timesheet]│
├─────────────────────────────────────────────────────────────┤
│  Search: [_______________] Status: [All|Active|Inactive] ▼  │
├─────────────────────────────────────────────────────────────┤
│  Name         │ Status │ Pay Type      │ Rate  │ Actions   │
│  John Smith   │ Active │ Efficiency    │ $25/hr│ [Edit][X] │
│  Jane Doe     │ Active │ Hourly + Comm │ $30/hr│ [Edit][X] │
│  Bob Helper   │ Helper │ Hourly        │ $18/hr│ [Edit][X] │
└─────────────────────────────────────────────────────────────┘
```

**Add Employee Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Add New Employee                        │
├─────────────────────────────────────────────────────────────┤
│  First Name: [_______________]  * Required                   │
│  Last Name:  [_______________]  * Required                   │
│  Status:     [Active|Inactive|Helper/Apprentice|Excluded] ▼ │
│  Pay Type:   [Efficiency Pay|Hourly + Commission] ▼         │
│  Hourly Rate: $ [___] (e.g., 25.00)                        │
│                                                              │
│  Commission Rate Overrides (Optional):                       │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Business Unit    │ Lead Gen % │ Sales % │ Work % │      │
│  │ Electrical       │ [___]      │ [___]   │ [___]  │      │
│  │ Plumbing         │ [___]      │ [___]   │ [___]  │      │
│  │ HVAC            │ [___]      │ [___]   │ [___]  │      │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  [Cancel] [Save Employee]                                    │
└─────────────────────────────────────────────────────────────┘
```

**Smart Add from Timesheet:**
```
┌─────────────────────────────────────────────────────────────┐
│                 Smart Add from Timesheet                     │
├─────────────────────────────────────────────────────────────┤
│  Found 5 new employees in timesheet data:                   │
│                                                              │
│  ☑ Mike Johnson    Status: [Active] ▼  Rate: $[25]         │
│                    Pay Type: [Efficiency Pay] ▼             │
│                                                              │
│  ☑ Sarah Williams  Status: [Active] ▼  Rate: $[25]         │
│                    Pay Type: [Efficiency Pay] ▼             │
│                                                              │
│  ☐ Tom Helper      Status: [Helper/Apprentice] ▼ Rate: $[18]│
│                    Pay Type: [Hourly] ▼                     │
│                                                              │
│  [Cancel] [Add Selected Employees]                          │
└─────────────────────────────────────────────────────────────┘
```

**Employee Status Types:**
- **Active**: Normal employee, gets commissions
- **Inactive**: Not currently working
- **Helper/Apprentice**: Gets hourly pay only, no commissions
- **Excluded from Payroll**: Tracked but not paid through system

**Pay Types:**
- **Efficiency Pay**: Employee gets MAX(hourly pay, total commissions)
- **Hourly + Commission**: Employee gets hourly pay + all commissions

**API Interactions:**
```javascript
// Get all employees
GET /api/v1/employees

// Add employee
POST /api/v1/employees
{
  "first_name": "John",
  "last_name": "Smith",
  "status": "Active",
  "pay_type": "Efficiency Pay",
  "hourly_rate": 25.00,
  "commission_overrides": {
    "Electrical": {
      "lead_gen_rate": 0.10,
      "sales_rate": 0.08,
      "work_done_rate": 0.45
    }
  }
}

// Smart add - first check timesheet for new names
POST /api/v1/upload/timesheet
// Then bulk create selected employees
POST /api/v1/employees/bulk
```

#### 2.3 🏢 Business Units Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Business Unit Setup                       │
├─────────────────────────────────────────────────────────────┤
│  [Add Business Unit] [Smart Detect from Revenue Data]       │
├─────────────────────────────────────────────────────────────┤
│  Unit Name    │ Lead Gen % │ Sales % │ Work Done % │ Action│
│  Electrical   │    10%     │   8%    │    45%      │ [Edit]│
│  Plumbing     │    10%     │   8%    │    45%      │ [Edit]│
│  HVAC         │    12%     │   10%   │    50%      │ [Edit]│
│  Maintenance  │    8%      │   6%    │    40%      │ [Edit]│
└─────────────────────────────────────────────────────────────┘
```

**Add/Edit Business Unit Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│                 Configure Business Unit                      │
├─────────────────────────────────────────────────────────────┤
│  Unit Name: [_______________] * Required                     │
│                                                              │
│  Default Commission Rates:                                   │
│  Lead Generation: [10] %  (Customer acquisition)            │
│  Sales:           [8]  %  (Closing the sale)               │
│  Work Done:       [45] %  (Performing the work)            │
│                                                              │
│  Total Work Done: 45% (will be split among techs)          │
│                                                              │
│  [Cancel] [Save Business Unit]                              │
└─────────────────────────────────────────────────────────────┘
```

**Commission Type Explanations:**
- **Lead Generation**: Commission for employee who brought in the customer
- **Sales**: Commission for employee who closed the sale
- **Work Done**: Commission split among technicians who performed the work

#### 2.4 🔧 Advanced Settings Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Advanced Settings                         │
├─────────────────────────────────────────────────────────────┤
│  Data Processing Settings                                    │
│  ┌─────────────────────────────────────────────────┐       │
│  │ ☑ Auto-detect employees from timesheets                 │
│  │ ☑ Auto-detect business units from revenue              │
│  │ ☑ Allow manual hour overrides                          │
│  │ ☑ Show detailed calculation breakdowns                 │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  Commission Calculation Settings                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Rounding: [Nearest cent|Nearest dollar] ▼              │
│  │ Minimum commission amount: $[0.00]                      │
│  │ Include weekends in calculations: [Yes|No] ▼           │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  [Save Settings]                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. 📊 Data Management Page

#### Purpose
Upload and view revenue data and timesheet data.

#### Sub-tabs Structure
```
Data Management
├── 📤 Upload Data
├── 💰 Revenue Data
└── ⏰ Timesheet Data
```

#### 3.1 📤 Upload Data Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Upload Data                             │
├─────────────────────────────────────────────────────────────┤
│  Select Data Type:                                           │
│  ○ Revenue Data    ● Timesheet Data    ○ Employee List     │
├─────────────────────────────────────────────────────────────┤
│  Upload Timesheet File                                       │
│  ┌─────────────────────────────────────────────────┐       │
│  │         📁 Drag & drop file here or              │       │
│  │                                                   │       │
│  │              [Browse Files]                       │       │
│  │                                                   │       │
│  │      Accepts: .csv, .xlsx, .xls (max 25MB)      │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  Expected Columns:                                           │
│  • Technician Name (required)                               │
│  • Date (required)                                          │
│  • Regular Hours                                            │
│  • Overtime Hours                                           │
│  • Total Hours                                              │
│                                                              │
│  [Download Template CSV]                                     │
└─────────────────────────────────────────────────────────────┘
```

**After Upload - Validation Results:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Upload Results                            │
├─────────────────────────────────────────────────────────────┤
│  ✅ File uploaded successfully!                              │
│                                                              │
│  Summary:                                                    │
│  • Records processed: 156                                    │
│  • Date range: Jan 1 - Jan 14, 2024                        │
│  • Employees found: 22                                       │
│  • New employees detected: 3 [Configure in Company Setup]   │
│                                                              │
│  ⚠️ Warnings:                                                │
│  • Row 45: Missing hours for John Smith on Jan 5           │
│  • Row 67: Invalid date format (fixed: 01/10 → 01/10/2024) │
│                                                              │
│  [View Uploaded Data] [Upload Another File]                 │
└─────────────────────────────────────────────────────────────┘
```

**Upload Process Flow:**
1. User selects file type (Revenue/Timesheet/Employee)
2. Drag & drop or browse for file
3. File validates on backend
4. Show results with any warnings/errors
5. If new employees/units found, prompt to configure

**API Calls:**
```javascript
// Upload timesheet
POST /api/v1/upload/timesheet
Content-Type: multipart/form-data
Body: file

// Upload revenue  
POST /api/v1/upload/revenue
Content-Type: multipart/form-data
Body: file

// Get template
GET /api/v1/upload/templates/timesheet
// Returns CSV file for download
```

#### 3.2 💰 Revenue Data Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Revenue Data                            │
├─────────────────────────────────────────────────────────────┤
│  Pay Period: [Current Period ▼] [Refresh] [Export CSV]      │
├─────────────────────────────────────────────────────────────┤
│  Date    │ Job # │ Customer      │ Business Unit │ Revenue  │
│  Jan 2   │ 1001  │ ABC Corp      │ Electrical    │ $5,420   │
│  Jan 2   │ 1002  │ XYZ Inc       │ Plumbing      │ $3,200   │
│  Jan 3   │ 1003  │ 123 Home      │ HVAC          │ $8,900   │
│  ...     │       │               │               │          │
├─────────────────────────────────────────────────────────────┤
│  Total Revenue: $125,430    Jobs: 45    Avg: $2,787        │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Filter by pay period
- Sort by any column
- Search/filter functionality
- Export filtered data
- Show totals and statistics

#### 3.3 ⏰ Timesheet Data Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                     Timesheet Data                           │
├─────────────────────────────────────────────────────────────┤
│  Pay Period: [Current Period ▼] Employee: [All ▼]          │
│  [Manual Hour Override] [Export CSV]                        │
├─────────────────────────────────────────────────────────────┤
│  Date    │ Employee     │ Regular │ OT   │ Total │ Status  │
│  Jan 1   │ John Smith   │ 8.0     │ 2.0  │ 10.0  │ ✓       │
│  Jan 1   │ Jane Doe     │ 8.0     │ 0.0  │ 8.0   │ ✓       │
│  Jan 2   │ John Smith   │ 7.5     │ 0.0  │ 7.5   │ Edited  │
│  ...     │              │         │      │       │         │
├─────────────────────────────────────────────────────────────┤
│  Total Hours: 880    Employees: 22    Avg/Employee: 40     │
└─────────────────────────────────────────────────────────────┘
```

**Manual Hour Override Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│                  Manual Hour Override                        │
├─────────────────────────────────────────────────────────────┤
│  Employee: [John Smith ▼]                                    │
│  Date: [Jan 2, 2024]                                        │
│                                                              │
│  Current Hours: 7.5                                          │
│  Override Hours: [8.0]                                       │
│  Reason: [Timesheet error - actually worked full day_____] │
│                                                              │
│  [Cancel] [Save Override]                                    │
└─────────────────────────────────────────────────────────────┘
```

### 4. 🧮 Commission Calc Page

#### Purpose
Calculate commissions for selected pay period and employees.

#### Layout
```
┌─────────────────────────────────────────────────────────────┐
│                  Commission Calculator                       │
├─────────────────────────────────────────────────────────────┤
│  Calculation Setup                                           │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Pay Period: [Jan 1-14, 2024 (Current) ▼]               │
│  │                                                          │
│  │ Select Employees:                                        │
│  │ ○ All Active Employees                                  │
│  │ ● Selected Employees:                                    │
│  │   ☑ John Smith      ☑ Jane Doe     ☑ Bob Johnson      │
│  │   ☑ Mike Wilson    ☐ Sarah Lee    ☑ Tom Anderson     │
│  │                                                          │
│  │ [Calculate Commissions]                                  │
│  └─────────────────────────────────────────────────┘       │
├─────────────────────────────────────────────────────────────┤
│  Calculation Progress                                        │
│  ┌─────────────────────────────────────────────────┐       │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░ 75% Complete                    │
│  │ Processing: Bob Johnson...                              │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**After Calculation - Results Preview:**
```
┌─────────────────────────────────────────────────────────────┐
│                 Commission Results Preview                   │
├─────────────────────────────────────────────────────────────┤
│  Pay Period: Jan 1-14, 2024    Status: ✅ Complete          │
├─────────────────────────────────────────────────────────────┤
│  Summary Statistics:                                         │
│  • Total Commissions: $45,670                               │
│  • Employees Processed: 18                                   │
│  • Average Commission: $2,537                               │
│  • Highest: John Smith ($5,420)                            │
├─────────────────────────────────────────────────────────────┤
│  Employee    │ Hours │ Hourly Pay │ Commission │ Total Pay  │
│  John Smith  │ 80    │ $2,000     │ $5,420     │ $5,420 *   │
│  Jane Doe    │ 75    │ $2,250     │ $1,890     │ $4,140     │
│  Bob Johnson │ 82    │ $2,050     │ $3,200     │ $3,200 *   │
│                                                              │
│  * Efficiency pay (commission > hourly)                      │
├─────────────────────────────────────────────────────────────┤
│  [View Detailed Report] [Export Results] [Recalculate]      │
└─────────────────────────────────────────────────────────────┘
```

**Calculation Process:**
1. Select pay period (defaults to current)
2. Select employees (all active or specific)
3. Click Calculate
4. Backend processes each employee:
   - Gets their hours from timesheet
   - Finds all jobs they worked on
   - Calculates commission based on role
   - Applies efficiency pay logic
5. Show results preview
6. Allow viewing detailed breakdown

**API Call:**
```javascript
POST /api/v1/commissions/calculate
{
  "pay_period_id": 1,
  "employee_ids": [1, 2, 3, 4, 5]
}
```

### 5. 📈 Reports Page

#### Purpose
View, analyze, and export detailed commission reports.

#### Sub-tabs Structure
```
Reports
├── 📊 Commission Report
├── 💰 Revenue Analysis
└── 📈 Employee Performance
```

#### 5.1 📊 Commission Report Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Commission Report                         │
├─────────────────────────────────────────────────────────────┤
│  Pay Period: [Jan 1-14, 2024 ▼] [Generate PDF] [Export CSV]│
├─────────────────────────────────────────────────────────────┤
│  Employee: John Smith         Status: Active                │
│  Pay Type: Efficiency Pay     Department: Field Tech        │
├─────────────────────────────────────────────────────────────┤
│  Earnings Breakdown                                          │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Hours Worked:        80 hrs @ $25/hr = $2,000          │
│  │ Regular Hours:       75 hrs                             │
│  │ Overtime Hours:      5 hrs (1.5x)                       │
│  │                                                          │
│  │ Commission Earned:                                       │
│  │ • Lead Generation:   $1,250 (3 leads)                   │
│  │ • Sales:            $890 (2 sales)                      │
│  │ • Work Done:        $3,280 (8 jobs)                     │
│  │ Total Commission:   $5,420                              │
│  │                                                          │
│  │ Pay Calculation:                                         │
│  │ Hourly Pay:         $2,000                              │
│  │ Commission:         $5,420                              │
│  │ Efficiency Pay:     $5,420 ✓ (commission higher)       │
│  └─────────────────────────────────────────────────┘       │
├─────────────────────────────────────────────────────────────┤
│  Commission Details                                          │
│  Date  │ Job# │ Type     │ Business Unit │ Revenue │ Comm  │
│  Jan 2 │ 1001 │ Lead Gen │ Electrical    │ $5,000  │ $500  │
│  Jan 3 │ 1002 │ Sales    │ Plumbing      │ $3,000  │ $240  │
│  Jan 4 │ 1003 │ Work     │ HVAC          │ $4,000  │ $1,800│
│  ...   │      │          │               │         │       │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Detailed breakdown showing HOW commission was calculated
- Shows efficiency pay comparison
- Lists every job and commission earned
- Printable/exportable format
- Navigate between employees

**Detailed Calculation Display Example:**
```
Work Done Commission Calculation:
Job #1003 - HVAC Installation
Total Revenue: $4,000
Commission Rate: 45%
Total Commission: $1,800
Technicians on Job: John Smith, Bob Helper
John's Share: $1,800 ÷ 1 = $1,800 (helpers don't get commission)
```

#### 5.2 💰 Revenue Analysis Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Revenue Analysis                          │
├─────────────────────────────────────────────────────────────┤
│  Date Range: [Last 6 Periods ▼] [Custom Range]             │
├─────────────────────────────────────────────────────────────┤
│         Revenue by Business Unit (Last 6 Periods)           │
│  ┌─────────────────────────────────────────────────┐       │
│  │              [Stacked Bar Chart]                 │       │
│  │  Shows each period with units stacked            │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  Business Unit Performance                                   │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Unit         │ Revenue  │ Jobs │ Avg Job │ Growth      │
│  │ Electrical   │ $45,230  │ 23   │ $1,966  │ +12%       │
│  │ Plumbing     │ $38,900  │ 31   │ $1,255  │ +8%        │
│  │ HVAC         │ $41,300  │ 15   │ $2,753  │ +22%       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

#### 5.3 📈 Employee Performance Tab

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│                  Employee Performance                        │
├─────────────────────────────────────────────────────────────┤
│  Period: [Current ▼] Dept: [All ▼] Sort: [Commission ▼]    │
├─────────────────────────────────────────────────────────────┤
│  Performance Rankings                                        │
│  ┌─────────────────────────────────────────────────┐       │
│  │ Rank │ Employee    │ Revenue Gen │ Commission │ Eff %   │
│  │ 1    │ John Smith  │ $28,450     │ $5,420     │ 19.1%   │
│  │ 2    │ Bob Johnson │ $22,100     │ $3,200     │ 14.5%   │
│  │ 3    │ Jane Doe    │ $18,900     │ $2,890     │ 15.3%   │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  Performance Trends                                          │
│  ┌─────────────────────────────────────────────────┐       │
│  │         [Line Chart - Top 5 Employees]           │       │
│  │    Shows commission trends over last 6 periods   │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 UI/UX Guidelines

### Design Principles
1. **Clean and Professional** - Business application aesthetic
2. **Data-Dense but Readable** - Show lots of info without clutter
3. **Mobile Responsive** - Should work on tablets for field use
4. **Fast Performance** - Quick loads, pagination for large datasets
5. **Clear Feedback** - Loading states, success/error messages

### Color Scheme
- **Primary**: Blue (#2563EB) - Actions, links, primary buttons
- **Success**: Green (#10B981) - Positive states, confirmations
- **Warning**: Amber (#F59E0B) - Warnings, attention needed
- **Error**: Red (#EF4444) - Errors, deletions
- **Neutral**: Grays - Text, borders, backgrounds

### Component Guidelines

**Forms:**
- Clear labels above inputs
- Required fields marked with asterisk
- Inline validation with helpful error messages
- Disabled submit until valid
- Loading state during submission

**Tables:**
- Sortable columns (click header)
- Pagination for >25 rows
- Search/filter box
- Hover states on rows
- Action buttons on right

**Modals:**
- Overlay with semi-transparent backdrop
- X close button in top right
- Cancel/Save buttons at bottom
- Escape key to close

**Navigation:**
- Persistent tab bar
- Active tab highlighted
- Breadcrumbs for sub-navigation
- Current pay period always visible

## 🔄 State Management

### Global State Structure
```javascript
{
  // Current context
  currentPayPeriod: {
    id: 1,
    start_date: "2024-01-01",
    end_date: "2024-01-14",
    pay_date: "2024-01-19",
    status: "Active"
  },
  
  // Loaded data
  employees: [...],
  businessUnits: [...],
  timesheetData: [...],
  revenueData: [...],
  
  // Calculation results
  commissionResults: {
    payPeriodId: 1,
    calculations: [...],
    summary: {...}
  },
  
  // UI State
  loading: {
    employees: false,
    calculations: false,
    // etc
  },
  
  // Settings
  companySettings: {
    autoDetectEmployees: true,
    autoDetectUnits: true,
    // etc
  }
}
```

### Data Flow
1. **On App Load:**
   - Fetch current pay period
   - Load employees and business units
   - Check for existing calculations

2. **On Pay Period Change:**
   - Update global state
   - Reload relevant data (revenue, timesheet)
   - Clear calculation results

3. **On Data Upload:**
   - Upload file to backend
   - Reload affected data
   - Show new employee/unit notifications

4. **On Calculate:**
   - Show loading state
   - Call calculation endpoint
   - Store results in state
   - Navigate to results

## 🔌 API Integration Details

### Base Configuration
```javascript
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// Axios instance with interceptors
const api = axios.create({
  baseURL: `${API_BASE}${API_VERSION}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token when available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Error Handling
```javascript
// Global error handler
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 422) {
      // Validation error - show field errors
      const errors = error.response.data.detail;
      // Display errors next to form fields
    } else if (error.response?.status === 404) {
      // Not found
      showNotification('Resource not found', 'error');
    } else {
      // Generic error
      showNotification('An error occurred', 'error');
    }
    return Promise.reject(error);
  }
);
```

### File Upload Example
```javascript
const uploadTimesheet = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post('/upload/timesheet', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(progress);
      },
    });
    
    return response.data;
  } catch (error) {
    // Handle error
  }
};
```

## 🚀 Implementation Priority

### Phase 1 - Core Functionality
1. Dashboard with basic metrics
2. Employee management (CRUD)
3. Business unit setup
4. Data upload (timesheet & revenue)
5. Basic commission calculation
6. Simple commission report

### Phase 2 - Enhanced Features  
1. Pay period management
2. Smart employee/unit detection
3. Manual hour overrides
4. Detailed calculation display
5. Revenue analysis charts
6. Employee performance metrics

### Phase 3 - Polish & Optimization
1. Advanced filtering/search
2. Bulk operations
3. Export functionality (PDF/CSV)
4. Mobile responsive design
5. Real-time notifications
6. Performance optimizations

## 📝 Testing Checklist

### Functional Tests
- [ ] Can create/edit/delete employees
- [ ] Can upload timesheet and revenue files
- [ ] Can calculate commissions for a pay period
- [ ] Efficiency pay calculates correctly
- [ ] Multi-tech jobs split commission properly
- [ ] Hour overrides work correctly
- [ ] Reports show accurate data

### Edge Cases
- [ ] Helper/Apprentice employees don't get commission
- [ ] Excluded employees are filtered out
- [ ] Invalid file uploads show clear errors
- [ ] Missing data handled gracefully
- [ ] Large datasets perform acceptably
- [ ] Pay period boundaries respected

### User Experience
- [ ] All loading states present
- [ ] Error messages are helpful
- [ ] Success feedback is clear
- [ ] Navigation is intuitive
- [ ] Forms validate properly
- [ ] Tables are sortable/filterable

## 🎯 Success Criteria

The UI is successful when:
1. Users can complete a full payroll cycle without confusion
2. Commission calculations match manual calculations exactly
3. Reports clearly show how each employee is paid
4. Data upload accepts common file formats without errors
5. The system handles 100+ employees smoothly
6. New users can navigate without training

## 🔧 Technical Recommendations

### Frontend Framework
- **React** with TypeScript for type safety
- **Next.js** for SSR and optimal performance
- **TailwindCSS** for styling
- **React Query** for API state management
- **React Hook Form** for form handling
- **Recharts** for data visualization

### Development Tools
- **Storybook** for component development
- **Jest** + **React Testing Library** for tests
- **MSW** for API mocking
- **Playwright** for E2E tests

### Performance Optimizations
- Virtualize long lists (employee tables)
- Lazy load chart libraries
- Implement pagination on backend
- Cache API responses appropriately
- Use optimistic updates for better UX

This specification provides everything needed to build a professional, full-featured commission calculator UI. The backend API is ready and waiting at the documented endpoints!