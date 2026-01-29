"""
Helper functions for Flask API.
Date/time formatting, calculations, etc.
"""

from datetime import datetime, timedelta


def calculate_arrival_time(appointment_time: str, appointment_type: str) -> str:
    """
    Calculate arrival time based on appointment type.
    NEW: 30 min early, ESTABLISHED: 10 min early
    """
    try:
        time_obj = datetime.strptime(appointment_time, '%H:%M')
        minutes_early = 30 if appointment_type == 'NEW' else 10
        arrival = time_obj - timedelta(minutes=minutes_early)
        return arrival.strftime('%H:%M')
    except ValueError:
        # Fallback if time format is wrong
        return appointment_time


def format_date_for_api(iso_date: str) -> str:
    """Convert ISO date (2024-08-12) to API format (8/12/24)"""
    try:
        date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
        return date_obj.strftime('%-m/%d/%y')  # %-m removes leading zero
    except ValueError:
        return iso_date


def format_time_for_api(time_24hr: str) -> str:
    """Convert 24hr time (14:30) to 12hr format (2:30pm)"""
    try:
        time_obj = datetime.strptime(time_24hr, '%H:%M')
        return time_obj.strftime('%-I:%M%p').lower()  # 2:30pm
    except ValueError:
        return time_24hr
