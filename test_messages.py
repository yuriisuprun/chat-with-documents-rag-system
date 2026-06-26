#!/usr/bin/env python3
"""
🧪 WhatsApp Test Message Sender

Send test messages to verify the WhatsApp auto-assistant system works correctly.
This uses the /api/v1/webhooks/whatsapp/test-message endpoint.

Usage:
    python test_messages.py                    # Run default sequence
    python test_messages.py --phone +15551234567 --message "Hello"  # Single message
    python test_messages.py --sequence multilang  # Multi-language sequence
    python test_messages.py --sequence multiphone # Multi-phone sequence

Requirements:
    - Backend running at http://localhost:8000
    - Install: pip install requests
"""

import requests
import time
import argparse
import sys
from typing import List, Tuple


BASE_URL = "http://localhost:8000/api/v1/webhooks/whatsapp/test-message"

# Test sequences
SEQUENCES = {
    "basic": [
        ("Hello", "+15551234567"),
        ("I need help", "+15551234567"),
        ("Can you schedule an appointment?", "+15551234567"),
    ],
    "multilang": [
        ("What are your office hours?", "+15551234567"),  # English
        ("Какие у вас часы работы?", "+15552222222"),     # Russian (different phone)
        ("Quali sono i vostri orari?", "+15553333333"),   # Italian (different phone)
    ],
    "multiphone": [
        ("Hello from first client", "+15551234567"),
        ("Hello from second client", "+15559876543"),
        ("Back to first client", "+15551234567"),
    ],
    "intents": [
        ("Hello, how are you?", "+15551234567"),           # greeting
        ("How much do you charge?", "+15552222222"),       # pricing inquiry
        ("Can I book an appointment tomorrow at 2pm?", "+15553333333"),  # appointment
    ],
}


def send_test_message(message_text: str, phone_number: str, timeout: int = 10) -> dict:
    """
    Send a single test message.
    
    Args:
        message_text: The message to send
        phone_number: Phone number (with or without +)
        timeout: Request timeout in seconds
        
    Returns:
        Response JSON or error dict
    """
    try:
        response = requests.post(
            BASE_URL,
            params={
                "phone_number": phone_number,
                "message_text": message_text
            },
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": f"Cannot connect to {BASE_URL}",
            "hint": "Is the backend running? Try: docker-compose up -d backend"
        }
    except requests.exceptions.Timeout:
        return {"status": "error", "message": f"Request timed out after {timeout}s"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_sequence(messages: List[Tuple[str, str]], delay_between: int = 2):
    """
    Run a sequence of test messages.
    
    Args:
        messages: List of (message_text, phone_number) tuples
        delay_between: Seconds to wait between messages
    """
    print(f"\n📱 Running sequence with {len(messages)} messages\n")
    
    for i, (message_text, phone_number) in enumerate(messages, 1):
        print(f"[{i}/{len(messages)}] Sending to {phone_number}")
        print(f"   Message: {message_text}")
        
        result = send_test_message(message_text, phone_number)
        
        if result.get("status") == "ok":
            print(f"   ✅ Success!")
            print(f"   Conversation ID: {result.get('conversation_id')}")
            print(f"   Detected Language: {result.get('detected_language')}")
            print(f"   Detected Intent: {result.get('detected_intent')}")
            print(f"   Auto-reply in: {result.get('auto_reply_in_seconds')}s")
        else:
            print(f"   ❌ Error: {result.get('message')}")
            if "hint" in result:
                print(f"   💡 Hint: {result.get('hint')}")
        
        if i < len(messages):
            print(f"   (waiting {delay_between}s before next message...)\n")
            time.sleep(delay_between)
        else:
            print()


def main():
    """Main entry point."""
    global BASE_URL
    
    parser = argparse.ArgumentParser(
        description="Send test messages to WhatsApp auto-assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                                # Basic sequence
  %(prog)s --sequence multilang                          # Multi-language
  %(prog)s --sequence multiphone                         # Multi-phone
  %(prog)s --phone +15551234567 --message "Hello"        # Single message
  %(prog)s --sequence basic --delay 5                    # Wait 5s between messages
        """
    )
    
    parser.add_argument(
        "--sequence",
        choices=list(SEQUENCES.keys()),
        default="basic",
        help="Test sequence to run (default: basic)"
    )
    
    parser.add_argument(
        "--phone",
        help="Phone number for single message (overrides sequence)"
    )
    
    parser.add_argument(
        "--message",
        help="Message text for single message"
    )
    
    parser.add_argument(
        "--delay",
        type=int,
        default=2,
        help="Seconds to wait between messages (default: 2)"
    )
    
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help="Backend URL (default: http://localhost:8000/api/v1/webhooks/whatsapp/test-message)"
    )
    
    args = parser.parse_args()
    
    # Update URL if provided
    BASE_URL = args.url
    
    print("\n" + "="*60)
    print("🧪 WhatsApp Test Message Sender")
    print("="*60)
    
    # Single message mode
    if args.phone and args.message:
        print(f"\n📱 Sending single message")
        print(f"   Phone: {args.phone}")
        print(f"   Message: {args.message}\n")
        
        result = send_test_message(args.message, args.phone)
        
        if result.get("status") == "ok":
            print("✅ Message sent successfully!")
            print(f"\nResponse:")
            for key, value in result.items():
                if key != "status":
                    print(f"  {key}: {value}")
        else:
            print("❌ Failed to send message")
            print(f"\nError: {result.get('message')}")
            if "hint" in result:
                print(f"Hint: {result.get('hint')}")
            return 1
    
    # Sequence mode
    else:
        sequence_name = args.sequence
        messages = SEQUENCES.get(sequence_name)
        
        if not messages:
            print(f"\n❌ Unknown sequence: {sequence_name}")
            print(f"Available: {', '.join(SEQUENCES.keys())}")
            return 1
        
        print(f"\n📋 Sequence: {sequence_name}")
        print(f"   Messages: {len(messages)}")
        print(f"   Delay between: {args.delay}s")
        
        run_sequence(messages, delay_between=args.delay)
        
        print("✅ Test sequence completed!")
        print("\n📊 Next steps:")
        print("   1. Wait 2-5 minutes for auto-replies")
        print("   2. Check dashboard: http://localhost:3000")
        print("   3. Verify all messages appear")
        print("   4. Check logs: docker-compose logs backend | grep -i test")
    
    print("\n" + "="*60 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
