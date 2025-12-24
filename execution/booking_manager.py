"""
Booking Manager - Handles all appointment CRUD operations
Deterministic booking system for dental practice appointments.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BookingManager:
    """Manages appointment bookings for dental practice."""
    
    def __init__(self, bookings_file: str = ".tmp/bookings.json"):
        """
        Initialize booking manager.
        
        Args:
            bookings_file: Path to JSON file storing bookings
        """
        self.bookings_file = Path(bookings_file)
        self.bookings_file.parent.mkdir(parents=True, exist_ok=True)
        self.bookings = self._load_bookings()
        
        # Default office hours (can be configured via .env)
        self.office_hours = {
            "monday": {"start": "09:00", "end": "17:00"},
            "tuesday": {"start": "09:00", "end": "17:00"},
            "wednesday": {"start": "09:00", "end": "17:00"},
            "thursday": {"start": "09:00", "end": "17:00"},
            "friday": {"start": "09:00", "end": "17:00"},
            "saturday": {"start": "09:00", "end": "13:00"},
            "sunday": {"start": None, "end": None},  # Closed
        }
        
        # Appointment duration in minutes (default 30)
        self.appointment_duration = int(os.getenv("APPOINTMENT_DURATION_MINUTES", "30"))
    
    def _load_bookings(self) -> List[Dict]:
        """Load bookings from JSON file."""
        if self.bookings_file.exists():
            try:
                with open(self.bookings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_bookings(self):
        """Save bookings to JSON file."""
        with open(self.bookings_file, 'w', encoding='utf-8') as f:
            json.dump(self.bookings, f, indent=2, default=str)
    
    def create_booking(
        self,
        patient_name: str,
        phone: str,
        email: Optional[str] = None,
        appointment_datetime: str = None,
        reason: Optional[str] = None,
        status: str = "confirmed"
    ) -> Dict:
        """
        Create a new appointment booking.
        
        Args:
            patient_name: Patient's full name
            phone: Patient's phone number
            email: Patient's email (optional)
            appointment_datetime: ISO format datetime string (YYYY-MM-DD HH:MM)
            reason: Reason for visit (optional)
            status: Booking status (confirmed, pending, cancelled)
        
        Returns:
            Dictionary with booking details including confirmation number
        """
        if not appointment_datetime:
            raise ValueError("appointment_datetime is required")
        
        # Parse datetime
        try:
            dt = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))
        except ValueError:
            # Try alternative format
            dt = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")
        
        # Check if slot is available
        if not self.is_slot_available(appointment_datetime):
            raise ValueError(f"Time slot {appointment_datetime} is not available")
        
        # Generate confirmation number
        confirmation_number = f"APT{dt.strftime('%Y%m%d')}{len(self.bookings) + 1:04d}"
        
        booking = {
            "id": len(self.bookings) + 1,
            "confirmation_number": confirmation_number,
            "patient_name": patient_name,
            "phone": phone,
            "email": email,
            "appointment_datetime": appointment_datetime,
            "datetime_iso": dt.isoformat(),
            "reason": reason,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.bookings.append(booking)
        self._save_bookings()
        
        return booking
    
    def get_booking(self, confirmation_number: str) -> Optional[Dict]:
        """Get booking by confirmation number."""
        for booking in self.bookings:
            if booking.get("confirmation_number") == confirmation_number:
                return booking
        return None
    
    def get_booking_by_phone(self, phone: str) -> List[Dict]:
        """Get all bookings for a phone number."""
        return [b for b in self.bookings if b.get("phone") == phone and b.get("status") != "cancelled"]
    
    def update_booking(
        self,
        confirmation_number: str,
        appointment_datetime: str = None,
        reason: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Update an existing booking.
        
        Args:
            confirmation_number: Booking confirmation number
            appointment_datetime: New appointment datetime (if rescheduling)
            reason: Updated reason for visit
            status: Updated status
        
        Returns:
            Updated booking dictionary or None if not found
        """
        booking = self.get_booking(confirmation_number)
        if not booking:
            return None
        
        # Check new slot availability if rescheduling
        if appointment_datetime and appointment_datetime != booking.get("appointment_datetime"):
            if not self.is_slot_available(appointment_datetime, exclude_confirmation=confirmation_number):
                raise ValueError(f"Time slot {appointment_datetime} is not available")
            
            try:
                dt = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))
            except ValueError:
                dt = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")
            
            booking["appointment_datetime"] = appointment_datetime
            booking["datetime_iso"] = dt.isoformat()
        
        if reason is not None:
            booking["reason"] = reason
        if status is not None:
            booking["status"] = status
        
        booking["updated_at"] = datetime.now().isoformat()
        self._save_bookings()
        
        return booking
    
    def cancel_booking(self, confirmation_number: str) -> bool:
        """Cancel a booking."""
        booking = self.update_booking(confirmation_number, status="cancelled")
        return booking is not None
    
    def is_slot_available(self, appointment_datetime: str, exclude_confirmation: Optional[str] = None) -> bool:
        """
        Check if a time slot is available.
        
        Args:
            appointment_datetime: ISO format datetime string
            exclude_confirmation: Confirmation number to exclude from conflict check (for updates)
        
        Returns:
            True if slot is available, False otherwise
        """
        try:
            dt = datetime.fromisoformat(appointment_datetime.replace('Z', '+00:00'))
        except ValueError:
            dt = datetime.strptime(appointment_datetime, "%Y-%m-%d %H:%M")
        
        # Check office hours
        day_name = dt.strftime("%A").lower()
        if day_name not in self.office_hours or not self.office_hours[day_name]["start"]:
            return False
        
        office_start = datetime.strptime(self.office_hours[day_name]["start"], "%H:%M").time()
        office_end = datetime.strptime(self.office_hours[day_name]["end"], "%H:%M").time()
        appointment_time = dt.time()
        
        if appointment_time < office_start or appointment_time >= office_end:
            return False
        
        # Check for conflicts with existing bookings
        slot_end = dt + timedelta(minutes=self.appointment_duration)
        
        for booking in self.bookings:
            if booking.get("status") == "cancelled":
                continue
            if exclude_confirmation and booking.get("confirmation_number") == exclude_confirmation:
                continue
            
            try:
                existing_dt = datetime.fromisoformat(booking.get("datetime_iso", "").replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                continue
            
            existing_end = existing_dt + timedelta(minutes=self.appointment_duration)
            
            # Check for overlap
            if (dt < existing_end and slot_end > existing_dt):
                return False
        
        return True
    
    def get_available_slots(
        self,
        date: str,
        start_time: str = "09:00",
        end_time: str = "17:00"
    ) -> List[str]:
        """
        Get available appointment slots for a given date.
        
        Args:
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
        
        Returns:
            List of available time slots in HH:MM format
        """
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return []
        
        day_name = target_date.strftime("%A").lower()
        if day_name not in self.office_hours or not self.office_hours[day_name]["start"]:
            return []
        
        # Use office hours if not specified
        if start_time == "09:00" and end_time == "17:00":
            start_time = self.office_hours[day_name]["start"]
            end_time = self.office_hours[day_name]["end"]
        
        slots = []
        current = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
        
        while current + timedelta(minutes=self.appointment_duration) <= end:
            slot_str = current.strftime("%Y-%m-%d %H:%M")
            if self.is_slot_available(slot_str):
                slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=self.appointment_duration)
        
        return slots
    
    def get_bookings_by_date(self, date: str) -> List[Dict]:
        """Get all bookings for a specific date."""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return []
        
        result = []
        for booking in self.bookings:
            if booking.get("status") == "cancelled":
                continue
            try:
                booking_dt = datetime.fromisoformat(booking.get("datetime_iso", "").replace('Z', '+00:00'))
                if booking_dt.date() == target_date:
                    result.append(booking)
            except (ValueError, AttributeError):
                continue
        
        return sorted(result, key=lambda x: x.get("datetime_iso", ""))


if __name__ == "__main__":
    # Example usage
    manager = BookingManager()
    
    # Create a booking
    booking = manager.create_booking(
        patient_name="John Doe",
        phone="555-1234",
        email="john@example.com",
        appointment_datetime="2025-12-23 10:00",
        reason="Regular checkup"
    )
    print(f"Created booking: {booking['confirmation_number']}")
    
    # Get available slots
    slots = manager.get_available_slots("2025-12-23")
    print(f"Available slots on 2025-12-23: {slots[:5]}")

