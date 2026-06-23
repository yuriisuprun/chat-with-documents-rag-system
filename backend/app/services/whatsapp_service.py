"""WhatsApp API integration service."""

import json
import logging
from typing import Optional, Dict, Any

import requests
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)


class WhatsAppService:
    """Service for WhatsApp Business Cloud API integration."""

    def __init__(self):
        """
        Initialize WhatsApp service.
        
        Uses Meta WhatsApp Business Cloud API v18.0
        Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/
        """
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        # Using latest stable API version
        self.base_url = "https://graph.instagram.com/v18.0"
        self.api_version = "18.0"

    def send_message(
        self,
        phone_number: str,
        message_content: str,
        conversation_id: str,
        tenant_id: str = None,
    ) -> bool:
        """
        Send text message via WhatsApp Business Cloud API.
        
        Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
        
        Args:
            phone_number: Recipient phone number (e.g., +1234567890)
            message_content: Message text to send
            conversation_id: Conversation ID for tracking
            tenant_id: Tenant ID
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.access_token or not self.phone_number_id:
            logger.warning(
                "whatsapp_credentials_missing",
                operation="send_message"
            )
            return False

        try:
            # WhatsApp Business API endpoint
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            # WhatsApp API payload format
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number.lstrip("+"),  # API expects phone without +
                "type": "text",
                "text": {
                    "preview_url": True,
                    "body": message_content,
                },
            }

            logger.debug(
                "whatsapp_send_message_started",
                conversation_id=conversation_id,
                recipient_phone=phone_number,
                message_length=len(message_content),
            )
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Extract message ID from response
                messages = result.get("messages", [])
                if messages:
                    message_id = messages[0].get("id")
                    logger.info(
                        "whatsapp_message_sent_successfully",
                        conversation_id=conversation_id,
                        whatsapp_message_id=message_id,
                        recipient_phone=phone_number,
                    )
                    return True
                else:
                    logger.error(
                        "whatsapp_send_no_message_id",
                        conversation_id=conversation_id,
                        response=result,
                    )
                    return False
            else:
                logger.error(
                    "whatsapp_send_api_error",
                    conversation_id=conversation_id,
                    status_code=response.status_code,
                    response_text=response.text,
                    recipient_phone=phone_number,
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(
                "whatsapp_send_request_error",
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True,
            )
            return False
        except Exception as e:
            logger.error(
                "whatsapp_send_unexpected_error",
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True,
            )
            return False

    def verify_webhook_token(self, token: str) -> bool:
        """
        Verify webhook token.
        
        Args:
            token: Token to verify
            
        Returns:
            True if token matches
        """
        return token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN

    def parse_webhook_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming webhook message from WhatsApp Business Cloud API.
        
        Expected webhook payload structure from Meta:
        https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
        
        Args:
            data: Webhook payload from WhatsApp Business API
            
        Returns:
            Parsed message dict with normalized keys or None if invalid
        """
        try:
            # Navigate WhatsApp webhook structure
            entries = data.get("entry", [])
            if not entries:
                logger.debug("webhook_no_entries")
                return None
            
            entry = entries[0]
            changes = entry.get("changes", [])
            if not changes:
                logger.debug("webhook_no_changes")
                return None
            
            change = changes[0]
            value = change.get("value", {})
            
            # Check for messages in the value
            messages = value.get("messages", [])
            if not messages:
                logger.debug("webhook_no_messages_possible_status_update")
                return None

            message = messages[0]
            message_id = message.get("id")
            sender_phone = message.get("from")
            timestamp = message.get("timestamp")
            message_type = message.get("type")  # text, audio, image, document, location, etc.
            
            logger.info(
                "whatsapp_webhook_message_parsed",
                message_type=message_type,
                sender_phone=sender_phone,
                message_id=message_id,
            )
            
            # Build normalized message dict
            parsed_msg = {
                "message_id": message_id,
                "from": sender_phone,  # Phone number without +
                "timestamp": timestamp,
                "type": message_type,
            }
            
            # Extract content based on message type
            if message_type == "text":
                text_data = message.get("text", {})
                parsed_msg["text"] = text_data.get("body", "")
            elif message_type == "audio":
                parsed_msg["audio"] = message.get("audio", {})
            elif message_type == "image":
                parsed_msg["image"] = message.get("image", {})
            elif message_type == "document":
                parsed_msg["document"] = message.get("document", {})
            elif message_type == "location":
                parsed_msg["location"] = message.get("location", {})
            elif message_type == "button":
                parsed_msg["button"] = message.get("button", {})
            elif message_type == "interactive":
                parsed_msg["interactive"] = message.get("interactive", {})
            
            return parsed_msg

        except (KeyError, IndexError, TypeError) as e:
            logger.error(
                "whatsapp_webhook_parse_error",
                error=str(e),
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                "whatsapp_webhook_unexpected_error",
                error=str(e),
                exc_info=True,
            )
            return None

    def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get media URL from media ID via WhatsApp Business API.
        
        Reference: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media
        
        Args:
            media_id: WhatsApp media object ID (from message payload)
            
        Returns:
            Direct URL to download media file, or None if error
        """
        if not self.access_token:
            logger.warning("Access token not configured - cannot retrieve media URL")
            return None

        try:
            # Query media endpoint to get download URL
            url = f"{self.base_url}/{media_id}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
            }
            
            logger.info(f"Retrieving media URL from WhatsApp API: {media_id}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                media_url = data.get("url")
                if media_url:
                    logger.info(f"Retrieved media URL from WhatsApp API")
                    return media_url
                else:
                    logger.error(f"No URL in WhatsApp media response: {data}")
                    return None
            else:
                logger.error(
                    f"WhatsApp media API failed: {response.status_code} - {response.text}"
                )
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error retrieving WhatsApp media URL: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting media URL from WhatsApp API: {str(e)}")
            return None

    def send_template_message(
        self,
        phone_number: str,
        template_name: str,
        parameters: Optional[list] = None,
    ) -> bool:
        """
        Send templated WhatsApp message (for future use).
        
        Args:
            phone_number: Recipient phone number
            template_name: WhatsApp template name
            parameters: Template parameters
            
        Returns:
            True if successful
        """
        if not self.access_token or not self.phone_number_id:
            return False

        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number.lstrip("+"),
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "en",
                    },
                },
            }

            if parameters:
                payload["template"]["parameters"] = {
                    "body": {
                        "parameters": parameters,
                    }
                }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error sending template message: {str(e)}")
            return False

    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark message as read.
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            True if successful
        """
        if not self.access_token or not self.phone_number_id:
            return False

        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False
