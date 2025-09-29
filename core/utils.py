from django.core.mail import EmailMessage
from django.conf import settings

def send_email_alert(subject, message, recipient_list):
    """
    Send an email alert to a list of recipients with headers that 
    encourage Gmail/Outlook to classify them as 'Updates/Notifications'.
    """

    # Ensure subject is tagged as an update
    if not subject.lower().startswith("[update]"):
        subject = f"[Update] {subject}"

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "updates@yourdomain.com"),
        to=recipient_list,
        headers={
            "Precedence": "bulk",  # Marks as bulk/notification
            "X-Auto-Response-Suppress": "All",  # Suppresses OOO replies
            "List-Id": "LifeConcern Updates <updates.yourdomain.com>",  # Treated like a mailing list
        },
    )

    email.send(fail_silently=False)
