from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Project, Indicator, MonthlyEntry, IndicatorTarget,
    Facility, Donor, Report
)

# -----------------------------
# User Admin Customization
# -----------------------------
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    list_editable = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# -----------------------------
# Facility Admin
# -----------------------------
@admin.register(Facility)
class FacilityAdmin(SimpleHistoryAdmin):
    list_display = ("name", "latitude", "longitude")
    search_fields = ("name",)
    ordering = ("name",)

# -----------------------------
# Donor Admin
# -----------------------------
@admin.register(Donor)
class DonorAdmin(SimpleHistoryAdmin):
    list_display = ("name", "contact_email", "phone", "total_projects")
    search_fields = ("name", "contact_email", "phone")

    def total_projects(self, obj):
        return obj.funded_projects().count()
    total_projects.short_description = "Projects Funded"

# -----------------------------
# Project Admin
# -----------------------------
@admin.register(Project)
class ProjectAdmin(SimpleHistoryAdmin):
    list_display = ("name", "coordinator_full_name", "start_year", "end_year", "is_active", "main_donor")
    list_editable = ("is_active",)
    list_filter = ("is_active", "start_date", "end_date", "coordinator")
    search_fields = ("name", "coordinator__first_name", "coordinator__last_name", "main_donor__name")
    filter_horizontal = ("facilities", "donors")

    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'start_date', 'end_date', 'is_active')
        }),
        ('Relationships', {
            'fields': ('coordinator', 'created_by', 'main_donor', 'donors', 'facilities')
        }),
    )

    def coordinator_full_name(self, obj):
        if obj.coordinator:
            return f"{obj.coordinator.first_name} {obj.coordinator.last_name}"
        return "Not assigned"
    coordinator_full_name.short_description = 'Coordinator'

    def start_year(self, obj):
        return obj.start_date.year if obj.start_date else "-"
    start_year.admin_order_field = "start_date"
    start_year.short_description = "Start Year"

    def end_year(self, obj):
        return obj.end_date.year if obj.end_date else "-"
    end_year.admin_order_field = "end_date"
    end_year.short_description = "End Year"

# -----------------------------
# Indicator Admin
# -----------------------------
@admin.register(Indicator)
class IndicatorAdmin(SimpleHistoryAdmin):
    list_display = ("name", "project", "unit", "is_kpi", "is_active", "latest_target")
    list_editable = ("is_kpi", "is_active")
    list_filter = ("project", "is_kpi", "is_active")
    search_fields = ("name", "project__name")

    def latest_target(self, obj):
        target_obj = IndicatorTarget.objects.filter(indicator=obj).order_by("-year").first()
        return target_obj.value if target_obj else "-"
    latest_target.short_description = "Latest Target"

# -----------------------------
# Indicator Target Admin
# -----------------------------
@admin.register(IndicatorTarget)
class IndicatorTargetAdmin(admin.ModelAdmin):
    list_display = ("indicator", "year", "value")
    list_filter = ("year", "indicator__project")
    search_fields = ("indicator__name",)

# -----------------------------
# Monthly Entry Admin
# -----------------------------
@admin.register(MonthlyEntry)
class MonthlyEntryAdmin(SimpleHistoryAdmin):
    list_display = ("indicator", "year", "month", "value", "created_by", "created_at")
    list_filter = ("indicator__project", "year", "month")
    search_fields = ("indicator__name",)

# -----------------------------
# Report Admin
# -----------------------------
@admin.register(Report)
class ReportAdmin(SimpleHistoryAdmin):
    list_display = ("title", "user", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("title", "user__username")
