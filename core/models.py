from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from django.core.exceptions import ValidationError
import datetime
from .utils import send_email_alert
from simple_history.models import HistoricalRecords

# -------------------------
# Facility Model
# -------------------------
class Facility(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    history = HistoricalRecords()

    def __str__(self):
        return self.name

# -------------------------
# Donor Model
# -------------------------
class Donor(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    facilities = models.ManyToManyField(Facility, blank=True, related_name='donors')

    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def funded_projects(self):
        return self.projects_from_form.all() if hasattr(self, 'projects_from_form') else []

# -------------------------
# Project Model + Manager
# -------------------------
class ProjectManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    main_donor = models.ForeignKey(
        Donor, on_delete=models.SET_NULL, null=True, blank=True, related_name="main_projects"
    )
    donors = models.ManyToManyField(Donor, related_name="projects", blank=True)
    facilities = models.ManyToManyField(Facility, related_name="projects", blank=True)

    coordinator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='coordinated_projects'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_projects'
    )

    objects = models.Manager()
    active_objects = ProjectManager()

    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def coordinator_first_name(self):
        return self.coordinator.first_name if self.coordinator else "No coordinator assigned"

    def status(self):
        today = datetime.date.today()
        if self.end_date and self.end_date < today:
            return "Completed"
        elif self.start_date and self.start_date > today:
            return "Upcoming"
        elif self.end_date and (self.end_date - today).days <= 30:
            return "Ending Soon"
        return "Active"

# Donor ↔ Projects for Form
Project.add_to_class(
    "projects_from_form",
    models.ManyToManyField(Donor, related_name="projects_from_form", blank=True)
)

# -------------------------
# Indicator Model + Manager
# -------------------------
class IndicatorManager(models.Manager):
    def active(self):
        return self.filter(is_active=True, project__is_active=True)

class Indicator(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='indicators')
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default='count')
    is_kpi = models.BooleanField(default=False)
    current_value = models.IntegerField(default=0)
    progress = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = IndicatorManager()

    history = HistoricalRecords()

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def update_progress(self):
        if not self.is_active or not self.project.is_active:
            return
        current_year = datetime.date.today().year
        target_obj = self.targets.filter(year=current_year).first()
        target_value = target_obj.value if target_obj else 0
        actual_total = self.entries.filter(year=current_year).aggregate(total=Sum("value"))["total"] or 0
        self.current_value = actual_total
        self.progress = int(round((actual_total / target_value) * 100)) if target_value > 0 else 0
        self.save(update_fields=["current_value", "progress"])

# -------------------------
# Indicator Target Model
# -------------------------
class IndicatorTarget(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='targets')
    year = models.IntegerField()
    value = models.IntegerField()

    class Meta:
        unique_together = ('indicator', 'year')
        ordering = ['year']

    def __str__(self):
        return f"{self.indicator.name} - {self.year}: {self.value}"

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
    month = models.IntegerField()
    value = models.IntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.value is None:
            raise ValidationError({'value': "KPI value cannot be empty."})
        if not isinstance(self.value, int):
            raise ValidationError({'value': "KPI value must be a whole number."})
        if not (1 <= self.month <= 12):
            raise ValidationError({'month': "Month must be between 1 and 12."})

    def save(self, *args, **kwargs):
        self.full_clean()
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
# Safe Email Alert + Progress Update Signal
# -------------------------
@receiver(post_save, sender=MonthlyEntry)
def handle_monthly_entry_save(sender, instance, created, **kwargs):
    # Update progress
    if instance.indicator.is_active and instance.indicator.project.is_active:
        instance.indicator.update_progress()

    # Send email safely
    if created and instance.indicator.is_active and instance.indicator.project.is_active:
        users = User.objects.all()
        recipient_list = [user.email for user in users if user.email]
        subject = f"New Data Entry Saved for {instance.indicator.project.name}"
        message = (
            f"Hello,\n\nA new data entry has been saved by "
            f"{instance.created_by.username if instance.created_by else 'a user'} "
            f"for the project '{instance.indicator.project.name}' and indicator '{instance.indicator.name}'.\n\n"
            f"Value: {instance.value}\nMonth: {instance.month}/{instance.year}\nNotes: {instance.notes}"
        )
        try:
            send_email_alert(subject, message, recipient_list)
        except Exception as e:
            # Log error or silently ignore network/email issues
            print(f"[Warning] Failed to send email alert: {e}")
