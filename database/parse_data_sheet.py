"""
Parse data_sheet.txt and extract structured data for database seeding.
"""

import re
from typing import Dict, List, Tuple


def parse_data_sheet(filepath: str = '../data_sheet.txt') -> Dict:
    """
    Parse data_sheet.txt and return structured data.
    
    Returns:
        Dict with keys: providers, departments, specialties, insurances, specialty_rates
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract sections
    provider_section = extract_section(content, 'Provider Directory', 'Appointments:')
    appointments_section = extract_section(content, 'Appointments:', 'Accepted Insurances:')
    insurance_section = extract_section(content, 'Accepted Insurances:', 'Self-pay:')
    rates_section = extract_section(content, 'Self-pay:', None)
    
    # Parse each section
    providers, departments, provider_dept_mappings = parse_providers(provider_section)
    specialties = extract_specialties(providers)
    specialty_rates = parse_specialty_rates(rates_section)
    insurances = parse_insurances(insurance_section)
    
    return {
        'providers': providers,
        'departments': departments,
        'provider_dept_mappings': provider_dept_mappings,
        'specialties': specialties,
        'specialty_rates': specialty_rates,
        'insurances': insurances
    }


def extract_section(content: str, start_marker: str, end_marker: str = None) -> str:
    """Extract a section of text between two markers."""
    start_idx = content.find(start_marker)
    if start_idx == -1:
        return ""
    
    if end_marker:
        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            return content[start_idx:]
        return content[start_idx:end_idx]
    else:
        return content[start_idx:]


def parse_providers(provider_text: str) -> Tuple[List[Dict], List[Dict], List[Tuple]]:
    """
    Parse provider directory section.
    
    Returns:
        (providers, departments, provider_dept_mappings)
    """
    providers = []
    departments = []
    provider_dept_mappings = []
    
    dept_id_counter = 1
    dept_name_to_id = {}
    
    # Split by provider (lines starting with "- " followed by name)
    provider_blocks = re.split(r'\n- ([A-Za-z]+, [A-Za-z]+)\n', provider_text)
    
    # Skip first empty element
    for i in range(1, len(provider_blocks), 2):
        if i + 1 >= len(provider_blocks):
            break
            
        name = provider_blocks[i]
        details = provider_blocks[i + 1]
        
        # Parse name (format: "Last, First")
        last_name, first_name = [n.strip() for n in name.split(',')]
        
        # Parse certification
        cert_match = re.search(r'certification:\s*(.+)', details)
        certification = cert_match.group(1).strip() if cert_match else ""
        
        # Parse specialty
        spec_match = re.search(r'specialty:\s*(.+)', details)
        specialty = spec_match.group(1).strip() if spec_match else ""
        
        provider = {
            'first_name': first_name,
            'last_name': last_name,
            'certification': certification,
            'specialty': specialty
        }
        providers.append(provider)
        provider_id = len(providers)  # 1-indexed
        
        # Parse departments for this provider
        dept_blocks = re.findall(r'department:\s*\n\s*- name:\s*(.+)\n\s*- phone:\s*(.+)\n\s*- address:\s*(.+)\n\s*- hours:\s*(.+)', details)
        
        for dept_name, phone, address, hours in dept_blocks:
            dept_name = dept_name.strip()
            phone = phone.strip()
            address = address.strip()
            hours = hours.strip()
            
            # Check if department already exists
            if dept_name not in dept_name_to_id:
                department = {
                    'name': dept_name,
                    'phone': phone,
                    'address': address,
                    'hours': hours
                }
                departments.append(department)
                dept_name_to_id[dept_name] = dept_id_counter
                dept_id = dept_id_counter
                dept_id_counter += 1
            else:
                dept_id = dept_name_to_id[dept_name]
            
            # Map provider to department
            provider_dept_mappings.append((provider_id, dept_id))
    
    return providers, departments, provider_dept_mappings


def extract_specialties(providers: List[Dict]) -> List[str]:
    """Extract unique specialties from providers."""
    specialties = set()
    for provider in providers:
        if provider['specialty']:
            specialties.add(provider['specialty'])
    return sorted(list(specialties))


def parse_specialty_rates(rates_text: str) -> Dict[str, int]:
    """
    Parse self-pay rates section.
    
    Returns:
        Dict mapping specialty name to rate (e.g., {'Primary Care': 150})
    """
    rates = {}
    
    # Pattern: "- Specialty: $amount"
    matches = re.findall(r'-\s*([^:]+):\s*\$(\d+)', rates_text)
    
    for specialty, amount in matches:
        specialty = specialty.strip()
        rates[specialty] = int(amount)
    
    return rates


def parse_insurances(insurance_text: str) -> List[str]:
    """Parse accepted insurances section."""
    insurances = []
    
    # Each insurance is on a line starting with "- "
    matches = re.findall(r'-\s*(.+)', insurance_text)
    
    for insurance in matches:
        insurance = insurance.strip()
        if insurance:
            insurances.append(insurance)
    
    return insurances


if __name__ == '__main__':
    # Test the parser
    data = parse_data_sheet('../data_sheet.txt')
    
    print("=== PARSED DATA ===\n")
    print(f"Providers: {len(data['providers'])}")
    for p in data['providers']:
        print(f"  - {p['first_name']} {p['last_name']}, {p['certification']} ({p['specialty']})")
    
    print(f"\nDepartments: {len(data['departments'])}")
    for d in data['departments']:
        print(f"  - {d['name']} ({d['hours']})")
    
    print(f"\nSpecialties: {data['specialties']}")
    print(f"Specialty Rates: {data['specialty_rates']}")
    print(f"Insurances: {data['insurances']}")
    print(f"\nProvider-Department Mappings: {len(data['provider_dept_mappings'])}")