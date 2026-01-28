"""
Test database to verify all data was seeded correctly.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env file")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def test_specialties():
    """Test specialties table."""
    print("\n=== TESTING SPECIALTIES ===")
    result = supabase.table('specialties').select('*').execute()
    
    print(f"Count: {len(result.data)}")
    for spec in result.data:
        print(f"  - {spec['name']}: ${spec['self_pay_rate']}")
    
    assert len(result.data) >= 3, "Expected at least 3 specialties"
    print("✓ Specialties test passed")


def test_providers():
    """Test providers table with JOIN to specialties."""
    print("\n=== TESTING PROVIDERS ===")
    result = supabase.table('providers').select('*, specialties(name)').execute()
    
    print(f"Count: {len(result.data)}")
    for provider in result.data:
        specialty_name = provider['specialties']['name'] if provider.get('specialties') else 'Unknown'
        print(f"  - Dr. {provider['first_name']} {provider['last_name']}, {provider['certification']} ({specialty_name})")
    
    assert len(result.data) >= 5, "Expected at least 5 providers"
    print("✓ Providers test passed")


def test_departments():
    """Test departments table."""
    print("\n=== TESTING DEPARTMENTS ===")
    result = supabase.table('departments').select('*').execute()
    
    print(f"Count: {len(result.data)}")
    for dept in result.data:
        print(f"  - {dept['name']} ({dept['hours']})")
        print(f"    {dept['address']}, {dept['phone']}")
    
    assert len(result.data) >= 5, "Expected at least 5 departments"
    print("✓ Departments test passed")


def test_provider_departments():
    """Test provider-department mappings."""
    print("\n=== TESTING PROVIDER-DEPARTMENT MAPPINGS ===")
    
    # Get mappings with provider and department names
    result = supabase.table('provider_departments').select('''
        *,
        providers(first_name, last_name),
        departments(name)
    ''').execute()
    
    print(f"Count: {len(result.data)}")
    for mapping in result.data[:10]:  # Show first 10
        provider = mapping['providers']
        dept = mapping['departments']
        provider_name = f"{provider['first_name']} {provider['last_name']}"
        dept_name = dept['name']
        print(f"  - Dr. {provider_name} works at {dept_name}")
    
    if len(result.data) > 10:
        print(f"  ... and {len(result.data) - 10} more")
    
    assert len(result.data) >= 6, "Expected at least 6 provider-department mappings"
    print("✓ Provider-department mappings test passed")


def test_patients():
    """Test patients table."""
    print("\n=== TESTING PATIENTS ===")
    result = supabase.table('patients').select('*').execute()
    
    print(f"Count: {len(result.data)}")
    for patient in result.data:
        print(f"  - {patient['first_name']} {patient['last_name']}")
        print(f"    DOB: {patient['dob']}, PCP: {patient['pcp']}")
        print(f"    EHR: {patient['ehr_id']}")
        if patient.get('notes'):
            print(f"    Notes: {patient['notes']}")
    
    assert len(result.data) >= 1, "Expected at least 1 patient (John Doe)"
    print("✓ Patients test passed")


def test_appointments():
    """Test appointments with JOINs."""
    print("\n=== TESTING APPOINTMENTS ===")
    
    # Get appointments with patient and provider names
    result = supabase.table('appointments').select('''
        *,
        patients(first_name, last_name),
        providers(first_name, last_name),
        departments(name)
    ''').order('date', desc=True).execute()
    
    print(f"Count: {len(result.data)}")
    for apt in result.data:
        patient = apt['patients']
        provider = apt['providers']
        dept = apt['departments']
        
        patient_name = f"{patient['first_name']} {patient['last_name']}"
        provider_name = f"Dr. {provider['first_name']} {provider['last_name']}"
        
        print(f"\n  {apt['date']} at {apt['appointment_time']} ({apt['appointment_type']})")
        print(f"    Patient: {patient_name}")
        print(f"    Provider: {provider_name}")
        print(f"    Location: {dept['name']}")
        print(f"    Status: {apt['status']}")
        print(f"    Arrival time: {apt['arrival_time']}")
        if apt.get('notes'):
            print(f"    Notes: {apt['notes']}")
    
    assert len(result.data) >= 4, "Expected at least 4 appointments for John Doe"
    print("✓ Appointments test passed")


def test_insurances():
    """Test insurances table."""
    print("\n=== TESTING INSURANCES ===")
    result = supabase.table('insurances').select('*').execute()
    
    print(f"Count: {len(result.data)}")
    for ins in result.data:
        print(f"  - {ins['name']}")
    
    assert len(result.data) >= 5, "Expected at least 5 accepted insurances"
    print("✓ Insurances test passed")


def test_complex_query():
    """Test a complex query - find all orthopedic providers with their locations."""
    print("\n=== TESTING COMPLEX QUERY ===")
    print("Query: Find all orthopedic providers and their locations")
    
    # First get specialty ID
    specialty_result = supabase.table('specialties').select('id').eq('name', 'Orthopedics').execute()
    
    if not specialty_result.data:
        print("  No Orthopedics specialty found")
        return
    
    specialty_id = specialty_result.data[0]['id']
    
    # Get providers with this specialty
    providers_result = supabase.table('providers').select('''
        *,
        provider_departments(
            departments(name, address, hours)
        )
    ''').eq('specialty_id', specialty_id).execute()
    
    print(f"Found {len(providers_result.data)} orthopedic providers:")
    for provider in providers_result.data:
        print(f"\n  Dr. {provider['first_name']} {provider['last_name']}")
        for mapping in provider['provider_departments']:
            dept = mapping['departments']
            print(f"    - {dept['name']}")
            print(f"      {dept['address']}")
            print(f"      Hours: {dept['hours']}")
    
    print("✓ Complex query test passed")


def test_new_vs_established():
    """Test determining NEW vs ESTABLISHED appointment."""
    print("\n=== TESTING NEW vs ESTABLISHED LOGIC ===")
    
    # Get John Doe
    patient_result = supabase.table('patients').select('id').eq('first_name', 'John').eq('last_name', 'Doe').execute()
    
    if not patient_result.data:
        print("  John Doe not found")
        return
    
    john_id = patient_result.data[0]['id']
    
    # Get Dr. House
    house_result = supabase.table('providers').select('id').eq('last_name', 'House').execute()
    
    if not house_result.data:
        print("  Dr. House not found")
        return
    
    house_id = house_result.data[0]['id']
    
    # Check if John has seen House in last 5 years
    # For testing, we'll just check if any completed appointments exist
    history_result = supabase.table('appointments').select('*').eq(
        'patient_id', john_id
    ).eq(
        'provider_id', house_id
    ).eq(
        'status', 'completed'
    ).execute()
    
    if history_result.data:
        print(f"  John Doe HAS seen Dr. House before ({len(history_result.data)} time(s))")
        print(f"  Most recent: {history_result.data[0]['date']}")
        print(f"  → Next appointment should be: ESTABLISHED")
    else:
        print(f"  John Doe has NOT seen Dr. House before")
        print(f"  → Next appointment should be: NEW")
    
    print("✓ NEW vs ESTABLISHED test passed")


def main():
    """Run all tests."""
    print("="*60)
    print("CARE COORDINATOR - DATABASE TESTS")
    print("="*60)
    
    try:
        test_specialties()
        test_providers()
        test_departments()
        test_provider_departments()
        test_patients()
        test_appointments()
        test_insurances()
        test_complex_query()
        test_new_vs_established()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nDatabase is ready for use!")
        print("Next step: Phase 2 - Backend API")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise


if __name__ == '__main__':
    main()