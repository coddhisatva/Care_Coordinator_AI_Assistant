"""
Test script for Care Coordinator API (Phase 2)
Run this to verify all endpoints are working correctly.

Usage:
    python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def print_test_header(test_name):
    """Print formatted test header"""
    print("\n" + "="*60)
    print(f"TEST: {test_name}")
    print("="*60)

def print_success(message):
    """Print success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ {message}")

def test_healthcheck():
    """Test 1: Health check endpoint"""
    print_test_header("Health Check (GET /)")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        
        if response.status_code == 200:
            print_success("Server is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    except requests.ConnectionError:
        print_error("Could not connect to server. Is it running?")
        print("Run: python flask-app.py")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_get_patient():
    """Test 2: Get patient data"""
    print_test_header("Get Patient (GET /patient/1)")
    
    try:
        response = requests.get(f"{BASE_URL}/patient/1")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify expected fields
            required_fields = ['id', 'name', 'dob', 'pcp', 'ehrId', 'appointments', 'referred_providers']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print_error(f"Missing fields: {missing_fields}")
                return False
            
            print_success("Patient data retrieved")
            print(f"Patient: {data['name']}")
            print(f"Appointments: {len(data['appointments'])}")
            print(f"Referrals: {len(data['referred_providers'])}")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_query_database():
    """Test 3: Execute SQL query"""
    print_test_header("Query Database (POST /api/query)")
    
    try:
        # Test query: Get all specialties
        payload = {
            "sql": "SELECT * FROM specialties"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/query",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'results' not in data or 'row_count' not in data:
                print_error("Response missing 'results' or 'row_count'")
                return False
            
            print_success("Query executed successfully")
            print(f"Rows returned: {data['row_count']}")
            
            # Show first result
            if data['results']:
                print(f"Sample result: {data['results'][0]}")
            
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_book_appointment():
    """Test 4: Book an appointment"""
    print_test_header("Book Appointment (POST /api/book)")
    
    try:
        # Test booking
        payload = {
            "patient_id": 1,
            "provider_id": 2,
            "department_id": 2,
            "appointment_type": "ESTABLISHED",
            "date": "2026-03-20",
            "appointment_time": "14:00",
            "notes": "Test appointment from API test script"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/book",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get('success'):
                print_error("Booking failed")
                print(f"Response: {data}")
                return False
            
            print_success("Appointment booked successfully")
            print(f"Appointment ID: {data['appointment_id']}")
            
            if 'details' in data:
                details = data['details']
                print(f"Patient: {details.get('patient')}")
                print(f"Provider: {details.get('provider')}")
                print(f"Location: {details.get('location')}")
                print(f"Date: {details.get('date')} at {details.get('appointment_time')}")
                print(f"Arrival time: {details.get('arrival_time')}")
            
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CARE COORDINATOR API - PHASE 2 TESTS")
    print("="*60)
    print("\nMake sure flask-app.py is running before running tests!")
    print("(In another terminal: python flask-app.py)\n")
    
    results = {
        "Health Check": test_healthcheck(),
        "Get Patient": test_get_patient(),
        "Query Database": test_query_database(),
        "Book Appointment": test_book_appointment()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED! Phase 2 complete.")
        print("Next: Phase 3 - AI Agent & Tools")
    else:
        print("\n⚠ Some tests failed. Fix issues before proceeding to Phase 3.")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)