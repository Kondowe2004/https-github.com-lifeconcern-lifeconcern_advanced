# core/utils.py

from django.core.mail import EmailMessage, get_connection
from django.conf import settings
import sys
import socket

def send_email_alert(subject, message, recipient_list):
    """
    Send an email alert to a list of recipients.
    Handles network unreachable errors gracefully.
    """

    # Ensure subject is tagged as an update
    if not subject.lower().startswith("[update]"):
        subject = f"[Update] {subject}"

    try:
        # Optional: test network connectivity to Gmail SMTP
        try:
            socket.create_connection(("smtp.gmail.com", 587), timeout=3)
        except OSError:
            raise ConnectionError("Network unreachable — cannot send email.")

        # Use Django's email backend
        connection = get_connection(fail_silently=False)
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "updates@yourdomain.com"),
            to=recipient_list,
            headers={
                "Precedence": "bulk",
                "X-Auto-Response-Suppress": "All",
                "List-Id": "LifeConcern Updates <updates.yourdomain.com>",
            },
            connection=connection,
        )
        email.send(fail_silently=False)

    except (ConnectionError, OSError) as e:
        # Handles free PythonAnywhere blocking or slow network
        print("⚠️ Email sending skipped:", e, file=sys.stderr)
    except Exception as e:
        # Catch any other email-related errors without crashing
        print("⚠️ Failed to send email alert:", e, file=sys.stderr)


def safe_int(value, default=0):
    """
    Safely convert a value to an integer.
    Returns default if conversion fails.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
