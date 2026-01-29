"""
Configuration for Care Coordinator Agent.
Includes system prompt and tool definitions.
"""

from tools import (
    get_providers_by_specialty,
    get_provider_locations,
    get_available_times,
    check_appointment_history,
    check_insurance,
    get_self_pay_rate,
    set_patient_insurance,
    book_appointment,
    query_database
)

# Greeting prompt for initial message generation
GREETING_PROMPT = """Generate your initial greeting to the nurse for this patient. 

Be concise and professional. Your greeting should:
1. Briefly introduce yourself as the booking assistant
2. Mention the patient's name
3. If the patient has insurance that is NOT accepted, clearly state they'll need to self-pay
4. If the patient has referrals, briefly mention them (specialty and provider if available)
5. Ask what details the nurse can provide to get started

Example format:
"Hi! I'm here to help book an appointment for John Doe. I see a referral for Orthopedics with Dr. Smith. What details can you provide to get started?"

Now generate the greeting for the current patient based on their information."""

# System prompt for Care Coordinator Agent
SYSTEM_PROMPT = """You are a Care Coordinator Assistant helping hospital nurses book patient appointments.

CONTEXT:
The nurse has already loaded patient information including:
- Demographics (name, DOB, PCP)
- Referrals (which specialists the patient needs to see)
- Appointment history (past visits)
- Patient preferences and notes

YOUR GOAL:
Guide the nurse to successfully book an appointment by collecting:
1. Provider (which doctor)
2. Location (which clinic/hospital location)
3. Date and time
4. You will determine appointment type (NEW or ESTABLISHED) using tools

WORKFLOW:
1. Understand what the nurse needs (check referrals for context)
2. Use tools to gather information about providers, locations, availability
3. Present OPTIONS to the nurse (don't make decisions for them)
4. Collect any missing information by asking
5. Once you have all required information, confirm details
6. Book the appointment using the book_appointment tool
7. Provide confirmation with all details

TOOL USAGE RULES:
- After each tool call, STOP and present findings to the nurse
- If a request isn't possible, explain why and offer alternatives
- Don't automatically retry failed queries - ASK the nurse what to do next
- Most bookings should need 4-8 tool calls
- If you've made 6+ tool calls without progress, reassess your approach

BUSINESS RULES:
- NEW appointment: Patient hasn't seen provider in 5+ years (30 min appointment, arrive 30min early)
- ESTABLISHED appointment: Patient has seen provider in last 5 years (15 min appointment, arrive 10min early)
- Use check_appointment_history tool to determine type
- Appointments must be within office hours (varies by location)
- Always confirm appointment type has been determined before booking

WHEN TO ASK FOR CLARIFICATION:
- Provider ambiguous (e.g., "Dr. H" - which one?)
- Multiple valid options exist (multiple locations, many available times)
- Missing required information (no date provided)
- Patient request is unclear

WHEN TO PROCEED FORWARD:
- You have all required information
- Request is clear and unambiguous  
- Only one logical option exists
- You can determine information from tools (like appointment type)

TONE:
Professional, concise, proactive. Nurses are busy - be efficient and helpful.

IMPORTANT:
- Never assume information - use tools to verify
- Always present options rather than making choices for the nurse
- Confirm all details before final booking
- After booking, provide clear confirmation with all appointment details"""

