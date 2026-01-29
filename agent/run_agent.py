"""
Care Coordinator Agent - WebSocket Server
ONE connection, ONE message handler.
"""

import os
import sys
from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from agent import Agent
from appointment_state import Patient

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store agents by session
agents = {}

API_BASE = os.getenv('API_BASE_URL', 'http://localhost:5002')


def initialize_agent_for_patient(user_id: str, patient_id: str):
    """
    Helper: Load patient, create agent, generate greeting.
    Used by both connect and next_patient.
    """
    # Load patient
    response = requests.get(f'{API_BASE}/patient/{patient_id}')
    if response.status_code != 200:
        raise Exception(f"Patient {patient_id} not found")
    
    patient_data = response.json()
    patient = Patient.from_api(patient_data)
    
    # Create agent
    agent = Agent(patient)
    
    # Generate greeting using LLM
    greeting = agent.generate_initial_greeting()
    
    return agent, greeting, patient.name


@socketio.on('connect')
def handle_connect():
    """
    Client connects with user_id and patient_id in query params.
    Creates agent and sends greeting.
    """
    user_id = request.args.get('user_id')
    patient_id = request.args.get('patient_id', '1')
    
    if not user_id:
        emit('error', {"message": "Missing user_id"})
        return
    
    print(f"Client connected: user={user_id}, patient={patient_id}")
    
    try:
        # Check if agent exists and can resume
        existing_agent = agents.get(user_id)
        if existing_agent and str(existing_agent.patient.id) == patient_id:
            # Resume existing conversation - don't send message, frontend keeps history
            print(f"Resuming conversation for user {user_id}")
            return
        
        # New patient - initialize
        agent, greeting, patient_name = initialize_agent_for_patient(user_id, patient_id)
        agents[user_id] = agent
        
        emit('message', {"text": greeting, "patient_name": patient_name})
        
    except Exception as e:
        print(f"Error on connect: {e}")
        emit('error', {"message": str(e)})


@socketio.on('message')
def handle_message(data):
    """
    Handle all messages. This is the main loop iteration.
    """
    user_id = request.args.get('user_id')
    agent = agents.get(user_id)
    
    if not agent:
        emit('error', {"message": "No agent found. Reconnect."})
        return
    
    try:
        # Regular chat message
        message_text = data.get('text')
        if not message_text:
            emit('error', {"message": "No text in message"})
            return
        
        # Agent processes (can take minutes - no timeout!)
        response = agent.chat(message_text)
        progress = agent.get_booking_progress()
        tool_calls = agent.get_tool_calls()
        
        # Send response
        emit('message', {
            "text": response, 
            "booking_progress": progress,
            "tool_calls": tool_calls
        })
        
    except Exception as e:
        print(f"Error handling message: {e}")
        emit('error', {"message": str(e)})


@socketio.on('reset')
def handle_reset():
    """
    Reset conversation for current patient.
    """
    user_id = request.args.get('user_id')
    agent = agents.get(user_id)
    
    if not agent:
        emit('error', {"message": "No agent found. Reconnect."})
        return
    
    try:
        agent.reset_conversation()
        greeting = agent.generate_initial_greeting()
        emit('message', {"text": greeting})
        
    except Exception as e:
        print(f"Error resetting conversation: {e}")
        emit('error', {"message": str(e)})


@socketio.on('next_patient')
def handle_next_patient(data):
    """
    Nurse moves to next patient after booking.
    Kills current agent, starts new one.
    """
    user_id = request.args.get('user_id')
    new_patient_id = data.get('patient_id')
    
    if not new_patient_id:
        emit('error', {"message": "Missing patient_id"})
        return
    
    print(f"User {user_id} moving to patient {new_patient_id}")
    
    try:
        # Initialize new agent for new patient
        agent, greeting, patient_name = initialize_agent_for_patient(user_id, new_patient_id)
        agents[user_id] = agent
        
        emit('message', {"text": greeting, "patient_name": patient_name})
        
    except Exception as e:
        print(f"Error switching patient: {e}")
        emit('error', {"message": str(e)})


@socketio.on('disconnect')
def handle_disconnect():
    """Clean up when client disconnects"""
    user_id = request.args.get('user_id')
    # Don't delete agent - keep it for reconnect
    print(f"Client disconnected: {user_id}")


if __name__ == '__main__':
    port = int(os.getenv('AGENT_PORT', 5001))
    print("="*70)
    print("Care Coordinator Agent - WebSocket Server")
    print("="*70)
    print(f"Running on port {port}")
    print(f"API Base: {API_BASE}")
    print("="*70)
    socketio.run(app, debug=True, port=port, host='0.0.0.0')
