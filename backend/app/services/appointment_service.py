"""Appointment scheduling service with feature flag support."""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests

from app.config import settings
from app.services.language_service import LanguageService

logger = logging.getLogger(__name__)


class AppointmentService:
    """Service for automatic appointment scheduling."""

    def __init__(self):
        """Initialize appointment service."""
        self.enabled = settings.TENANT_ENABLE_AUTO_APPOINTMENT
        self.api_type = settings.TENANT_APPOINTMENT_API_TYPE
        self.api_key = settings.TENANT_APPOINTMENT_API_KEY
        self.api_url = settings.TENANT_APPOINTMENT_API_URL
        self.default_duration = settings.TENANT_APPOINTMENT_DEFAULT_DURATION
        self.confirmation_message = settings.TENANT_APPOINTMENT_CONFIRMATION_MESSAGE
        self.language_service = LanguageService()

    def is_enabled(self) -> bool:
        """
        Check if appointment automation is enabled.
        
        Returns:
            True if feature is enabled, False otherwise
        """
        return self.enabled

    def can_create_appointment(self) -> bool:
        """
        Check if all required conditions for appointment creation are met.
        
        Returns:
            True if appointment creation is possible
        """
        if not self.enabled:
            logger.debug("Appointment automation is disabled")
            return False

        if not self.api_type:
            logger.warning("Appointment API type not configured")
            return False

        # Calendly requires API key but uses their hosted interface
        if self.api_type == "calendly":
            return True

        # Other types require API URL and key
        if not self.api_url or not self.api_key:
            logger.warning("Appointment API URL or key not configured")
            return False

        return True

    def create_appointment(
        self,
        client_phone: str,
        client_name: Optional[str] = None,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create appointment with configured calendar service.
        
        Args:
            client_phone: Client phone number
            client_name: Client name (optional)
            preferred_date: Preferred date (YYYY-MM-DD format)
            preferred_time: Preferred time (HH:MM format)
            notes: Additional notes for appointment
            
        Returns:
            Dictionary with appointment details:
            {
                "appointment_id": str,
                "client_phone": str,
                "scheduled_at": str or None,
                "confirmation_url": str or None,
                "status": str,  # pending, confirmed, failed
                "message": str
            }
        """
        if not self.can_create_appointment():
            return {
                "appointment_id": None,
                "client_phone": client_phone,
                "scheduled_at": None,
                "confirmation_url": None,
                "status": "failed",
                "message": "Appointment automation is not configured"
            }

        try:
            if self.api_type == "calendly":
                return self._create_calendly_appointment(
                    client_phone, client_name, notes
                )
            elif self.api_type == "google_calendar":
                return self._create_google_calendar_appointment(
                    client_phone, client_name, preferred_date, preferred_time, notes
                )
            elif self.api_type == "custom":
                return self._create_custom_appointment(
                    client_phone, client_name, preferred_date, preferred_time, notes
                )
            else:
                raise ValueError(f"Unknown appointment API type: {self.api_type}")

        except Exception as e:
            logger.error(f"Error creating appointment: {str(e)}", exc_info=True)
            return {
                "appointment_id": None,
                "client_phone": client_phone,
                "scheduled_at": None,
                "confirmation_url": None,
                "status": "failed",
                "message": f"Failed to create appointment: {str(e)}"
            }

    def _create_calendly_appointment(
        self,
        client_phone: str,
        client_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create appointment using Calendly (generates booking link).
        
        For Calendly, we don't actually create appointments directly,
        but return the Calendly link for the client to book.
        """
        logger.info(f"Creating Calendly appointment for {client_phone}")

        booking_url = settings.TENANT_BOOKING_URL

        return {
            "appointment_id": f"calendly_{client_phone}_{int(datetime.utcnow().timestamp())}",
            "client_phone": client_phone,
            "scheduled_at": None,
            "confirmation_url": booking_url,
            "status": "pending",
            "message": (
                self.confirmation_message or
                f"I've prepared your booking link. Please visit {booking_url} to schedule your appointment at a time that works for you."
            )
        }

    def _create_google_calendar_appointment(
        self,
        client_phone: str,
        client_name: Optional[str] = None,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create appointment using Google Calendar API.
        
        Requires TENANT_APPOINTMENT_API_KEY with Google Calendar credentials.
        """
        logger.info(f"Creating Google Calendar appointment for {client_phone}")

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            # Parse credentials from API key (should be JSON)
            if isinstance(self.api_key, str):
                creds_dict = json.loads(self.api_key)
            else:
                creds_dict = self.api_key

            # Create credentials
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/calendar']
            )

            # Build service
            service = build('calendar', 'v3', credentials=credentials)

            # Create event
            event = {
                "summary": f"Consultation - {client_name or client_phone}",
                "description": f"Client Phone: {client_phone}\nNotes: {notes or 'N/A'}",
                "attendees": [
                    {"email": client_phone.replace("+", ""), "displayName": client_name or "Client"}
                ],
            }

            # Set time if provided
            if preferred_date and preferred_time:
                try:
                    start_dt = datetime.fromisoformat(f"{preferred_date}T{preferred_time}")
                    end_dt = start_dt + timedelta(minutes=self.default_duration)

                    event["start"] = {
                        "dateTime": start_dt.isoformat(),
                        "timeZone": "UTC"
                    }
                    event["end"] = {
                        "dateTime": end_dt.isoformat(),
                        "timeZone": "UTC"
                    }
                except ValueError:
                    logger.warning(f"Invalid date/time format: {preferred_date} {preferred_time}")

            # Insert event
            result = service.events().insert(calendarId='primary', body=event).execute()

            return {
                "appointment_id": result.get("id"),
                "client_phone": client_phone,
                "scheduled_at": result.get("start", {}).get("dateTime"),
                "confirmation_url": result.get("htmlLink"),
                "status": "confirmed",
                "message": (
                    self.confirmation_message or
                    f"Your appointment has been scheduled! You'll receive a confirmation at {client_phone}."
                )
            }

        except Exception as e:
            logger.error(f"Google Calendar error: {str(e)}")
            raise

    def _create_custom_appointment(
        self,
        client_phone: str,
        client_name: Optional[str] = None,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create appointment using custom API endpoint.
        
        Requires TENANT_APPOINTMENT_API_URL and TENANT_APPOINTMENT_API_KEY.
        """
        logger.info(f"Creating custom appointment for {client_phone} at {self.api_url}")

        payload = {
            "client_phone": client_phone,
            "client_name": client_name,
            "preferred_date": preferred_date,
            "preferred_time": preferred_time,
            "notes": notes,
            "duration_minutes": self.default_duration,
            "professional_name": settings.TENANT_PROFESSIONAL_NAME,
            "business_name": settings.TENANT_BUSINESS_NAME,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code not in [200, 201]:
                logger.error(f"Custom API error: {response.status_code} - {response.text}")
                raise Exception(f"API returned {response.status_code}")

            result = response.json()

            return {
                "appointment_id": result.get("appointment_id"),
                "client_phone": client_phone,
                "scheduled_at": result.get("scheduled_at"),
                "confirmation_url": result.get("confirmation_url"),
                "status": result.get("status", "pending"),
                "message": (
                    self.confirmation_message or
                    result.get("message", "Appointment request submitted successfully.")
                )
            }

        except Exception as e:
            logger.error(f"Custom API error: {str(e)}")
            raise

    def extract_appointment_info(self, message: str, language: str = "en") -> Dict[str, Optional[str]]:
        """
        Extract appointment details from natural language with language awareness.
        
        Args:
            message: Client message
            language: ISO 639-1 language code
            
        Returns:
            Dictionary with extracted info:
            {
                "client_name": str or None,
                "preferred_date": str or None,
                "preferred_time": str or None,
                "notes": str or None
            }
        """
        info = {
            "client_name": None,
            "preferred_date": None,
            "preferred_time": None,
            "notes": message
        }

        # Use language service for language-aware pattern extraction
        patterns = self.language_service.extract_date_time_patterns(message, language)
        
        # Extract dates and times using language-specific patterns
        if patterns.get("dates"):
            # Use the first detected date
            date_str = patterns["dates"][0]
            try:
                # Normalize to YYYY-MM-DD format
                info["preferred_date"] = self._normalize_date(date_str, language)
            except Exception as e:
                logger.debug(f"Could not normalize date '{date_str}': {str(e)}")
        
        if patterns.get("times"):
            # Use the first detected time
            time_str = patterns["times"][0]
            try:
                info["preferred_time"] = self._normalize_time(time_str, language)
            except Exception as e:
                logger.debug(f"Could not normalize time '{time_str}': {str(e)}")
        
        return info

    def _normalize_date(self, date_str: str, language: str) -> str:
        """
        Normalize date string to YYYY-MM-DD format based on language.
        
        Args:
            date_str: Date string to normalize
            language: ISO 639-1 language code
            
        Returns:
            Normalized date in YYYY-MM-DD format
        """
        from dateutil import parser
        
        try:
            # Try to parse with language hints
            if language == "ru":
                # Russian month names
                russian_months = {
                    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
                    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
                    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
                }
                for month_name, month_num in russian_months.items():
                    date_str = date_str.replace(month_name, str(month_num))
            
            elif language == "it":
                # Italian month names
                italian_months = {
                    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
                    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
                    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
                }
                for month_name, month_num in italian_months.items():
                    date_str = date_str.replace(month_name, str(month_num))
            
            # Parse the date
            parsed_date = parser.parse(date_str, dayfirst=(language != "en"))
            return parsed_date.strftime("%Y-%m-%d")
        
        except Exception as e:
            logger.debug(f"Date normalization failed: {str(e)}")
            raise

    def _normalize_time(self, time_str: str, language: str) -> str:
        """
        Normalize time string to HH:MM format based on language.
        
        Args:
            time_str: Time string to normalize
            language: ISO 639-1 language code
            
        Returns:
            Normalized time in HH:MM format
        """
        import re
        
        try:
            # Remove language-specific time markers
            time_str = time_str.lower()
            
            if language == "ru":
                # Remove Russian time markers
                time_str = re.sub(r'\s*(часов|часа|час)\b', '', time_str)
            elif language == "it":
                # Remove Italian time markers
                time_str = re.sub(r'\s*(di mattina|del pomeriggio|di sera)\b', '', time_str)
            
            # Extract hour and minute
            time_pattern = r'(\d{1,2}):?(\d{0,2})'
            match = re.search(time_pattern, time_str)
            
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2) or "0") if match.group(2) else 0
                
                # Handle 12-hour format if present
                if "am" in time_str or "pm" in time_str:
                    is_pm = "pm" in time_str
                    if is_pm and hour != 12:
                        hour += 12
                    elif not is_pm and hour == 12:
                        hour = 0
                
                return f"{hour:02d}:{minute:02d}"
            
            raise ValueError("Could not extract time")
        
        except Exception as e:
            logger.debug(f"Time normalization failed: {str(e)}")
            raise
