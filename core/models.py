from django.db import models
from django.contrib.auth.models import User  # <-- Add this import for User


class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class Indicator(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='indicators')
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default='count')
    target = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_kpi = models.BooleanField(default=False)  # Field for KPI indicators

    # 🔹 New fields for automation
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)  
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # % progress

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def update_progress(self):
        """Recalculate progress against target"""
        if self.target and self.target > 0:
            self.progress = round((self.current_value / self.target) * 100, 2)
        else:
            self.progress = 0
        self.save(update_fields=["progress"])


class MonthlyEntry(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name='entries')
    year = models.IntegerField()
    month = models.IntegerField()  # 1..12
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Reference to User
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('indicator', 'year', 'month')
        ordering = ['indicator', 'year', 'month']

    def __str__(self):
        return f"{self.indicator} {self.year}-{self.month:02d}"