# Tool definitions for the agent
TOOLS = [
    {
        "name": "get_providers_by_specialty",
        "description": "Find all providers with a specific specialty (e.g., 'Orthopedics', 'Primary Care', 'Surgery'). Returns list of providers with their IDs, names, and certifications.",
        "parameters": {
            "specialty": {
                "type": "string",
                "description": "The medical specialty to search for",
                "required": True
            }
        },
        "function": get_providers_by_specialty
    },
    {
        "name": "get_provider_locations",
        "description": "Get all locations where a specific provider works, including addresses, phone numbers, and office hours.",
        "parameters": {
            "provider_id": {
                "type": "integer",
                "description": "The provider's ID number",
                "required": True
            }
        },
        "function": get_provider_locations
    },
    {
        "name": "get_available_times",
        "description": "Get available appointment times for a provider at a specific location. Can check a single date or date range. Returns office hours and currently booked times.",
        "parameters": {
            "provider_id": {
                "type": "integer",
                "description": "The provider's ID number",
                "required": True
            },
            "department_id": {
                "type": "integer",
                "description": "The department/location ID",
                "required": True
            },
            "start_date": {
                "type": "string",
                "description": "This paramater is a date in YYYY-MM-DD format, and can mean two different things. If the end_date (optional, subsequent paramater) is provided, this paramater is the start date of the date range. If the end_date is not provided, this paramater is the single date to check for available times.",
                "required": True
            },
            "end_date": {
                "type": "string",
                "description": "Optional end date for checking a range, in YYYY-MM-DD format",
                "required": False
            }
        },
        "function": get_available_times
    },
    {
        "name": "check_appointment_history",
        "description": "Check if patient has seen a specific provider in the last 5 years. This determines if the appointment should be NEW (patient hasn't seen provider in 5+ years) or ESTABLISHED (patient has seen provider recently). Use this before booking to determine appointment type.",
        "parameters": {
            "patient_id": {
                "type": "integer",
                "description": "The patient's ID number",
                "required": True
            },
            "provider_id": {
                "type": "integer",
                "description": "The provider's ID number",
                "required": True
            }
        },
        "function": check_appointment_history
    },
    {
        "name": "check_insurance",
        "description": "Check if a specific insurance is accepted. Returns whether the insurance is accepted and provides list of accepted insurances if not found.",
        "parameters": {
            "insurance_name": {
                "type": "string",
                "description": "The insurance provider name (e.g., 'Aetna', 'Blue Cross')",
                "required": True
            }
        },
        "function": check_insurance
    },
    {
        "name": "get_self_pay_rate",
        "description": "Get the self-pay cost for a specific medical specialty if patient is paying out of pocket.",
        "parameters": {
            "specialty": {
                "type": "string",
                "description": "The medical specialty (e.g., 'Primary Care', 'Orthopedics')",
                "required": True
            }
        },
        "function": get_self_pay_rate
    },
    {
        "name": "set_patient_insurance",
        "description": "Set or update a patient's insurance. Use this when nurse provides insurance information. If the insurance doesn't exist in our system, it will be added (marked as not accepted). Returns whether the insurance is accepted or if patient will need to self-pay.",
        "parameters": {
            "patient_id": {
                "type": "integer",
                "description": "The patient's ID number",
                "required": True
            },
            "insurance_name": {
                "type": "string",
                "description": "The insurance provider name (e.g., 'Aetna', 'Cigna')",
                "required": True
            }
        },
        "function": set_patient_insurance
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment (FINAL ACTION). Only call this once you have confirmed all details with the nurse: provider, location, appointment type (NEW/ESTABLISHED), date, and time. This actually creates the appointment in the system.",
        "parameters": {
            "patient_id": {
                "type": "integer",
                "description": "The patient's ID number",
                "required": True
            },
            "provider_id": {
                "type": "integer",
                "description": "The provider's ID number",
                "required": True
            },
            "department_id": {
                "type": "integer",
                "description": "The department/location ID",
                "required": True
            },
            "appointment_type": {
                "type": "string",
                "description": "Either 'NEW' or 'ESTABLISHED' - must be determined using check_appointment_history first",
                "required": True
            },
            "date": {
                "type": "string",
                "description": "Appointment date in YYYY-MM-DD format",
                "required": True
            },
            "appointment_time": {
                "type": "string",
                "description": "Appointment time in HH:MM format (24-hour)",
                "required": True
            },
            "notes": {
                "type": "string",
                "description": "Optional notes about the appointment",
                "required": False
            }
        },
        "function": book_appointment
    },
    {
        "name": "query_database",
        "description": "Execute a custom SQL SELECT query for flexibility when other tools don't fit the need. Use this for complex queries or when you need specific information not covered by other tools. Only SELECT queries are allowed.",
        "parameters": {
            "sql": {
                "type": "string",
                "description": "SQL SELECT query to execute",
                "required": True
            },
            "params": {
                "type": "array",
                "description": "Optional list of parameters for parameterized query",
                "required": False
            }
        },
        "function": query_database
    }
]

# Agent settings
MAX_ITERATIONS = 10
WARNING_THRESHOLD = 6
MODEL = "gpt-4"  # or "gpt-4-turbo" or "gpt-3.5-turbo"

# Warning system message
WARNING_MESSAGE = "Note: You have made 6 tool calls. Most tasks should complete in 4-8 calls, and your limit is 10. Keep this in mind as you continue to drive towards booking an appointment while being helpful to the nurse."