# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import MonthlyEntry, Indicator


@receiver([post_save, post_delete], sender=MonthlyEntry)
def update_indicator_latest(sender, instance, **kwargs):
    indicator = instance.indicator

    # Get the most recent entry (latest year+month)
    latest_entry = indicator.entries.order_by("-year", "-month").first()

    if latest_entry:
        indicator.current_value = latest_entry.value
    else:
        indicator.current_value = 0  # No entries left

    # Save current_value immediately
    indicator.save(update_fields=["current_value"])

    # Update progress (this will also save progress internally)
    indicator.update_progress()
