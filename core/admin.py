from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Project, Indicator, MonthlyEntry, IndicatorTarget, Facility


# -----------------------------
# User Admin Customization
# -----------------------------
class CustomUserAdmin(UserAdmin):
    # Show fields in list view
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    # ✅ Make fields editable directly from the list view
    list_editable = ("email", "first_name", "last_name", "is_staff", "is_active")
    # Optional: search by username or email
    search_fields = ("username", "email", "first_name", "last_name")


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# -----------------------------
# Facility Admin
# -----------------------------
@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude")
    search_fields = ("name",)
    list_filter = ()  # you can later add filters if you want
    ordering = ("name",)


# -----------------------------
# Project Admin
# -----------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "start_year", "end_year", "active")
    list_editable = ("start_year", "end_year", "active")   # ✅ Inline editing
    list_filter = ("active", "start_year", "end_year")
    search_fields = ("name",)
    filter_horizontal = ("facilities",)  # ✅ easier selection for many-to-many


# -----------------------------
# Indicator Admin
# -----------------------------
@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "unit", "is_kpi")
    list_filter = ("project", "is_kpi")
    search_fields = ("name",)

    # Optional: show latest target as a method
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
class MonthlyEntryAdmin(admin.ModelAdmin):
    list_display = ("indicator", "year", "month", "value", "created_by", "created_at")
    list_filter = ("indicator__project", "year", "month")
    search_fields = ("indicator__name",)
