"""
Care Coordinator Agent - Core Implementation
Handles conversation loop, tool calling, and OpenAI integration.
"""

import os
import json
from typing import List, Dict, Optional, Callable
from dotenv import load_dotenv
import openai

from config import SYSTEM_PROMPT, GREETING_PROMPT, TOOLS, TOOL_FUNCTIONS, MAX_ITERATIONS, WARNING_THRESHOLD, WARNING_MESSAGE, MODEL
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
        self.tool_map = TOOL_FUNCTIONS
        self.iteration_count = 0
        self.tool_calls_log = []  # Track tool calls for debugging
        
        # Initialize conversation with system prompt and patient context
        patient_context = self._build_patient_context()
        self.messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\n" + patient_context
        })
    
    def generate_initial_greeting(self) -> str:
        """
        Generate initial greeting using LLM based on patient context.
        Agent can call tools (e.g., check insurance) during greeting.
        """
        try:
            # Add greeting prompt
            self.messages.append({
                "role": "user",
                "content": GREETING_PROMPT
            })
            
            # Allow tool calls during greeting
            while True:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=TOOLS,
                    temperature=0.7,
                    max_tokens=300
                )
                
                assistant_message = response.choices[0].message
                self.messages.append(assistant_message)
                
                # If tool calls, execute them
                if assistant_message.tool_calls:
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        result = self._execute_tool(tool_name, tool_args)
                        
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": json.dumps(result)
                        })
                    continue
                
                # No tool calls, return greeting
                return assistant_message.content
        
        except Exception as e:
            # Fallback if LLM fails
            return f"Hi! I'm here to help book an appointment for {self.patient.name}. What details can you provide?"
    
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
                    "content": WARNING_MESSAGE
                })
            
            # Call OpenAI with tools
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    tools=TOOLS,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                assistant_message = response.choices[0].message
                
                # Add assistant message to history
                self.messages.append(assistant_message)

                # Check for tool calls (OpenAI native format)
                if assistant_message.tool_calls:
                    # Execute tools and add results
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        # Log tool call for debugging
                        self.tool_calls_log.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "iteration": self.iteration_count
                        })
                        
                        # Execute tool
                        result = self._execute_tool(tool_name, tool_args)
                        
                        # Add tool result to conversation
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": json.dumps(result)
                        })
                    
                    # Continue loop to get agent's response to tool results
                    continue
                
                # No tool calls, return response to user
                return assistant_message.content
                
            except Exception as e:
                error_message = f"Error calling OpenAI: {str(e)}"
                print(error_message)
                return error_message
        
        # Hit max iterations
        return "I've reached the maximum number of actions for this conversation. Let me summarize what we've done so far and we can continue with a fresh start if needed."
    
    def _execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Execute a tool and return its result."""
        if tool_name not in self.tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            tool_function = self.tool_map[tool_name]
            result = tool_function(**arguments)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def get_booking_progress(self) -> str:
        """Get current booking progress summary."""
        return self.booking.summary()
    
    def get_tool_calls(self) -> list:
        """Get recent tool calls for debugging."""
        return self.tool_calls_log[-10:]  # Last 10 calls
    
    def reset_conversation(self):
        """Reset conversation but keep patient context."""
        self.messages = [self.messages[0]]  # Keep system prompt
        self.iteration_count = 0
        self.booking = AppointmentBooking(patient=self.patient)
        self.tool_calls_log = []  # Clear tool calls log