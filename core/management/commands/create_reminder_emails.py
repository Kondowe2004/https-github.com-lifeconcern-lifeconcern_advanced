# core/management/commands/create_reminder_emails.py

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import datetime, date, time, timedelta
import pytz
from core.models import Project, Indicator, MonthlyEntry

class Command(BaseCommand):
    help = "Send monthly indicator reminder emails to coordinators"

    def handle(self, *args, **options):
        # Set timezone to CAT (Central Africa Time, UTC+2)
        cat_tz = pytz.timezone("Africa/Blantyre")
        now_cat = datetime.now(cat_tz)

        # Only run on 6th day of month at 08:30 CAT
        if not (now_cat.day == 6 and now_cat.hour == 8 and now_cat.minute == 30):
            self.stdout.write("It's not 6th day at 08:30 CAT. Exiting.")
            return

        today = now_cat.date()
        first_day_this_month = today.replace(day=1)
        prev_month_last_day = first_day_this_month - timedelta(days=1)
        prev_month = prev_month_last_day.month
        prev_year = prev_month_last_day.year

        # Loop through all active projects
        projects = Project.objects.filter(is_active=True)

        for project in projects:
            coordinator = project.coordinator
            if not coordinator or not coordinator.email:
                continue  # skip if no coordinator or email

            # Indicators for this project
            indicators = Indicator.objects.filter(project=project, is_active=True)

            # Count indicators without entry for prev month
            missing_entries_count = 0
            for indicator in indicators:
                exists = MonthlyEntry.objects.filter(
                    indicator=indicator,
                    month=prev_month,
                    year=prev_year
                ).exists()
                if not exists:
                    missing_entries_count += 1

            # Compose email
            if missing_entries_count > 0:
                # Reminder email
                subject = f"Reminder: {missing_entries_count} indicators pending update"
                message = (
                    f"Dear {coordinator.first_name} {coordinator.last_name},\n\n"
                    f"As of today, {missing_entries_count} indicator(s) for your project "
                    f"'{project.name}' for {prev_month_last_day.strftime('%B %Y')} have not been updated.\n\n"
                    "Please update these indicators at your earliest convenience. "
                    "If you face any challenges, reach out to the M&E team for assistance.\n\n"
                    "Best regards,\n"
                    "Life Concern Data Management Team"
                )
            else:
                # Congratulatory email
                subject = f"Congratulations: All indicators updated for {prev_month_last_day.strftime('%B %Y')}"
                message = (
                    f"Dear {coordinator.first_name} {coordinator.last_name},\n\n"
                    f"All your indicators for project '{project.name}' for {prev_month_last_day.strftime('%B %Y')} "
                    "have been successfully updated as of today.\n\n"
                    "Great work!\n\n"
                    "Best regards,\n"
                    "Life Concern Data Management Team"
                )

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email="datamanagementlico@gmail.com",
                recipient_list=[coordinator.email],
                fail_silently=False,
            )

            self.stdout.write(f"Email sent to {coordinator.email}")
# core/management/commands/create_reminder_emails.py

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import datetime, timedelta
import pytz
from core.models import Project, Indicator, MonthlyEntry

class Command(BaseCommand):
    help = "Send monthly indicator reminder emails to coordinators"

    def handle(self, *args, **options):
        # Set timezone to CAT (Central Africa Time, UTC+2)
        cat_tz = pytz.timezone("Africa/Blantyre")
        now_cat = datetime.now(cat_tz)

        # Only run on 6th day of month between 08:25 and 08:35 CAT
        if not (now_cat.day == 6 and now_cat.hour == 8 and 25 <= now_cat.minute <= 35):
            self.stdout.write("It's not the 6th day at 08:30 CAT (within tolerance). Exiting.")
            return

        today = now_cat.date()
        first_day_this_month = today.replace(day=1)
        prev_month_last_day = first_day_this_month - timedelta(days=1)
        prev_month = prev_month_last_day.month
        prev_year = prev_month_last_day.year

        # Loop through all active projects
        projects = Project.objects.filter(is_active=True)

        for project in projects:
            coordinator = project.coordinator
            if not coordinator or not coordinator.email:
                continue  # skip if no coordinator or email

            # Indicators for this project
            indicators = Indicator.objects.filter(project=project, is_active=True)

            # Count indicators without entry for prev month
            missing_entries_count = 0
            for indicator in indicators:
                exists = MonthlyEntry.objects.filter(
                    indicator=indicator,
                    month=prev_month,
                    year=prev_year
                ).exists()
                if not exists:
                    missing_entries_count += 1

            # Compose email
            if missing_entries_count > 0:
                subject = f"Reminder: {missing_entries_count} indicators pending update"
                message = (
                    f"Dear {coordinator.first_name} {coordinator.last_name},\n\n"
                    f"As of today, {missing_entries_count} indicator(s) for your project "
                    f"'{project.name}' for {prev_month_last_day.strftime('%B %Y')} have not been updated.\n\n"
                    "Please update these indicators at your earliest convenience. "
                    "If you face any challenges, reach out to the M&E team for assistance.\n\n"
                    "Best regards,\n"
                    "Life Concern Data Management Team"
                )
            else:
                subject = f"Congratulations: All indicators updated for {prev_month_last_day.strftime('%B %Y')}"
                message = (
                    f"Dear {coordinator.first_name} {coordinator.last_name},\n\n"
                    f"All your indicators for project '{project.name}' for {prev_month_last_day.strftime('%B %Y')} "
                    "have been successfully updated as of today.\n\n"
                    "Great work!\n\n"
                    "Best regards,\n"
                    "Life Concern Data Management Team"
                )

            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email="datamanagementlico@gmail.com",
                recipient_list=[coordinator.email],
                fail_silently=False,
            )

            self.stdout.write(f"Email sent to {coordinator.email}")
