from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from core.utils import send_email_alert

class Command(BaseCommand):
    help = 'Send monthly reminder to Project Staff group to update project data'

    def handle(self, *args, **kwargs):
        try:
            # Get the Project Staff group
            staff_group = Group.objects.get(name='Project Staff')
            staff_users = staff_group.user_set.all()
            recipient_list = [user.email for user in staff_users if user.email]

            subject = "Monthly Reminder: Update Your Project Data"
            message = (
                "Dear Project Staff,\n\n"
                "This is a friendly reminder to update the data for your projects in the Life Concern system.\n\n"
                "Thank you!"
            )

            if recipient_list:
                send_email_alert(subject, message, recipient_list)
                self.stdout.write(self.style.SUCCESS('Monthly reminder sent successfully!'))
            else:
                self.stdout.write(self.style.WARNING('No staff with email found in Project Staff group.'))

        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR('Project Staff group does not exist.'))
