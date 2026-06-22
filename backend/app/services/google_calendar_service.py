"""Google Calendar integration service."""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for Google Calendar integration."""

    def __init__(self, credentials_json: str):
        """
        Initialize Google Calendar service.
        
        Args:
            credentials_json: JSON string containing Google service account credentials
        """
        self.credentials_json = credentials_json
        self._service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Calendar API service."""
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            # Parse credentials
            if isinstance(self.credentials_json, str):
                creds_dict = json.loads(self.credentials_json)
            else:
                creds_dict = self.credentials_json

            # Create credentials with Calendar scope
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/calendar.events'
                ]
            )

            # Build service
            self._service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {str(e)}")
            raise

    def create_event(
        self,
        summary: str,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 30,
        attendee_email: Optional[str] = None,
        attendee_name: Optional[str] = None,
        calendar_id: str = "primary",
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Create a Google Calendar event.
        
        Args:
            summary: Event title
            description: Event description
            start_time: Event start time (datetime object). If None, uses current time + 1 hour
            duration_minutes: Event duration in minutes
            attendee_email: Attendee email address
            attendee_name: Attendee display name
            calendar_id: Calendar ID (default: primary)
            timezone: Timezone for the event
            
        Returns:
            Dictionary with event details:
            {
                "id": str,
                "summary": str,
                "start": str (ISO format),
                "end": str (ISO format),
                "html_link": str,
                "description": str
            }
        """
        try:
            # Set default start time if not provided
            if start_time is None:
                start_time = datetime.utcnow() + timedelta(hours=1)

            end_time = start_time + timedelta(minutes=duration_minutes)

            # Build event object
            event = {
                "summary": summary,
                "description": description or "",
                "start": {
                    "dateTime": start_time.isoformat() + "Z",
                    "timeZone": timezone
                },
                "end": {
                    "dateTime": end_time.isoformat() + "Z",
                    "timeZone": timezone
                },
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},  # 1 day before
                        {"method": "popup", "minutes": 30}  # 30 minutes before
                    ]
                }
            }

            # Add attendee if provided
            if attendee_email:
                event["attendees"] = [
                    {
                        "email": attendee_email,
                        "displayName": attendee_name or "Guest",
                        "responseStatus": "needsAction"
                    }
                ]

            # Insert event
            result = self._service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendNotifications=True
            ).execute()

            logger.info(f"Google Calendar event created: {result.get('id')}")

            return {
                "id": result.get("id"),
                "summary": result.get("summary"),
                "start": result.get("start", {}).get("dateTime"),
                "end": result.get("end", {}).get("dateTime"),
                "html_link": result.get("htmlLink"),
                "description": result.get("description")
            }

        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {str(e)}")
            raise

    def get_free_slots(
        self,
        date: datetime,
        duration_minutes: int = 30,
        working_hours_start: int = 9,
        working_hours_end: int = 17,
        calendar_id: str = "primary"
    ) -> list:
        """
        Get available time slots for a specific date.
        
        Args:
            date: Date to check for availability
            duration_minutes: Required duration for the slot
            working_hours_start: Working hours start (hour in 24-format)
            working_hours_end: Working hours end (hour in 24-format)
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            List of available time slots:
            [
                {"start": "HH:MM", "end": "HH:MM"},
                ...
            ]
        """
        try:
            # Query events for the date
            start_of_day = datetime.combine(date.date(), datetime.min.time())
            end_of_day = datetime.combine(date.date(), datetime.max.time())

            events_result = self._service.events().list(
                calendarId=calendar_id,
                timeMin=start_of_day.isoformat() + "Z",
                timeMax=end_of_day.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])

            # Extract busy times
            busy_times = []
            for event in events:
                start = event.get("start", {}).get("dateTime")
                end = event.get("end", {}).get("dateTime")
                if start and end:
                    busy_times.append({
                        "start": datetime.fromisoformat(start.replace("Z", "+00:00")),
                        "end": datetime.fromisoformat(end.replace("Z", "+00:00"))
                    })

            # Generate free slots
            free_slots = self._calculate_free_slots(
                date,
                busy_times,
                duration_minutes,
                working_hours_start,
                working_hours_end
            )

            return free_slots

        except Exception as e:
            logger.error(f"Error getting free slots: {str(e)}")
            raise

    def _calculate_free_slots(
        self,
        date: datetime,
        busy_times: list,
        duration_minutes: int,
        working_hours_start: int,
        working_hours_end: int
    ) -> list:
        """Calculate free time slots based on busy times and working hours."""
        free_slots = []

        # Create 30-minute intervals for the working day
        current_time = datetime.combine(date.date(), datetime.min.time()).replace(
            hour=working_hours_start
        )
        end_of_day = datetime.combine(date.date(), datetime.min.time()).replace(
            hour=working_hours_end
        )

        while current_time + timedelta(minutes=duration_minutes) <= end_of_day:
            slot_end = current_time + timedelta(minutes=duration_minutes)

            # Check if slot is free (not occupied by any event)
            is_free = True
            for busy_time in busy_times:
                if not (slot_end <= busy_time["start"] or current_time >= busy_time["end"]):
                    is_free = False
                    break

            if is_free:
                free_slots.append({
                    "start": current_time.strftime("%H:%M"),
                    "end": slot_end.strftime("%H:%M")
                })

            current_time += timedelta(minutes=30)

        return free_slots

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> bool:
        """
        Delete a Google Calendar event.
        
        Args:
            event_id: Event ID to delete
            calendar_id: Calendar ID (default: primary)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"Event {event_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return False

    def update_event(
        self,
        event_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update a Google Calendar event.
        
        Args:
            event_id: Event ID to update
            **kwargs: Fields to update (summary, description, start, end, etc.)
            
        Returns:
            Updated event details
        """
        try:
            # Get existing event
            event = self._service.events().get(
                calendarId="primary",
                eventId=event_id
            ).execute()

            # Update fields
            for key, value in kwargs.items():
                event[key] = value

            # Update event
            result = self._service.events().update(
                calendarId="primary",
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Event {event_id} updated successfully")
            return result

        except Exception as e:
            logger.error(f"Error updating event: {str(e)}")
            raise
