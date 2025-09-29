from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from django.core.exceptions import ValidationError
import datetime
from .utils import send_email_alert


# -------------------------
# Facility Model
# -------------------------
class Facility(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.name


# -------------------------
# Project Model
# -------------------------
class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)

    # NEW: Link projects to facilities
    facilities = models.ManyToManyField(Facility, related_name="projects", blank=True)

    def __str__(self):
        return self.name


# -------------------------
# Indicator Model
# -------------------------
class Indicator(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='indicators')
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default='count')
    is_kpi = models.BooleanField(default=False)
    current_value = models.IntegerField(default=0)  # whole numbers only
    progress = models.IntegerField(default=0)       # % progress as integer

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def update_progress(self):
        """Recalculate progress against the current year's target only"""
        current_year = datetime.date.today().year

        # Get current year's target
        target_obj = self.targets.filter(year=current_year).first()
        target_value = target_obj.value if target_obj else 0

        # Get total actuals for current year
        actual_total = (
            self.entries.filter(year=current_year).aggregate(total=Sum("value"))["total"] or 0
        )

        # Update fields
        self.current_value = actual_total
        if target_value > 0:
            self.progress = int(round((actual_total / target_value) * 100))
        else:
            self.progress = 0

        self.save(update_fields=["current_value", "progress"])


# -------------------------
# Indicator Target Model
# -------------------------
class IndicatorTarget(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='targets')
    year = models.IntegerField()
    value = models.IntegerField()  # whole numbers only

    class Meta:
        unique_together = ('indicator', 'year')
        ordering = ['year']

    def __str__(self):
        return f"{self.indicator.name} - {self.year}: {self.value}"

    # Backend validation
    def clean(self):
        if self.value is None:
            raise ValidationError({'value': "Target value cannot be empty."})
        if not isinstance(self.value, int):
            raise ValidationError({'value': "Target value must be a whole number."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# -------------------------
# Monthly Entry Model
# -------------------------
class MonthlyEntry(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='entries')
    year = models.IntegerField()
    month = models.IntegerField()  # 1..12
    value = models.IntegerField(default=0)  # whole numbers only
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Backend validation
    def clean(self):
        if self.value is None:
            raise ValidationError({'value': "KPI value cannot be empty."})
        if not isinstance(self.value, int):
            raise ValidationError({'value': "KPI value must be a whole number."})
        if not (1 <= self.month <= 12):
            raise ValidationError({'month': "Month must be between 1 and 12."})

    def save(self, *args, **kwargs):
        self.full_clean()  # calls clean() before saving
        super().save(*args, **kwargs)


# -------------------------
# Report Model
# -------------------------
class Report(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.user.username}"


# -------------------------
# Email Alert + Progress Update Signal
# -------------------------
@receiver(post_save, sender=MonthlyEntry)
def handle_monthly_entry_save(sender, instance, created, **kwargs):
    """Send alert + update indicator progress when a monthly entry is saved"""
    # Update progress automatically
    instance.indicator.update_progress()

    # Send email alert if new entry created
    if created:
        users = User.objects.all()
        recipient_list = [user.email for user in users if user.email]
        subject = f"New Data Entry Saved for {instance.indicator.project.name}"
        message = (
            f"Hello,\n\nA new data entry has been saved by "
            f"{instance.created_by.username if instance.created_by else 'a user'} "
            f"for the project '{instance.indicator.project.name}' and indicator '{instance.indicator.name}'.\n\n"
            f"Value: {instance.value}\nMonth: {instance.month}/{instance.year}\nNotes: {instance.notes}"
        )
        send_email_alert(subject, message, recipient_list)
