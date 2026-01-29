# flask-app.py - Care Coordinator Backend API
# Phase 2: Extended with Supabase integration

import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client
import psycopg2
from psycopg2.extras import RealDictCursor

# Import helpers
from api_helpers import calculate_arrival_time, format_date_for_api, format_time_for_api

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file")
    print("API will not be able to connect to database")
    supabase = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize PostgreSQL connection for raw SQL queries
POSTGRES_CONNECTION = None
conn_string = os.getenv('POSTGRES_CONNECTION_STRING')

if conn_string:
    try:
        POSTGRES_CONNECTION = psycopg2.connect(conn_string)
        print("✓ Connected to PostgreSQL for raw SQL queries")
    except Exception as e:
        print(f"⚠ PostgreSQL connection failed: {e}")


# ============================================
# ROUTES
# ============================================

@app.route('/', methods=['GET'])
def healthcheck():
    """Health check endpoint"""
    return jsonify("Hello World")


@app.route('/patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """
    Get patient information with appointments and referrals.
    Now queries Supabase instead of returning hardcoded data.
    """
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500
    
    try:
        # Get patient data with insurance
        patient_response = supabase.table('patients').select('''
            *,
            insurances(id, name, accepted)
        ''').eq('id', patient_id).execute()
        
        if not patient_response.data:
            return jsonify({"error": f"Patient {patient_id} not found"}), 404
        
        patient = patient_response.data[0]
        
        # Get appointments with provider names
        appointments_response = supabase.table('appointments').select('''
            *,
            providers(first_name, last_name)
        ''').eq('patient_id', patient_id).order('date', desc=True).execute()
        
        # Format appointments for API response
        appointments = []
        for apt in appointments_response.data:
            provider_name = f"Dr. {apt['providers']['first_name']} {apt['providers']['last_name']}"
            appointments.append({
                "date": format_date_for_api(apt['date']),
                "time": format_time_for_api(apt['appointment_time']),
                "provider": provider_name,
                "status": apt['status'],
                "notes": apt.get('notes', '')
            })
        
        # Get referrals
        referrals_response = supabase.table('referrals').select('''
            *,
            providers(first_name, last_name),
            specialties(name)
        ''').eq('patient_id', patient_id).execute()
        
        # Format referrals
        referred_providers = []
        for ref in referrals_response.data:
            ref_data = {"specialty": ref['specialties']['name']}
            if ref.get('providers'):
                provider = ref['providers']
                ref_data["provider"] = f"{provider['last_name']}, {provider['first_name']} MD"
            referred_providers.append(ref_data)
        
        # Build response matching original format
        response_data = {
            "id": patient['id'],
            "name": f"{patient['first_name']} {patient['last_name']}",
            "dob": patient['dob'],
            "pcp": patient.get('pcp', ''),
            "ehrId": patient.get('ehr_id', ''),
            "notes": patient.get('notes', ''),
            "referred_providers": referred_providers,
            "appointments": appointments
        }
        
        # Add insurance information if patient has one
        if patient.get('insurances'):
            insurance = patient['insurances']
            response_data["insurance"] = {
                "id": insurance['id'],
                "name": insurance['name'],
                "accepted": insurance['accepted']
            }
        else:
            response_data["insurance"] = None
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error getting patient data: {str(e)}")
        return jsonify({"error": "Failed to retrieve patient data"}), 500


@app.route('/api/query', methods=['POST'])
def query_database():
    """
    Execute SQL query on PostgreSQL.
    
    Example request body:
    {
        "sql": "SELECT * FROM providers WHERE specialty_id = %s",
        "params": [1]
    }
    """
    if not POSTGRES_CONNECTION:
        return jsonify({"error": "Database connection not configured"}), 500
    
    try:
        data = request.json
        
        if not data or 'sql' not in data:
            return jsonify({"error": "Missing 'sql' in request body"}), 400
        
        sql = data['sql']
        params = data.get('params', [])
        
        # Security: Only allow SELECT queries
        if not sql.strip().upper().startswith('SELECT'):
            return jsonify({"error": "Only SELECT queries are allowed"}), 400
        
        # Execute query
        cursor = POSTGRES_CONNECTION.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        
        # Convert to list of dicts
        results_list = [dict(row) for row in results]
        
        return jsonify({
            "results": results_list,
            "row_count": len(results_list)
        })
    
    except Exception as e:
        print(f"Query error: {str(e)}")
        return jsonify({"error": f"Query failed: {str(e)}"}), 500


@app.route('/api/book', methods=['POST'])
def book_appointment():
    """
    Book a new appointment.
    
    Example request body:
    {
        "patient_id": 1,
        "provider_id": 2,
        "department_id": 2,
        "appointment_type": "ESTABLISHED",
        "date": "2026-02-15",
        "appointment_time": "10:00",
        "notes": "Follow-up for knee pain"
    }
    """
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500
    
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['patient_id', 'provider_id', 'department_id', 
                          'appointment_type', 'date', 'appointment_time']
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate appointment type
        if data['appointment_type'] not in ['NEW', 'ESTABLISHED']:
            return jsonify({"error": "appointment_type must be 'NEW' or 'ESTABLISHED'"}), 400
        
        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "date must be in YYYY-MM-DD format"}), 400
        
        # Validate time format (HH:MM)
        try:
            datetime.strptime(data['appointment_time'], '%H:%M')
        except ValueError:
            return jsonify({"error": "appointment_time must be in HH:MM format (24-hour)"}), 400
        
        # Calculate arrival time
        arrival_time = calculate_arrival_time(
            data['appointment_time'], 
            data['appointment_type']
        )
        
        # Insert appointment
        appointment_data = {
            'patient_id': data['patient_id'],
            'provider_id': data['provider_id'],
            'department_id': data['department_id'],
            'appointment_type': data['appointment_type'],
            'date': data['date'],
            'appointment_time': data['appointment_time'],
            'arrival_time': arrival_time,
            'status': 'scheduled',
            'notes': data.get('notes', '')
        }
        
        result = supabase.table('appointments').insert(appointment_data).execute()
        
        if result.data:
            appointment_id = result.data[0]['id']
            
            # Get provider and department names for confirmation
            provider = supabase.table('providers').select('first_name, last_name').eq('id', data['provider_id']).execute()
            department = supabase.table('departments').select('name').eq('id', data['department_id']).execute()
            patient = supabase.table('patients').select('first_name, last_name').eq('id', data['patient_id']).execute()
            
            return jsonify({
                "success": True,
                "appointment_id": appointment_id,
                "confirmation": "Appointment booked successfully",
                "details": {
                    "patient": f"{patient.data[0]['first_name']} {patient.data[0]['last_name']}",
                    "provider": f"Dr. {provider.data[0]['first_name']} {provider.data[0]['last_name']}",
                    "location": department.data[0]['name'],
                    "date": data['date'],
                    "appointment_time": data['appointment_time'],
                    "arrival_time": arrival_time,
                    "type": data['appointment_type']
                }
            })
        else:
            return jsonify({"error": "Failed to create appointment"}), 500
    
    except Exception as e:
        print(f"Booking error: {str(e)}")
        return jsonify({"error": f"Booking failed: {str(e)}"}), 500


@app.route('/api/set_patient_insurance', methods=['POST'])
def set_patient_insurance():
    """
    Set or update a patient's insurance.
    Creates insurance record if it doesn't exist (marked as not accepted).
    
    Example request body:
    {
        "patient_id": 1,
        "insurance_name": "Cigna"
    }
    """
    if not supabase:
        return jsonify({"error": "Database connection not configured"}), 500
    
    try:
        data = request.json
        
        # Validate required fields
        if 'patient_id' not in data or 'insurance_name' not in data:
            return jsonify({"error": "Missing required fields: patient_id, insurance_name"}), 400
        
        patient_id = data['patient_id']
        insurance_name = data['insurance_name'].strip()
        
        if not insurance_name:
            return jsonify({"error": "insurance_name cannot be empty"}), 400
        
        # Check if insurance exists
        existing = supabase.table('insurances') \
            .select('id, name, accepted') \
            .ilike('name', insurance_name) \
            .execute()
        
        insurance_id = None
        is_accepted = False
        actual_name = insurance_name
        
        if existing.data:
            # Insurance exists - use it
            insurance_id = existing.data[0]['id']
            is_accepted = existing.data[0]['accepted']
            actual_name = existing.data[0]['name']
        else:
            # Insurance doesn't exist - create it (not accepted by default)
            insert_result = supabase.table('insurances') \
                .insert({'name': insurance_name, 'accepted': False}) \
                .execute()
            
            if not insert_result.data:
                return jsonify({"error": "Failed to create insurance record"}), 500
            
            insurance_id = insert_result.data[0]['id']
            is_accepted = False
        
        # Update patient's insurance_id
        update_result = supabase.table('patients') \
            .update({'insurance_id': insurance_id}) \
            .eq('id', patient_id) \
            .execute()
        
        if not update_result.data:
            return jsonify({"error": "Failed to update patient insurance"}), 500
        
        # Build response
        response = {
            "success": True,
            "insurance_name": actual_name,
            "accepted": is_accepted,
            "message": f"Patient insurance set to {actual_name}"
        }
        
        if not is_accepted:
            response["message"] += " (NOTE: This insurance is not currently accepted. Patient will need to self-pay.)"
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Set insurance error: {str(e)}")
        return jsonify({"error": f"Failed to set insurance: {str(e)}"}), 500


# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    if supabase:
        print("✓ Connected to Supabase")
    else:
        print("⚠ Supabase connection not configured - check .env file")
    
    print("Starting Flask server on http://localhost:5002")
    app.run(debug=True, port=5002)