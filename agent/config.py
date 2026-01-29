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
3. If the patient has insurance that is NOT accepted, clearly state they'll need to self-pay (you may need to call tool to get this or other info)
4. If the patient has referrals, briefly mention them (specialty and provider if available)
5. Ask what details the nurse can provide to get started

Example format:
"Hi! I'm here to help book an appointment for John Doe. I see a referral for Orthopedics with Dr. Smith. What details can you provide to get started?"

Now generate the greeting for the current patient based on their information."""

# System prompt for Care Coordinator Agent
SYSTEM_PROMPT = """You are a Care Coordinator Assistant helping hospital nurses book patient appointments.

WHO YOU'RE HELPING:
The nurse is working with a specific patient. The patient's information (name, DOB, PCP, referrals, appointment history, insurance, notes) is provided to you at the start of each conversation and you can see it in the context. The nurse may have additional information the patient told them directly, or they may be figuring things out as they go, and may or may not be talking with the patient at this moment. Your job is to help them successfully book an appointment.
You dont just want to book a random appointment, but the best available appointment given the patient's needs and the nurse's input.
While we want to book the appointment efficiently and quickly, we also want to be thorough and helpful to the nurse, without cutting corners or making assumptions.


WHAT YOU CAN DO AT ANY MOMENT:
- Respond to the nurse with information, questions, or confirmation
- Call tools to query the database (get provider info, check availability, verify insurance, etc.)
- Book an appointment using the book_appointment tool (only after confirming all details with the nurse)

THE DATABASE:
Our hospital database contains providers, departments/locations, appointment schedules, patients, insurances, and referrals. You have access to pre-built query tools for common operations, plus a general query_database tool for custom SQL SELECT queries when you need something specific. You can see all available tools and their parameters.

INSURANCE:
If the patient has insurance, check if it's accepted. If not accepted or missing, the patient will need to self-pay. You can look up self-pay rates by specialty using the get_self_pay_rate tool. If the nurse provides new insurance info, use set_patient_insurance to update it (it'll tell you if we accept it or not).

