"""
Care Coordinator Agent - Core Implementation
Handles conversation loop, tool calling, and OpenAI integration.
"""

import os
import json
import re
from typing import List, Dict, Optional, Callable
from dotenv import load_dotenv
import openai
from tools import book_appointment

from config import SYSTEM_PROMPT, TOOLS, MAX_ITERATIONS, WARNING_THRESHOLD, MODEL
from appointment_state import Patient, AppointmentBooking

load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    print("WARNING: OPENAI_API_KEY not found in .env file")


class Agent:
    """
    Care Coordinator conversational agent with tool calling capabilities.
    """
    
    def __init__(self, patient: Patient, model: str = MODEL):
        self.patient = patient
        self.booking = AppointmentBooking(patient=patient)
        self.model = model
        self.messages = []
        self.tool_map = {tool['name']: tool['function'] for tool in TOOLS}
        self.iteration_count = 0
        
        # Initialize conversation with system prompt and patient context
        patient_context = self._build_patient_context()
        self.messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\n" + patient_context
        })
    
    def _build_patient_context(self) -> str:
        """Build patient context string for system prompt."""
        context = f"""
		CURRENT PATIENT INFORMATION:
		- Name: {self.patient.name}
		- DOB: {self.patient.dob}
		- PCP: {self.patient.pcp}
		- EHR ID: {self.patient.ehr_id}
		"""
        
        if self.patient.notes:
            context += f"- Notes: {self.patient.notes}\n"
        
        if self.patient.referrals:
            context += "\nREFERRALS:\n"
            for ref in self.patient.referrals:
                specialty = ref.get('specialty', 'Unknown')
                provider = ref.get('provider', 'No specific provider')
                context += f"- {specialty}: {provider}\n"
        
        if self.patient.appointments:
            context += f"\nRECENT APPOINTMENT HISTORY ({len(self.patient.appointments)} appointments):\n"
            for apt in self.patient.appointments[:5]:  # Show last 5
                context += f"- {apt.get('date')}: {apt.get('provider')} ({apt.get('status')})\n"
        
        return context
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and return agent's response.
        Handles tool calling loop internally.
        """
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Conversation loop with tool calling
        while self.iteration_count < MAX_ITERATIONS:
            self.iteration_count += 1
            
            # Warning if approaching iteration limit
            if self.iteration_count == WARNING_THRESHOLD:
                self.messages.append({
                    "role": "system",
                    "content": f"You have made {WARNING_THRESHOLD} tool calls. Most tasks should complete in 4-8 calls. Reassess your approach and work toward completion."
                })
            
            # Call OpenAI
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                assistant_message = response.choices[0].message.content
                
                # Add assistant message to history
                self.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })

				# Check if agent is ready to book
                if self._ready_to_book(assistant_message):
                    if self.booking.is_complete():
                        # Use booking state to book
                        booking_data = self.booking.to_booking_request()
                        result = book_appointment(**booking_data)
                        
                        # Add result to conversation
                        self.messages.append({
                            "role": "user",
                            "content": f"Booking result:\n{json.dumps(result, indent=2)}"
                        })
                        
                        # Continue to get agent's response about the booking
                        continue
                    else:
                        # Not ready - tell agent what's missing
                        missing = self.booking.missing_fields()
                        self.messages.append({
                            "role": "user",
                            "content": f"Cannot book yet. Still need: {', '.join(missing)}"
                        })
                        continue

                # Check for tool calls
                tool_calls = self._extract_tool_calls(assistant_message)
                
                if not tool_calls:
                    # No tool calls, return response to user
                    return assistant_message
                
                # Execute tools and add results
                for tool_call in tool_calls:
                    result = self._execute_tool(tool_call)
                    
                    # Add tool result to conversation
                    self.messages.append({
                        "role": "user",
                        "content": f"Tool result for {tool_call['name']}:\n{json.dumps(result, indent=2)}"
                    })
                
                # Continue loop to process tool results
                
            except Exception as e:
                error_message = f"Error calling OpenAI: {str(e)}"
                print(error_message)
                return error_message
        
        # Hit max iterations
        return "I've reached the maximum number of actions for this conversation. Let me summarize what we've done so far and we can continue with a fresh start if needed."
    
    def _extract_tool_calls(self, message: str) -> List[Dict]:
        """
        Extract tool calls from assistant message.
        Expected format: <tool_call>function_name(arg1="value", arg2=123)</tool_call>
        """
        tool_calls = []
        pattern = r'<tool_call>(.*?)</tool_call>'
        matches = re.findall(pattern, message, re.DOTALL)
        
        for match in matches:
            # Parse function call
            # Format: function_name(arg1="value", arg2=123)
            func_pattern = r'(\w+)\((.*?)\)'
            func_match = re.match(func_pattern, match.strip())
            
            if func_match:
                func_name = func_match.group(1)
                args_str = func_match.group(2)
                
                # Parse arguments
                kwargs = {}
                if args_str.strip():
                    # Simple parsing - split by comma, handle quotes
                    arg_pairs = re.findall(r'(\w+)=([^,]+)', args_str)
                    for key, value in arg_pairs:
                        # Clean up value
                        value = value.strip()
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        # Try to convert to int if possible
                        try:
                            value = int(value)
                        except ValueError:
                            pass
                        kwargs[key] = value
                
                tool_calls.append({
                    "name": func_name,
                    "arguments": kwargs
                })
        
        return tool_calls

	def _ready_to_book(self, message: str) -> bool:
        """Detect if agent is trying to book appointment."""
        message_lower = message.lower()
        
        # Look for booking indicators
        booking_phrases = [
            'book the appointment',
            'book this appointment',
            'create the appointment',
            'schedule the appointment',
            'confirm the booking',
            'proceed with booking',
            '<tool_call>book_appointment'
        ]
        
        return any(phrase in message_lower for phrase in booking_phrases)
    
    def _execute_tool(self, tool_call: Dict) -> Dict:
        """Execute a tool and return its result."""
        tool_name = tool_call['name']
        arguments = tool_call['arguments']
        
        if tool_name not in self.tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            tool_function = self.tool_map[tool_name]
            result = tool_function(**arguments)
            
            # Update booking state if relevant
            self._update_booking_state(tool_name, arguments, result)
            
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _update_booking_state(self, tool_name: str, arguments: Dict, result: Dict):
        """Update booking state based on tool results."""
        # Track provider selection
        if tool_name == "get_providers_by_specialty" and result.get('found'):
            providers = result.get('providers', [])
            if len(providers) == 1:
                provider = providers[0]
                self.booking.provider_id = provider['id']
                self.booking.provider_name = f"Dr. {provider['first_name']} {provider['last_name']}"
        
        # Track location selection
        if tool_name == "get_provider_locations" and result.get('found'):
            locations = result.get('locations', [])
            if len(locations) == 1:
                location = locations[0]
                self.booking.department_id = location['department_id']
                self.booking.location_name = location['location_name']
        
        # Track appointment type determination
        if tool_name == "check_appointment_history":
            self.booking.appointment_type = result.get('appointment_type')
        
        # Track successful booking
        if tool_name == "book_appointment" and result.get('success'):
            # Booking complete - could trigger some state update
            pass
    
    def get_booking_progress(self) -> str:
        """Get current booking progress summary."""
        return self.booking.summary()
    
    def reset_conversation(self):
        """Reset conversation but keep patient context."""
        self.messages = [self.messages[0]]  # Keep system prompt
        self.iteration_count = 0
        self.booking = AppointmentBooking(patient=self.patient)