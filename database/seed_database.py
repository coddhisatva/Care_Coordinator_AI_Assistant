"""
Seed Supabase database with hospital data.

This script:
1. Connects to Supabase
2. Parses data_sheet.txt
3. Populates all tables with data
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from parse_data_sheet import parse_data_sheet

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def seed_specialties(parsed_data: dict) -> dict:
    """Insert specialties with rates. Returns {name: id} mapping."""
    print("Seeding specialties...")
    
    specialty_map = {}
    
    for specialty_name in parsed_data['specialties']:
        rate = parsed_data['specialty_rates'].get(specialty_name, 0)
        
        if rate == 0:
            print(f"  WARNING: No rate found for {specialty_name}, defaulting to 0")
        
        result = supabase.table('specialties').insert({
            'name': specialty_name,
            'self_pay_rate': rate
        }).execute()
        
        specialty_id = result.data[0]['id']
        specialty_map[specialty_name] = specialty_id
        print(f"  ✓ {specialty_name} (${rate}) - ID: {specialty_id}")
    
    return specialty_map


def seed_providers(parsed_data: dict, specialty_map: dict) -> dict:
    """Insert providers. Returns {index: id} mapping."""
    print("\nSeeding providers...")
    
    provider_map = {}
    
    for idx, provider in enumerate(parsed_data['providers'], start=1):
        specialty_id = specialty_map.get(provider['specialty'])
        
        if not specialty_id:
            print(f"  ERROR: Specialty '{provider['specialty']}' not found for {provider['first_name']} {provider['last_name']}")
            continue
        
        result = supabase.table('providers').insert({
            'first_name': provider['first_name'],
            'last_name': provider['last_name'],
            'certification': provider['certification'],
            'specialty_id': specialty_id
        }).execute()
        
        provider_id = result.data[0]['id']
        provider_map[idx] = provider_id
        print(f"  ✓ Dr. {provider['first_name']} {provider['last_name']} ({provider['specialty']}) - ID: {provider_id}")
    
    return provider_map


def seed_departments(parsed_data: dict) -> dict:
    """Insert departments. Returns {index: id} mapping."""
    print("\nSeeding departments...")
    
    dept_map = {}
    
    for idx, dept in enumerate(parsed_data['departments'], start=1):
        result = supabase.table('departments').insert({
            'name': dept['name'],
            'phone': dept['phone'],
            'address': dept['address'],
            'hours': dept['hours']
        }).execute()
        
        dept_id = result.data[0]['id']
        dept_map[idx] = dept_id
        print(f"  ✓ {dept['name']} ({dept['hours']}) - ID: {dept_id}")
    
    return dept_map


def seed_provider_departments(parsed_data: dict, provider_map: dict, dept_map: dict):
    """Insert provider-department mappings."""
    print("\nSeeding provider-department mappings...")
    
    for provider_idx, dept_idx in parsed_data['provider_dept_mappings']:
        provider_id = provider_map.get(provider_idx)
        dept_id = dept_map.get(dept_idx)
        
        if not provider_id or not dept_id:
            print(f"  ERROR: Invalid mapping - provider {provider_idx}, dept {dept_idx}")
            continue
        
        supabase.table('provider_departments').insert({
            'provider_id': provider_id,
            'department_id': dept_id
        }).execute()
        
        print(f"  ✓ Provider {provider_id} ↔ Department {dept_id}")


def seed_patients(provider_map: dict):
    """Insert sample patients."""
    print("\nSeeding patients...")
    
    # Patient 1: John Doe (from requirements)
    john_result = supabase.table('patients').insert({
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': '01/01/1975',
        'pcp': 'Dr. Meredith Grey',
        'ehr_id': '1234abcd',
        'notes': 'Patient prefers afternoon appointments. Previous no-show on 9/17/24.'
    }).execute()
    
    john_id = john_result.data[0]['id']
    print(f"  ✓ John Doe - ID: {john_id}")
    
    # Patient 2: Jane Smith (optional - for testing multiple patients)
    jane_result = supabase.table('patients').insert({
        'first_name': 'Jane',
        'last_name': 'Smith',
        'dob': '05/15/1982',
        'pcp': 'Dr. Chris Perry',
        'ehr_id': '5678efgh',
        'notes': 'Patient has morning availability only.'
    }).execute()
    
    jane_id = jane_result.data[0]['id']
    print(f"  ✓ Jane Smith - ID: {jane_id}")
    
    return {'john': john_id, 'jane': jane_id}


def seed_appointments(patient_map: dict, provider_map: dict, dept_map: dict):
    """Insert appointment history."""
    print("\nSeeding appointments...")
    
    john_id = patient_map['john']
    
    # John's appointment history (from requirements)
    appointments = [
        {
            'patient_id': john_id,
            'provider_id': provider_map[1],  # Dr. Grey (provider index 1)
            'department_id': dept_map[1],    # Sloan Primary Care
            'appointment_type': 'ESTABLISHED',
            'date': '2018-03-05',
            'appointment_time': '09:15',
            'arrival_time': '09:05',  # ESTABLISHED: 10 min early
            'status': 'completed',
            'notes': 'Annual checkup'
        },
        {
            'patient_id': john_id,
            'provider_id': provider_map[2],  # Dr. House (provider index 2)
            'department_id': dept_map[2],    # PPTH Orthopedics
            'appointment_type': 'ESTABLISHED',
            'date': '2024-08-12',
            'appointment_time': '14:30',
            'arrival_time': '14:20',
            'status': 'completed',
            'notes': 'Knee pain evaluation'
        },
        {
            'patient_id': john_id,
            'provider_id': provider_map[1],  # Dr. Grey
            'department_id': dept_map[1],
            'appointment_type': 'ESTABLISHED',
            'date': '2024-09-17',
            'appointment_time': '10:00',
            'arrival_time': '09:50',
            'status': 'noshow',
            'notes': 'Patient called to reschedule'
        },
        {
            'patient_id': john_id,
            'provider_id': provider_map[1],  # Dr. Grey
            'department_id': dept_map[1],
            'appointment_type': 'ESTABLISHED',
            'date': '2024-11-25',
            'appointment_time': '11:30',
            'arrival_time': '11:20',
            'status': 'cancelled',
            'notes': 'Cancelled by patient - conflict'
        }
    ]
    
    for apt in appointments:
        supabase.table('appointments').insert(apt).execute()
        print(f"  ✓ {apt['date']} - {apt['status']}")


def seed_insurances(parsed_data: dict):
    """Insert accepted insurances."""
    print("\nSeeding insurances...")
    
    for insurance in parsed_data['insurances']:
        supabase.table('insurances').insert({
            'name': insurance
        }).execute()
        print(f"  ✓ {insurance}")


def main():
    """Main seeding workflow."""
    print("="*60)
    print("CARE COORDINATOR - DATABASE SEEDING")
    print("="*60)
    print()
    
    # Parse data_sheet.txt
    print("Parsing data_sheet.txt...")
    parsed_data = parse_data_sheet('../data_sheet.txt')
    print(f"✓ Found {len(parsed_data['providers'])} providers, {len(parsed_data['departments'])} departments\n")
    
    try:
        # Seed in dependency order
        specialty_map = seed_specialties(parsed_data)
        provider_map = seed_providers(parsed_data, specialty_map)
        dept_map = seed_departments(parsed_data)
        seed_provider_departments(parsed_data, provider_map, dept_map)
        patient_map = seed_patients(provider_map)
        seed_appointments(patient_map, provider_map, dept_map)
        seed_insurances(parsed_data)
        
        print("\n" + "="*60)
        print("✓ DATABASE SEEDING COMPLETE!")
        print("="*60)
        print("\nNext step: Run test_db.py to verify data")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nMake sure:")
        print("1. Schema has been applied to Supabase")
        print("2. .env file has correct credentials")
        print("3. data_sheet.txt exists in parent directory")
        raise


if __name__ == '__main__':
    main()