BOOKING AN APPOINTMENT REQUIRES:
- Patient ID (you already have this)
- Provider ID (which doctor - look up by specialty if needed)
- Department ID (which location - providers can work at multiple locations)
- Appointment type: NEW (patient hasn't seen this provider in 5+ years) or ESTABLISHED (patient has seen them recently) - use check_appointment_history to determine this
- Date and time (check availability with get_available_times)
- Optional: notes

BEFORE YOU BOOK:
You must confirm the final details with the nurse. Don't just book silently. Say something like "Ready to book: Dr. Smith at Main Campus on Monday Feb 3 at 2:00pm, NEW patient appointment. Should I proceed?" Wait for confirmation, then call book_appointment.

YOUR APPROACH:
When the nurse asks for something, figure out what information you need. If you need to look things up, call the appropriate tools and present the findings. If there are multiple options (several providers, many time slots, multiple locations), present them clearly and let the nurse choose - don't pick for them. If something is ambiguous or you're missing key information, ask. 
It's up to you to determine if the next best action is to get more information yourself with tool calls, or ask the nurse for specific clarifications. 
You know what information is needed to book the appointment, and you can drive towards that to make your next decision.
This will likely be an iterative process between you and the nurse, though it's possible with the initial info you get from the patient info and nurse, as wel as info you can get from the dbs, that you can present an ideal appointment or set of potential appointments very quickly.

A good time to ask for info is when:
-You need more clarity about the patient's needs or preferences for an appointment to narrow it down, such as after you have returned a broad range from the db
-You need some specific info to make a specific db call that would help you narrow down the options or confirm the appointment
-Other times you think it's valuable

TOOL CALL LIMIT:
You have a limit of 10 tool calls per conversation to keep things efficient and on-track. Most bookings should only need 4-8 calls (e.g., find provider, get locations, check availability, check history, book). If you're approaching the limit without progress, reassess your approach. You'll get a warning at 6 calls.

TONE:
Professional, helpful, efficient. Nurses are busy - be concise and proactive. After you book an appointment, provide clear confirmation with all the details (provider, location, date, time, appointment type, arrival time)."""

# Tool function mapping
TOOL_FUNCTIONS = {
    "get_providers_by_specialty": get_providers_by_specialty,
    "get_provider_locations": get_provider_locations,
    "get_available_times": get_available_times,
    "check_appointment_history": check_appointment_history,
    "check_insurance": check_insurance,
    "get_self_pay_rate": get_self_pay_rate,
    "set_patient_insurance": set_patient_insurance,
    "book_appointment": book_appointment,
    "query_database": query_database
}

# Tool definitions for OpenAI (native function calling format)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_providers_by_specialty",
            "description": "Find all providers with a specific specialty (e.g., 'Orthopedics', 'Primary Care', 'Surgery'). Returns list of providers with their IDs, names, and certifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {
                        "type": "string",
                        "description": "The medical specialty to search for"
                    }
                },
                "required": ["specialty"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_provider_locations",
            "description": "Get all locations where a specific provider works, including addresses, phone numbers, and office hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "provider_id": {
                        "type": "integer",
                        "description": "The provider's ID number"
                    }
                },
                "required": ["provider_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_times",
            "description": "Get available appointment times for a provider at a specific location. Can check a single date or date range. Returns office hours and currently booked times.",
            "parameters": {
                "type": "object",
                "properties": {
                    "provider_id": {
                        "type": "integer",
                        "description": "The provider's ID number"
                    },
                    "department_id": {
                        "type": "integer",
                        "description": "The department/location ID"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "This paramater is a date in YYYY-MM-DD format, and can mean two different things. If the end_date (optional, subsequent paramater) is provided, this paramater is the start date of the date range. If the end_date is not provided, this paramater is the single date to check for available times."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Optional end date for checking a range, in YYYY-MM-DD format"
                    }
                },
                "required": ["provider_id", "department_id", "start_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_appointment_history",
            "description": "Check if patient has seen a specific provider in the last 5 years. This determines if the appointment should be NEW (patient hasn't seen provider in 5+ years) or ESTABLISHED (patient has seen provider recently). Use this before booking to determine appointment type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "integer",
                        "description": "The patient's ID number"
                    },
                    "provider_id": {
                        "type": "integer",
                        "description": "The provider's ID number"
                    }
                },
                "required": ["patient_id", "provider_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_insurance",
            "description": "Check if a specific insurance is accepted. Returns whether the insurance is accepted and provides list of accepted insurances if not found.",
            "parameters": {
                "type": "object",
                "properties": {
                    "insurance_name": {
                        "type": "string",
                        "description": "The insurance provider name (e.g., 'Aetna', 'Blue Cross')"
                    }
                },
                "required": ["insurance_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_self_pay_rate",
            "description": "Get the self-pay cost for a specific medical specialty if patient is paying out of pocket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {
                        "type": "string",
                        "description": "The medical specialty (e.g., 'Primary Care', 'Orthopedics')"
                    }
                },
                "required": ["specialty"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_patient_insurance",
            "description": "Set or update a patient's insurance. Use this when nurse provides insurance information. If the insurance doesn't exist in our system, it will be added (marked as not accepted). Returns whether the insurance is accepted or if patient will need to self-pay.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "integer",
                        "description": "The patient's ID number"
                    },
                    "insurance_name": {
                        "type": "string",
                        "description": "The insurance provider name (e.g., 'Aetna', 'Cigna')"
                    }
                },
                "required": ["patient_id", "insurance_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment (FINAL ACTION). Only call this once you have confirmed all details with the nurse: provider, location, appointment type (NEW/ESTABLISHED), date, and time. This actually creates the appointment in the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "integer",
                        "description": "The patient's ID number"
                    },
                    "provider_id": {
                        "type": "integer",
                        "description": "The provider's ID number"
                    },
                    "department_id": {
                        "type": "integer",
                        "description": "The department/location ID"
                    },
                    "appointment_type": {
                        "type": "string",
                        "description": "Either 'NEW' or 'ESTABLISHED' - must be determined using check_appointment_history first"
                    },
                    "date": {
                        "type": "string",
                        "description": "Appointment date in YYYY-MM-DD format"
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "Appointment time in HH:MM format (24-hour)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the appointment"
                    }
                },
                "required": ["patient_id", "provider_id", "department_id", "appointment_type", "date", "appointment_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Execute a custom SQL SELECT query for flexibility when other tools don't fit the need. Use this for complex queries or when you need specific information not covered by other tools. Only SELECT queries are allowed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    },
                    "params": {
                        "type": "array",
                        "description": "Optional list of parameters for parameterized query",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["sql"]
            }
        }
    }
]

# Agent settings
MAX_ITERATIONS = 10
WARNING_THRESHOLD = 6
MODEL = "gpt-4"  # or "gpt-4-turbo" or "gpt-3.5-turbo"

# Warning system message
WARNING_MESSAGE = "Note: You have made 6 tool calls. Most tasks should complete in 4-8 calls, and your limit is 10. Keep this in mind as you continue to drive towards booking an appointment while being helpful to the nurse."