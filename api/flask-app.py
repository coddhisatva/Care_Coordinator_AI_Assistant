# flask-app.py - Care Coordinator Backend API
# Phase 2: Extended with Supabase integration

import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor

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
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize PostgreSQL connection for raw SQL queries
POSTGRES_CONNECTION = None
if SUPABASE_URL:
    # Extract Postgres connection details from Supabase URL
    # Format: https://xxxxx.supabase.co
    project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
    
    try:
        POSTGRES_CONNECTION = psycopg2.connect(
            host=f"db.{project_ref}.supabase.co",
            database="postgres",
            user="postgres",
            password=os.getenv('SUPABASE_DB_PASSWORD'),  # Need to add this to .env
            port=5432
        )
        print("✓ Connected to PostgreSQL for raw SQL queries")
    except Exception as e:
        print(f"⚠ PostgreSQL connection failed: {e}")


# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_arrival_time(appointment_time: str, appointment_type: str) -> str:
    """
    Calculate arrival time based on appointment type.
    NEW: 30 min early, ESTABLISHED: 10 min early
    """
    try:
        time_obj = datetime.strptime(appointment_time, '%H:%M')
        minutes_early = 30 if appointment_type == 'NEW' else 10
        arrival = time_obj - timedelta(minutes=minutes_early)
        return arrival.strftime('%H:%M')
    except ValueError:
        # Fallback if time format is wrong
        return appointment_time


def format_date_for_api(iso_date: str) -> str:
    """Convert ISO date (2024-08-12) to API format (8/12/24)"""
    try:
        date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
        return date_obj.strftime('%-m/%d/%y')  # %-m removes leading zero
    except ValueError:
        return iso_date


def format_time_for_api(time_24hr: str) -> str:
    """Convert 24hr time (14:30) to 12hr format (2:30pm)"""
    try:
        time_obj = datetime.strptime(time_24hr, '%H:%M')
        return time_obj.strftime('%-I:%M%p').lower()  # 2:30pm
    except ValueError:
        return time_24hr


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
        # Get patient data
        patient_response = supabase.table('patients').select('*').eq('id', patient_id).execute()
        
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


# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    if supabase:
        print("✓ Connected to Supabase")
    else:
        print("⚠ Supabase connection not configured - check .env file")
    
    print("Starting Flask server on http://localhost:5000")
    app.run(debug=True)