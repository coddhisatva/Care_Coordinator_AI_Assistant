"""
State management for Care Coordinator Agent.
Tracks patient information and appointment booking progress.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class Patient:
    """Patient information loaded from API."""
    id: int
    name: str
    dob: str
    pcp: str
    ehr_id: str
    notes: str
    insurance: Optional[Dict] = None  # {"id": int, "name": str, "accepted": bool}
    referrals: List[Dict] = field(default_factory=list)
    appointments: List[Dict] = field(default_factory=list)
    
    @staticmethod
    def from_api(data: dict) -> 'Patient':
        """Create Patient from API response."""
        return Patient(
            id=data['id'],
            name=data['name'],
            dob=data['dob'],
            pcp=data.get('pcp', ''),
            ehr_id=data.get('ehrId', ''),
            notes=data.get('notes', ''),
            insurance=data.get('insurance'),
            referrals=data.get('referred_providers', []),
            appointments=data.get('appointments', [])
        )


@dataclass
class AppointmentBooking:
    """
    Tracks appointment booking progress.
    Accumulates information needed to book appointment.
    """
    patient: Patient
    provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    department_id: Optional[int] = None
    location_name: Optional[str] = None
    appointment_type: Optional[str] = None  # 'NEW' or 'ESTABLISHED'
    date: Optional[str] = None  # ISO format YYYY-MM-DD
    appointment_time: Optional[str] = None  # 24hr format HH:MM
    notes: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Check if all required fields are collected."""
        required = [
            self.patient,
            self.provider_id,
            self.department_id,
            self.appointment_type,
            self.date,
            self.appointment_time
        ]
        return all(field is not None for field in required)
    
    def missing_fields(self) -> List[str]:
        """Return list of missing required fields."""
        missing = []
        
        if not self.provider_id:
            missing.append("provider")
        if not self.department_id:
            missing.append("location/department")
        if not self.appointment_type:
            missing.append("appointment type (NEW/ESTABLISHED)")
        if not self.date:
            missing.append("date")
        if not self.appointment_time:
            missing.append("time")
        
        return missing
    
    def to_booking_request(self) -> dict:
        """Convert to format expected by /api/book endpoint."""
        if not self.is_complete():
            raise ValueError(f"Cannot create booking request. Missing: {self.missing_fields()}")
        
        return {
            "patient_id": self.patient.id,
            "provider_id": self.provider_id,
            "department_id": self.department_id,
            "appointment_type": self.appointment_type,
            "date": self.date,
            "appointment_time": self.appointment_time,
            "notes": self.notes or ""
        }
    
	#for debug
    def summary(self) -> str:
        """Return human-readable summary of current state."""
        lines = []
        lines.append(f"Patient: {self.patient.name}")
        
        if self.provider_name:
            lines.append(f"Provider: {self.provider_name}")
        else:
            lines.append("Provider: (not selected)")
        
        if self.location_name:
            lines.append(f"Location: {self.location_name}")
        else:
            lines.append("Location: (not selected)")
        
        if self.appointment_type:
            lines.append(f"Type: {self.appointment_type}")
        else:
            lines.append("Type: (not determined)")
        
        if self.date and self.appointment_time:
            lines.append(f"Date/Time: {self.date} at {self.appointment_time}")
        elif self.date:
            lines.append(f"Date: {self.date} (time not selected)")
        else:
            lines.append("Date/Time: (not selected)")
        
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        
        return "\n".join(lines)