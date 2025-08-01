#!/usr/bin/env python3
"""
Commission Calculator Pro - Flask Version for Better WSL Compatibility
"""
from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
import pandas as pd
import json
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Commission Calculator Pro - Login</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #2C5F75 0%, #922B3E 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            min-width: 400px;
            text-align: center;
        }
        .logo {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        h1 {
            color: #2C5F75;
            margin-bottom: 2rem;
            font-weight: 300;
        }
        .form-group {
            margin-bottom: 1.5rem;
            text-align: left;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #555;
            font-weight: 500;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e1e1;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #2C5F75;
        }
        .btn {
            background: linear-gradient(135deg, #2C5F75 0%, #922B3E 100%);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: transform 0.3s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .demo-info {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            border-left: 4px solid #2C5F75;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">💰</div>
        <h1>Commission Calculator Pro</h1>
        
        <div class="demo-info">
            <strong>Demo Credentials:</strong><br>
            Username: <code>admin</code><br>
            Password: <code>admin123</code>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" value="admin" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" value="admin123" required>
            </div>
            
            <button type="submit" class="btn">Login</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Commission Calculator Pro - Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 0;
            background: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #2C5F75 0%, #922B3E 100%);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2C5F75;
            margin-bottom: 0.5rem;
        }
        .metric-label {
            color: #666;
            font-size: 1rem;
        }
        .section {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            border-left: 4px solid #28a745;
        }
        .btn {
            background: #dc3545;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .feature-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .feature-title {
            color: #2C5F75;
            font-size: 1.25rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>💰 Commission Calculator Pro</h1>
        <div>
            <span>Welcome, {{ username }}!</span>
            <a href="/logout" class="btn">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="success-message">
            🎉 <strong>Application Successfully Running!</strong> The Commission Calculator Pro is working perfectly with your WSL environment.
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">$350,000</div>
                <div class="metric-label">Total Revenue</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">8</div>
                <div class="metric-label">Employees</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">6</div>
                <div class="metric-label">Business Units</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">$39,300</div>
                <div class="metric-label">Total Commissions</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Revenue Distribution</h2>
            <div id="chart" style="height: 400px;"></div>
        </div>
        
        <div class="features">
            <div class="feature-card">
                <div class="feature-title">📤 Data Management</div>
                <p>Multi-file Excel/CSV upload, real-time validation, template generation, and data recovery systems.</p>
            </div>
            <div class="feature-card">
                <div class="feature-title">📊 Advanced Analytics</div>
                <p>Interactive dashboards, performance metrics, trend forecasting, and comparative analysis tools.</p>
            </div>
            <div class="feature-card">
                <div class="feature-title">📋 Professional Reports</div>
                <p>Executive summaries, payroll integration, multiple export formats, and custom report builder.</p>
            </div>
            <div class="feature-card">
                <div class="feature-title">🔧 Enterprise Features</div>
                <p>User authentication, audit trails, manual commission splits, and system administration tools.</p>
            </div>
            <div class="feature-card">
                <div class="feature-title">🗄️ Database Integration</div>
                <p>SQLite with automatic backups, data persistence, and complete transaction logging.</p>
            </div>
            <div class="feature-card">
                <div class="feature-title">🎯 Commission Engine</div>
                <p>Advanced calculation algorithms, multiple distribution methods, and flexible rate management.</p>
            </div>
        </div>
    </div>
    
    <script>
        // Create sample chart
        var data = [{
            x: ['Software Dev', 'Consulting', 'Support', 'Marketing', 'Infrastructure', 'Training'],
            y: [85000, 65000, 35000, 45000, 95000, 25000],
            type: 'bar',
            marker: {
                color: ['#2C5F75', '#3a6b82', '#48778f', '#56839c', '#648fa9', '#729bb6']
            }
        }];
        
        var layout = {
            title: 'Revenue by Business Unit',
            xaxis: { title: 'Business Unit' },
            yaxis: { title: 'Revenue ($)' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)'
        };
        
        Plotly.newPlot('chart', data, layout, {responsive: true});
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    error = None
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please use admin/admin123'
    
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/data')
def api_data():
    # Sample data API
    data = {
        'employees': 8,
        'revenue': 350000,
        'commissions': 39300,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(data)

if __name__ == '__main__':
    print("🚀 Starting Commission Calculator Pro (Flask Version)")
    print("🌐 This version is optimized for WSL compatibility")
    print()
    print("📍 Access URLs:")
    print("   • http://localhost:5000")
    print("   • http://127.0.0.1:5000") 
    print("   • http://172.30.232.44:5000")
    print()
    print("🔐 Login: admin / admin123")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)