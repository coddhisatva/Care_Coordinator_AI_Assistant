"""
Test Care Coordinator Agent in terminal/console.
Interactive testing before building frontend.
"""

import requests
from agent import Agent
from appointment_state import Patient

API_BASE = 'http://localhost:5000'


def load_patient(patient_id: int) -> Patient:
    """Load patient data from API."""
    try:
        response = requests.get(f'{API_BASE}/patient/{patient_id}')
        
        if response.status_code != 200:
            print(f"Error loading patient: {response.text}")
            return None
        
        data = response.json()
        return Patient.from_api(data)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def print_separator():
    """Print visual separator."""
    print("\n" + "="*60 + "\n")


def interactive_test():
    """Interactive chat with agent."""
    print("="*60)
    print("CARE COORDINATOR AGENT - INTERACTIVE TEST")
    print("="*60)
    print("\nMake sure flask-app.py is running!")
    print("(In another terminal: python flask-app.py)\n")
    
    # Load patient
    print("Loading patient data...")
    patient = load_patient(1)  # John Doe
    
    if not patient:
        print("Failed to load patient. Check if Flask API is running.")
        return
    
    print(f"✓ Loaded patient: {patient.name}")
    print(f"  DOB: {patient.dob}")
    print(f"  PCP: {patient.pcp}")
    print(f"  Referrals: {len(patient.referrals)}")
    print(f"  Past appointments: {len(patient.appointments)}")
    
    # Create agent
    print("\nInitializing agent...")
    agent = Agent(patient)
    print("✓ Agent ready!")
    
    print_separator()
    print("You can now chat with the agent.")
    print("Commands:")
    print("  - Type your message and press Enter")
    print("  - 'status' - Show booking progress")
    print("  - 'reset' - Reset conversation")
    print("  - 'quit' - Exit")
    print_separator()
    
    # Conversation loop
    while True:
        try:
            # Get user input
            user_input = input("Nurse: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == 'status':
                print("\nCurrent Booking Progress:")
                print(agent.get_booking_progress())
                print()
                continue
            
            elif user_input.lower() == 'reset':
                agent.reset_conversation()
                print("✓ Conversation reset\n")
                continue
            
            # Get agent response
            print("Agent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            print()
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


def automated_test_scenarios():
    """
    Run automated test scenarios to verify agent works.
    """
    print("="*60)
    print("CARE COORDINATOR AGENT - AUTOMATED TESTS")
    print("="*60)
    
    # Load patient
    print("\n1. Loading patient...")
    patient = load_patient(1)
    
    if not patient:
        print("❌ Failed to load patient")
        return
    
    print(f"✓ Loaded patient: {patient.name}")
    
    # Create agent
    print("\n2. Creating agent...")
    agent = Agent(patient)
    print("✓ Agent created")
    
    # Test scenario 1: Book orthopedics appointment
    print_separator()
    print("TEST SCENARIO 1: Book Orthopedics Appointment")
    print_separator()
    
    test_messages = [
        "I need to book an orthopedics appointment for this patient",
        "Dr. House",
        "PPTH Orthopedics",
        "March 25th, 2026",
        "2:00pm",
        "Yes, please book it"
    ]
    
    for msg in test_messages:
        print(f"\nNurse: {msg}")
        response = agent.chat(msg)
        print(f"Agent: {response}")
        
        # Stop if booking completed
        if "successfully" in response.lower() or "booked" in response.lower():
            print("\n✓ Booking completed!")
            break
    
    # Show final status
    print("\nFinal Booking Status:")
    print(agent.get_booking_progress())
    
    print_separator()
    print("TESTS COMPLETE")
    print_separator()


def main():
    """Main entry point."""
    print("\nCare Coordinator Agent Testing")
    print("Choose mode:")
    print("  1. Interactive chat")
    print("  2. Automated test scenarios")
    print("  3. Both")
    
    choice = input("\nYour choice (1/2/3): ").strip()
    
    if choice == '1':
        interactive_test()
    elif choice == '2':
        automated_test_scenarios()
    elif choice == '3':
        automated_test_scenarios()
        print("\n\nNow starting interactive mode...")
        input("Press Enter to continue...")
        interactive_test()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")