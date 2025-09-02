from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Project, Indicator, MonthlyEntry

# -----------------------------
# User Admin Customization
# -----------------------------
class CustomUserAdmin(UserAdmin):
    # Show in list view
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")

    # ✅ Allow editing directly from the list view
    list_editable = ("first_name", "last_name", "is_staff", "is_active")

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# -----------------------------
# Project Admin
# -----------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "start_year", "end_year", "active")
    list_editable = ("start_year", "end_year", "active")   # ✅ Inline editing
    list_filter = ("active", "start_year", "end_year")
    search_fields = ("name",)

# -----------------------------
# Indicator Admin
# -----------------------------
@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "unit", "target", "is_kpi")
    list_filter = ("project", "is_kpi")
    search_fields = ("name",)

# -----------------------------
# Monthly Entry Admin
# -----------------------------
@admin.register(MonthlyEntry)
class MonthlyEntryAdmin(admin.ModelAdmin):
    list_display = ("indicator", "year", "month", "value", "created_by", "created_at")
    list_filter = ("indicator__project", "year", "month")
    search_fields = ("indicator__name",)
