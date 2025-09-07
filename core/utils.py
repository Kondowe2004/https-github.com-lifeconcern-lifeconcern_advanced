from django.core.mail import send_mail
from django.conf import settings

def send_email_alert(subject, message, recipient_list):
    """
    Send an email alert to a list of recipients.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        fail_silently=False
    )
