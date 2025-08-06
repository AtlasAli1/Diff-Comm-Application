#!/usr/bin/env python3
"""
Simple API test script to validate endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date

API_BASE_URL = "http://localhost:8000/api/v1"


async def test_health_endpoint():
    """Test health check endpoint"""
    print("🩺 Testing health endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data['status']}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False


async def test_employee_endpoints():
    """Test employee CRUD operations"""
    print("\n👥 Testing employee endpoints...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test GET employees (empty initially)
            async with session.get(f"{API_BASE_URL}/employees") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ GET employees: {data['total']} employees found")
                else:
                    print(f"❌ GET employees failed: {response.status}")
                    return False
            
            # Test employee summary
            async with session.get(f"{API_BASE_URL}/employees/summary") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Employee summary: {data['data']['total_employees']} total")
                else:
                    print(f"❌ Employee summary failed: {response.status}")
                    return False
            
            # Test creating an employee
            test_employee = {
                "name": "John Doe",
                "employee_id": "EMP001",
                "department": "Sales",
                "hourly_rate": 25.50,
                "status": "Active",
                "commission_plan": "Efficiency Pay"
            }
            
            async with session.post(
                f"{API_BASE_URL}/employees",
                json=test_employee,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    employee_id = data['data']['id']
                    print(f"✅ Created employee: {data['data']['name']} (ID: {employee_id})")
                    
                    # Test getting the created employee
                    async with session.get(f"{API_BASE_URL}/employees/{employee_id}") as get_response:
                        if get_response.status == 200:
                            get_data = await get_response.json()
                            print(f"✅ Retrieved employee: {get_data['data']['name']}")
                        else:
                            print(f"❌ GET employee failed: {get_response.status}")
                    
                else:
                    print(f"❌ Create employee failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Employee endpoints error: {e}")
            return False


async def test_pay_period_endpoints():
    """Test pay period endpoints"""
    print("\n📅 Testing pay period endpoints...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test GET pay periods (empty initially)
            async with session.get(f"{API_BASE_URL}/pay-periods") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ GET pay periods: {data['total']} periods found")
                else:
                    print(f"❌ GET pay periods failed: {response.status}")
                    return False
            
            # Test pay period stats
            async with session.get(f"{API_BASE_URL}/pay-periods/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Pay period stats: {data['data']['total_periods']} total periods")
                else:
                    print(f"❌ Pay period stats failed: {response.status}")
                    return False
            
            # Test creating a pay period
            test_period = {
                "period_number": 1,
                "start_date": date.today().isoformat(),
                "end_date": (date.today().replace(day=14)).isoformat(),
                "pay_date": (date.today().replace(day=16)).isoformat(),
                "is_current": True
            }
            
            async with session.post(
                f"{API_BASE_URL}/pay-periods",
                json=test_period,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ Created pay period: Period {data['data']['period_number']}")
                else:
                    print(f"❌ Create pay period failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Pay period endpoints error: {e}")
            return False


async def test_business_unit_endpoints():
    """Test business unit endpoints"""
    print("\n🏢 Testing business unit endpoints...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test GET business units (empty initially)
            async with session.get(f"{API_BASE_URL}/business-units") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ GET business units: {data['total']} units found")
                else:
                    print(f"❌ GET business units failed: {response.status}")
                    return False
            
            # Test creating a business unit
            test_unit = {
                "name": "HVAC Services",
                "description": "Heating and cooling services",
                "enabled": True,
                "rates": {
                    "lead_gen_rate": 2.5,
                    "sold_by_rate": 3.0,
                    "work_done_rate": 1.5
                },
                "auto_added": False
            }
            
            async with session.post(
                f"{API_BASE_URL}/business-units",
                json=test_unit,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print(f"✅ Created business unit: {data['data']['name']}")
                else:
                    print(f"❌ Create business unit failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Business unit endpoints error: {e}")
            return False


async def main():
    """Run all API tests"""
    print("🚀 Starting API tests...\n")
    
    tests = [
        test_health_endpoint(),
        test_employee_endpoints(),
        test_pay_period_endpoints(),
        test_business_unit_endpoints()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    passed = sum(1 for result in results if result is True)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API tests passed!")
        return 0
    else:
        print("❌ Some API tests failed")
        return 1


if __name__ == "__main__":
    print("📝 Commission Calculator Pro API Test Suite")
    print("=" * 50)
    print("Make sure the API is running: python start_api.py --reload")
    print("=" * 50)
    
    exit_code = asyncio.run(main())
    exit(exit_code)