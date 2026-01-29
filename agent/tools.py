"""
Tool implementations for Care Coordinator Agent.
Each tool makes HTTP requests to the Flask API.
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

API_BASE = 'http://localhost:5000'


def get_providers_by_specialty(specialty: str) -> dict:
    """
    Find all providers with a given specialty.
    
    Args:
        specialty: Specialty name (e.g., "Orthopedics", "Primary Care", "Surgery")
    
    Returns:
        dict with list of providers and their locations
    """
    try:
        # Query providers table filtered by specialty
        sql = """
            SELECT p.id, p.first_name, p.last_name, p.certification, s.name as specialty
            FROM providers p
            JOIN specialties s ON p.specialty_id = s.id
            WHERE s.name ILIKE %s
        """
        
        response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': sql, 'params': [specialty]}
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to query providers: {response.text}"}
        
        data = response.json()
        providers = data.get('results', [])
        
        if not providers:
            return {
                "found": False,
                "message": f"No providers found with specialty '{specialty}'"
            }
        
        return {
            "found": True,
            "providers": providers,
            "count": len(providers)
        }
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}


def get_provider_locations(provider_id: int) -> dict:
    """
    Get all locations where a provider works, including hours.
    
    Args:
        provider_id: Provider ID
    
    Returns:
        dict with list of locations and their details
    """
    try:
        sql = """
            SELECT 
                d.id as department_id,
                d.name as location_name,
                d.address,
                d.phone,
                d.hours
            FROM provider_departments pd
            JOIN departments d ON pd.department_id = d.id
            WHERE pd.provider_id = %s
        """
        
        response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': sql, 'params': [provider_id]}
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to query locations: {response.text}"}
        
        data = response.json()
        locations = data.get('results', [])
        
        if not locations:
            return {
                "found": False,
                "message": f"No locations found for provider ID {provider_id}"
            }
        
        return {
            "found": True,
            "locations": locations,
            "count": len(locations)
        }
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}


def get_available_times(provider_id: int, department_id: int, start_date: str, end_date: Optional[str] = None) -> dict:
    """
    Get available appointment times for a provider at a location.
    Can check single date or date range.
    
    Args:
        provider_id: Provider ID
        department_id: Department/location ID
        start_date: Start date (YYYY-MM-DD)
        end_date: Optional end date for range (YYYY-MM-DD)
    
    Returns:
        dict with available times by date
    """
    try:
        if end_date is None:
            end_date = start_date
        
        # Get department hours
        dept_sql = "SELECT hours FROM departments WHERE id = %s"
        dept_response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': dept_sql, 'params': [department_id]}
        )
        
        if dept_response.status_code != 200:
            return {"error": "Failed to get department hours"}
        
        dept_data = dept_response.json()
        if not dept_data.get('results'):
            return {"error": f"Department {department_id} not found"}
        
        hours_str = dept_data['results'][0]['hours']
        
        # Get booked appointments in date range
        apt_sql = """
            SELECT date, appointment_time
            FROM appointments
            WHERE provider_id = %s
            AND department_id = %s
            AND date >= %s
            AND date <= %s
            AND status = 'scheduled'
        """
        
        apt_response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': apt_sql, 'params': [provider_id, department_id, start_date, end_date]}
        )
        
        if apt_response.status_code != 200:
            return {"error": "Failed to get booked appointments"}
        
        apt_data = apt_response.json()
        booked = apt_data.get('results', [])
        
        # Build dict of booked times by date
        booked_by_date = {}
        for apt in booked:
            date = apt['date']
            if date not in booked_by_date:
                booked_by_date[date] = set()
            booked_by_date[date].add(apt['appointment_time'])
        
        # For simplicity, return office hours string and booked times
        # Agent can reason about what's available
        return {
            "office_hours": hours_str,
            "date_range": f"{start_date} to {end_date}",
            "booked_times": booked_by_date,
            "message": f"Office hours: {hours_str}. Booked times provided by date."
        }
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}


def check_appointment_history(patient_id: int, provider_id: int) -> dict:
    """
    Check if patient has seen provider in last 5 years.
    Determines if next appointment should be NEW or ESTABLISHED.
    
    Args:
        patient_id: Patient ID
        provider_id: Provider ID
    
    Returns:
        dict with appointment_type and reasoning
    """
    try:
        # Calculate date 5 years ago
        five_years_ago = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
        
        sql = """
            SELECT date, status
            FROM appointments
            WHERE patient_id = %s
            AND provider_id = %s
            AND date >= %s
            AND status = 'completed'
            ORDER BY date DESC
            LIMIT 1
        """
        
        response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': sql, 'params': [patient_id, provider_id, five_years_ago]}
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to check history: {response.text}"}
        
        data = response.json()
        appointments = data.get('results', [])
        
        if appointments:
            last_visit = appointments[0]['date']
            return {
                "appointment_type": "ESTABLISHED",
                "reason": f"Patient has seen this provider before (last visit: {last_visit})",
                "last_visit": last_visit
            }
        else:
            return {
                "appointment_type": "NEW",
                "reason": "Patient has not seen this provider in the last 5 years (or ever)",
                "last_visit": None
            }
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}


def check_insurance(insurance_name: str) -> dict:
    """
    Check if insurance is accepted.
    
    Args:
        insurance_name: Insurance provider name
    
    Returns:
        dict with acceptance status
    """
    try:
        # Check if this specific insurance is accepted using ILIKE for case-insensitive match
        sql = "SELECT id, name, accepted FROM insurances WHERE name ILIKE %s"
        
        response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': sql, 'params': [f"%{insurance_name}%"]}
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to query insurances: {response.text}"}
        
        data = response.json()
        results = data.get('results', [])
        
        # Check if we found a match
        if results:
            insurance = results[0]
            if insurance['accepted']:
                return {
                    "accepted": True,
                    "matched_name": insurance['name'],
                    "message": f"Yes, {insurance['name']} is accepted"
                }
            else:
                return {
                    "accepted": False,
                    "matched_name": insurance['name'],
                    "message": f"{insurance['name']} is in our system but is not currently accepted"
                }
        
        # No match found - get list of accepted insurances
        list_sql = "SELECT name FROM insurances WHERE accepted = TRUE"
        list_response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': list_sql}
        )
        
        accepted_list = []
        if list_response.status_code == 200:
            list_data = list_response.json()
            accepted_list = [ins['name'] for ins in list_data.get('results', [])]
        
        return {
            "accepted": False,
            "message": f"'{insurance_name}' not found in our system",
            "accepted_insurances": accepted_list
        }
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}


def set_patient_insurance(patient_id: int, insurance_name: str) -> dict:
    """
    Set or update patient's insurance.
    Creates new insurance record if it doesn't exist (marked as not accepted).
    
    Args:
        patient_id: Patient ID
        insurance_name: Insurance provider name
    
    Returns:
        dict with success status and whether insurance is accepted
    """
    try:
        response = requests.post(
            f'{API_BASE}/api/set_patient_insurance',
            json={
                'patient_id': patient_id,
                'insurance_name': insurance_name
            }
        )
        
        if response.status_code != 200:
            error_data = response.json()
            return {"error": error_data.get('error', 'Failed to set insurance')}
        
        return response.json()
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}


def get_self_pay_rate(specialty: str) -> dict:
    """
    Get self-pay rate for a specialty.
    
    Args:
        specialty: Specialty name
    
    Returns:
        dict with rate information
    """
    try:
        sql = "SELECT name, self_pay_rate FROM specialties WHERE name ILIKE %s"
        
        response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': sql, 'params': [specialty]}
        )
        
        if response.status_code != 200:
            return {"error": f"Failed to query rates: {response.text}"}
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            return {
                "found": False,
                "message": f"No rate found for specialty '{specialty}'"
            }
        
        rate_info = results[0]
        return {
            "found": True,
            "specialty": rate_info['name'],
            "rate": rate_info['self_pay_rate'],
            "message": f"Self-pay rate for {rate_info['name']}: ${rate_info['self_pay_rate']}"
        }
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}


def book_appointment(patient_id: int, provider_id: int, department_id: int, 
                    appointment_type: str, date: str, appointment_time: str, 
                    notes: str = "") -> dict:
    """
    Book an appointment (final action).
    
    Args:
        patient_id: Patient ID
        provider_id: Provider ID
        department_id: Department/location ID
        appointment_type: 'NEW' or 'ESTABLISHED'
        date: Date in YYYY-MM-DD format
        appointment_time: Time in HH:MM format (24-hour)
        notes: Optional notes
    
    Returns:
        dict with booking confirmation or error
    """
    try:
        booking_data = {
            "patient_id": patient_id,
            "provider_id": provider_id,
            "department_id": department_id,
            "appointment_type": appointment_type,
            "date": date,
            "appointment_time": appointment_time,
            "notes": notes
        }
        
        response = requests.post(
            f'{API_BASE}/api/book',
            json=booking_data
        )
        
        if response.status_code != 200:
            error_data = response.json()
            return {
                "success": False,
                "error": error_data.get('error', 'Booking failed')
            }
        
        data = response.json()
        
        if data.get('success'):
            return {
                "success": True,
                "appointment_id": data['appointment_id'],
                "confirmation": data['confirmation'],
                "details": data.get('details', {})
            }
        else:
            return {
                "success": False,
                "error": data.get('error', 'Unknown error')
            }
    
    except Exception as e:
        return {"success": False, "error": f"Tool error: {str(e)}"}


def query_database(sql: str, params: List = None) -> dict:
    """
    General database query tool for flexibility.
    Only allows SELECT queries for security.
    
    Args:
        sql: SQL SELECT query
        params: Optional list of parameters for query
    
    Returns:
        dict with query results
    """
    try:
        if params is None:
            params = []
        
        response = requests.post(
            f'{API_BASE}/api/query',
            json={'sql': sql, 'params': params}
        )
        
        if response.status_code != 200:
            return {"error": f"Query failed: {response.text}"}
        
        data = response.json()
        return {
            "success": True,
            "results": data.get('results', []),
            "row_count": data.get('row_count', 0)
        }
    
    except Exception as e:
        return {"error": f"Tool error: {str(e)}"}