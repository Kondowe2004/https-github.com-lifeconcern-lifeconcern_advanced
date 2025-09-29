from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
import datetime
from django.db.models import Sum
from django.contrib.auth.models import User
from collections import defaultdict
import csv
from django.db.models.functions import TruncMonth
from .models import Project, Indicator, MonthlyEntry
from .forms import ProjectForm, IndicatorForm
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Count
from core.models import Report
from core.templatetags.custom_tags import get_month_name
import calendar
import json
from .models import Indicator
from decimal import Decimal
from django.db.models import F, ExpressionWrapper, FloatField
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Max
from django.template.loader import render_to_string
from datetime import date
from decimal import Decimal, DivisionUndefined, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.utils import timezone
from .models import Indicator, IndicatorTarget
from .forms import IndicatorTargetForm #from django.shortcuts import render
from decimal import Decimal, InvalidOperation
from django.db import transaction, IntegrityError
import datetime
from collections import defaultdict
from .forms import IndicatorForm
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.http import HttpResponse
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image  # for logo
import os
from django.conf import settings
from django.db import models

def safe_int(value, default=0):
    """
    Safely converts a value to integer.
    Returns `default` if value is None, empty string, or invalid.
    """
    try:
        if value in [None, '']:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


# -----------------------------
# Dashboard
# -----------------------------
@login_required
def dashboard(request):
    """Dashboard view showing KPIs, comparative analysis, trend analysis, and rotating indicators."""

    today_year = datetime.date.today().year
    selected_year = safe_int(request.GET.get("year"), default=today_year)

    # Available years for dropdown (ensure current year is always included)
    years_set = set(
        list(MonthlyEntry.objects.values_list("year", flat=True).distinct()) +
        list(IndicatorTarget.objects.values_list("year", flat=True).distinct()) +
        [today_year]  # Ensure current year is included
    )
    years = sorted(years_set, reverse=True)

    # Active projects only
    projects = Project.objects.filter(active=True)
    total_projects = projects.count()

    # Active indicators
    all_indicators = Indicator.objects.filter(project__active=True).select_related("project")
    total_indicators = all_indicators.count()

    # KPI: total entries for selected year
    total_entries = MonthlyEntry.objects.filter(year=selected_year).count()

    # Annual total for "People Reached"
    annual_total = safe_int(
        MonthlyEntry.objects.filter(
            year=selected_year,
            indicator__unit__iexact="People Reached"
        ).aggregate(total=Sum("value"))["total"]
    )

    user_count = User.objects.filter(is_active=True).count()

    # Comparative Analysis (Actual vs Target per active project)
    comparative_labels, comparative_actuals, comparative_targets = [], [], []

    for proj in projects:
        comparative_labels.append(proj.name)

        actual_total = safe_int(
            MonthlyEntry.objects.filter(
                year=selected_year,
                indicator__project=proj,
                indicator__unit__iexact="People Reached"
            ).aggregate(total=Sum("value"))["total"]
        )

        indicator_total = safe_int(
            IndicatorTarget.objects.filter(
                indicator__project=proj,
                year=selected_year,
                indicator__unit__iexact="People Reached"
            ).aggregate(total=Sum("value"))["total"]
        )

        comparative_actuals.append(actual_total)
        comparative_targets.append(indicator_total)

    # Trend Analysis (Monthly Actual vs Monthly Target)
    trend_months, trend_actuals, trend_targets = [], [], []

    total_annual_target = safe_int(
        IndicatorTarget.objects.filter(
            year=selected_year,
            indicator__unit__iexact="People Reached"
        ).aggregate(total=Sum("value"))["total"]
    )

    monthly_target = int(total_annual_target / 12) if total_annual_target else 0

    for month_num in range(1, 13):
        trend_months.append(datetime.date(1900, month_num, 1).strftime("%b"))

        monthly_actual = safe_int(
            MonthlyEntry.objects.filter(
                year=selected_year,
                month=month_num,
                indicator__unit__iexact="People Reached"
            ).aggregate(total=Sum("value"))["total"]
        )

        trend_actuals.append(monthly_actual)
        trend_targets.append(monthly_target)

    # Rotating Indicators (timeless for active projects)
    indicators_data = []
    for ind in all_indicators:
        total_actual = safe_int(
            MonthlyEntry.objects.filter(
                indicator=ind,
                year=selected_year
            ).aggregate(total=Sum("value"))["total"]
        )

        last_entry = MonthlyEntry.objects.filter(indicator=ind, year=selected_year).order_by("-id").first()
        prev_entry_qs = MonthlyEntry.objects.filter(indicator=ind, year=selected_year).order_by("-id")[1:2]

        previous_value = safe_int(prev_entry_qs[0].value) if prev_entry_qs else 0
        last_value = safe_int(last_entry.value) if last_entry else 0

        target_obj = IndicatorTarget.objects.filter(indicator=ind, year=selected_year).first()
        target_value = safe_int(target_obj.value) if target_obj else 0

        indicators_data.append({
            "id": ind.id,
            "name": ind.name,
            "project": ind.project.name if ind.project else None,
            "value": total_actual,
            "target": target_value,
            "previous_value": previous_value,
            "last_month_value": last_value,
        })

    # Stats for KPI cards
    stats = [
        {
            "label": "Projects",
            "value": total_projects,
            "icon": "fas fa-folder-open",
            "bg_gradient": "linear-gradient(135deg, #6a11cb, #2575fc)",
            "url": "/projects/",
        },
        {
            "label": "Indicators",
            "value": total_indicators,
            "icon": "fas fa-bullseye",
            "bg_gradient": "linear-gradient(135deg, #11998e, #38ef7d)",
            "url": "/projects/",
        },
        {
            "label": f"People Reached ({selected_year})",
            "value": annual_total,
            "icon": "fas fa-calendar-alt",
            "bg_gradient": "linear-gradient(135deg, #f7971e, #ffd200)",
            "url": "#",
        },
        {
            "label": "Active Users",
            "value": user_count,
            "icon": "fas fa-users",
            "bg_gradient": "linear-gradient(135deg, #ff416c, #ff4b2b)",
            "url": "/profile/",
        },
    ]

    context = {
        "projects": projects,
        "total_projects": total_projects,
        "total_indicators": total_indicators,
        "total_entries": total_entries,
        "current_year": today_year,
        "selected_year": selected_year,
        "years": years,
        "annual_total": annual_total,
        "user_count": user_count,
        "comparative_labels": comparative_labels,
        "comparative_actuals": comparative_actuals,
        "comparative_targets": comparative_targets,
        "trend_months": trend_months,
        "trend_actuals": trend_actuals,
        "trend_targets": trend_targets,
        "indicators": indicators_data,
        "stats": stats,
    }

    return render(request, "core/dashboard.html", context)




@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    indicators = Indicator.objects.filter(project=project)
    months = list(range(1, 13))
    year = int(request.GET.get("year", datetime.datetime.now().year))

    # --- Build KPI grid ---
    grid = {}
    for ind in indicators:
        grid[ind.id] = {}
        for month in months:
            entry = MonthlyEntry.objects.filter(indicator=ind, year=year, month=month).first()
            grid[ind.id][month] = entry.value if entry else None

    return render(request, "core/project_detail.html", {
        "project": project,
        "indicators": indicators,
        "months": months,
        "year": year,
        "grid": grid,
    })




# -----------------------------
# KPI Data Entry View
# -----------------------------
@login_required
def project_kpis(request, pk):
    project = get_object_or_404(Project, pk=pk)
    indicators = Indicator.objects.filter(project=project)
    months = list(range(1, 13))
    year = int(request.GET.get("year", request.POST.get("year", datetime.datetime.now().year)))

    errors = defaultdict(dict)  # {indicator_id: {month: error_message}}

    # -------------------------
    # Handle POST: bulk monthly values + optional target updates
    # -------------------------
    if request.method == "POST":
        with transaction.atomic():
            for ind in indicators:
                # --- Update monthly entries ---
                for month in months:
                    field_name = f"val_{ind.id}_{month}"
                    raw_val = request.POST.get(field_name, "").strip()
                    if raw_val == "":
                        continue
                    try:
                        val = safe_int(raw_val)
                        MonthlyEntry.objects.update_or_create(
                            indicator=ind,
                            year=year,
                            month=month,
                            defaults={"value": val, "created_by": request.user},
                        )
                    except ValueError:
                        errors[ind.id][month] = "Only whole numbers allowed"

                # --- Update annual target if provided ---
                target_field = f"target_{ind.id}"
                raw_target = request.POST.get(target_field, "").strip()
                if raw_target != "":
                    try:
                        target_val = safe_int(raw_target)
                        IndicatorTarget.objects.update_or_create(
                            indicator=ind,
                            year=year,
                            defaults={"value": target_val},
                        )
                    except ValueError:
                        errors[ind.id]["target"] = "Only whole numbers allowed"

                # --- Update indicator progress ---
                total_val = MonthlyEntry.objects.filter(indicator=ind, year=year).aggregate(
                    total=Sum("value")
                )["total"] or 0
                ind.current_value = total_val
                ind.update_progress()

        if any(errors[ind.id] for ind in indicators):
            messages.warning(request, "Some cells contained invalid values. Please correct them.")
        else:
            messages.success(request, "KPI data and targets saved successfully!")
            return redirect("project_kpis", pk=project.id)

    # -------------------------
    # Prepare grid + totals
    # -------------------------
    grid = defaultdict(dict)
    totals = {}              # Row totals per indicator
    monthly_totals = {}      # Column totals across indicators
    grand_total = 0          # Bottom-right grand total

    # Fetch targets for all indicators for this year
    targets = IndicatorTarget.objects.filter(indicator__in=indicators, year=year)
    target_dict = {t.indicator_id: int(t.value) for t in targets}

    # --- Auto-create target for new indicators ---
    for ind in indicators:
        if ind.id not in target_dict:
            target_obj, created = IndicatorTarget.objects.get_or_create(
                indicator=ind,
                year=year,
                defaults={"value": 0},  # integer default
            )
            target_dict[ind.id] = int(target_obj.value)

    # Build grid and row totals
    for ind in indicators:
        row_total = 0
        for month in months:
            entry = MonthlyEntry.objects.filter(indicator=ind, year=year, month=month).first()
            val = int(entry.value) if entry else 0
            grid[ind.id][month] = val if val != 0 else None
            row_total += val
        totals[ind.id] = row_total
        grand_total += row_total

    # Build column totals
    for month in months:
        monthly_totals[month] = sum(grid[ind.id].get(month, 0) or 0 for ind in indicators)

    context = {
        "project": project,
        "indicators": indicators,
        "months": months,
        "year": year,
        "grid": grid,
        "totals": totals,
        "monthly_totals": monthly_totals,
        "grand_total": grand_total,
        "target_dict": target_dict,
        "errors": errors,  # Pass errors to template
    }

    return render(request, "core/project_kpis.html", context)





# -------------------------
# ADD / EDIT / DELETE PROJECT
# -------------------------
@login_required
def project_add(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Project added successfully!")
            return redirect("projects")
    else:
        form = ProjectForm()
    return render(request, "core/project_form.html", {"form": form, "title": "Add Project"})


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully!")
            return redirect("projects")
    else:
        form = ProjectForm(instance=project)
    return render(request, "core/project_form.html", {"form": form, "title": "Edit Project"})


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted successfully!")
        return redirect("projects")
    return render(request, "core/project_confirm_delete.html", {"project": project})




# -----------------------------
# Add KPI view
# -----------------------------
@login_required
def indicator_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    current_year = timezone.now().year
    years = [current_year - 2, current_year - 1, current_year, current_year + 1, current_year + 2]

    if request.method == "POST":
        form = IndicatorForm(request.POST)
        if form.is_valid():
            # Save Indicator instance first
            indicator = form.save(commit=False)
            indicator.project = project
            indicator.save()

            # Handle KPI target for selected year
            target_val_raw = form.cleaned_data.get("target")
            target_year_raw = request.POST.get("year", current_year)

            try:
                target_year = int(target_year_raw)
            except (ValueError, TypeError):
                target_year = current_year

            # Validate numeric target before saving
            if target_val_raw is not None and str(target_val_raw).strip() != "":
                try:
                    target_val = safe_int(target_val_raw)
                except ValueError:
                    messages.warning(
                        request,
                        "Invalid target value. Only whole numbers are allowed."
                    )
                    return render(
                        request,
                        "core/indicators/indicator_form.html",
                        {
                            "form": form,
                            "project": project,
                            "title": "Add KPI",
                            "now": timezone.now(),
                            "years": years,
                            "selected_year": target_year,
                        },
                    )

                IndicatorTarget.objects.update_or_create(
                    indicator=indicator,
                    year=target_year,
                    defaults={"value": target_val},
                )
            else:
                # If target is empty, default to 0
                IndicatorTarget.objects.update_or_create(
                    indicator=indicator,
                    year=target_year,
                    defaults={"value": 0},
                )

            messages.success(request, "KPI added successfully!")
            return redirect("project_detail", pk=project.pk)
        else:
            messages.warning(request, "Please correct the errors in the form.")
    else:
        form = IndicatorForm()

    return render(
        request,
        "core/indicators/indicator_form.html",
        {
            "form": form,
            "project": project,
            "title": "Add KPI",
            "now": timezone.now(),
            "years": years,
            "selected_year": current_year,
        },
    )




# -----------------------------
# Edit KPI view
# -----------------------------
@login_required
def indicator_edit(request, project_pk, pk):
    project = get_object_or_404(Project, pk=project_pk)
    indicator = get_object_or_404(Indicator, pk=pk, project=project)
    current_year = timezone.now().year
    years = [current_year - 2, current_year - 1, current_year, current_year + 1, current_year + 2]

    # Pre-fill current-year target if it exists
    try:
        current_target = IndicatorTarget.objects.get(indicator=indicator, year=current_year)
        initial_data = {"target": current_target.value}
        selected_year = current_year
    except IndicatorTarget.DoesNotExist:
        initial_data = {}
        selected_year = current_year

    if request.method == "POST":
        form = IndicatorForm(request.POST, instance=indicator, initial=initial_data)
        if form.is_valid():
            indicator = form.save(commit=False)
            indicator.project = project
            indicator.save()

            # Handle KPI target for selected year
            target_val_raw = form.cleaned_data.get("target")
            target_year_raw = request.POST.get("year", current_year)

            try:
                target_year = int(target_year_raw)
            except (ValueError, TypeError):
                target_year = current_year

            # Validate numeric target before saving
            if target_val_raw is not None and str(target_val_raw).strip() != "":
                try:
                    target_val = safe_int(target_val_raw)
                    IndicatorTarget.objects.update_or_create(
                        indicator=indicator,
                        year=target_year,
                        defaults={"value": target_val},
                    )
                    messages.success(request, "KPI updated successfully!")
                    return redirect("project_detail", pk=project.pk)
                except ValueError:
                    messages.warning(
                        request,
                        "Invalid target value. Only whole numbers are allowed."
                    )
            else:
                # If target is empty, default to 0
                IndicatorTarget.objects.update_or_create(
                    indicator=indicator,
                    year=target_year,
                    defaults={"value": 0},
                )
                messages.success(request, "KPI updated successfully!")
                return redirect("project_detail", pk=project.pk)
        else:
            messages.warning(request, "Please correct the errors in the form.")
    else:
        form = IndicatorForm(instance=indicator, initial=initial_data)

    return render(
        request,
        "core/indicators/indicator_form.html",
        {
            "form": form,
            "project": project,
            "indicator": indicator,
            "title": "Edit KPI",
            "now": timezone.now(),
            "years": years,
            "selected_year": selected_year,
        },
    )


@login_required
def indicator_delete(request, project_pk, pk):
    project = get_object_or_404(Project, pk=project_pk)
    indicator = get_object_or_404(Indicator, pk=pk, project=project)
    if request.method == "POST":
        indicator.delete()
        messages.success(request, "KPI deleted successfully!")
        return redirect("project_detail", pk=project.pk)
    return render(request, "core/indicators/indicator_confirm_delete.html",
                  {"project": project, "indicator": indicator})


# -------------------------
# USER PROFILE
# -------------------------
@login_required
def profile(request):
    return render(request, "core/profile.html")


# -------------------------
# LIST PROJECTS WITH FACILITIES (AJAX-enabled)
# -------------------------
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def projects(request):
    # Fetch all projects
    projects = Project.objects.all().order_by('name')

    # Fetch all facilities for selection
    all_facilities = Facility.objects.all().order_by('name')

    # Handle POST for facility updates
    if request.method == "POST":
        # Check if this is an AJAX JSON request
        try:
            data = json.loads(request.body)
            project_id = data.get("project_id")
            facilities = data.get("facilities", [])
            project = get_object_or_404(Project, pk=project_id)
            project.facilities.set(facilities)
            project.save()
            return JsonResponse({"status": "success"})
        except (json.JSONDecodeError, KeyError):
            # Fallback for traditional POST (non-AJAX) submission
            if "facilities_submit" in request.POST:
                project_id = request.POST.get("project_id")
                project = get_object_or_404(Project, pk=project_id)
                selected_facilities = request.POST.getlist("facilities")
                project.facilities.set(selected_facilities)
                project.save()
                messages.success(request, f"Facilities updated for project '{project.name}'.")
                return redirect('projects')
            # If nothing matches, return error
            return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    # Render template
    return render(request, "core/projects.html", {
        "projects": projects,
        "all_facilities": all_facilities,
    })



# -----------------------------
# Bulk Save Entries View
# -----------------------------
@login_required
def bulk_save_entries(request, pk):
    project = get_object_or_404(Project, pk=pk)
    indicators = Indicator.objects.filter(project=project)
    now = timezone.now()
    current_year = now.year
    current_month = now.month

    if request.method == "POST":
        year = int(request.POST.get("year", current_year))
        month = int(request.POST.get("month", current_month))
        invalid_entries = []

        with transaction.atomic():
            for indicator in indicators:
                raw_value = request.POST.get(f"indicator_{indicator.id}")
                if raw_value not in [None, ""]:
                    try:
                        numeric_value = safe_int(raw_value)
                        MonthlyEntry.objects.update_or_create(
                            indicator=indicator,
                            year=year,
                            month=month,
                            defaults={"value": numeric_value, "created_by": request.user},
                        )
                    except ValueError:
                        invalid_entries.append(indicator.name)

        if invalid_entries:
            messages.warning(
                request,
                f"Some entries were not saved because they were not whole numbers: {', '.join(invalid_entries)}"
            )
        else:
            messages.success(request, f"Entries for {month}/{year} saved successfully!")

        return redirect("project_detail", pk=project.id)

    return render(request, "core/bulk_save_entries.html", {
        "project": project,
        "indicators": indicators,
        "year": current_year,
        "month": current_month,
    })


# -------------------------
# REPORTS
# -------------------------
@login_required
def reports(request):
    current_year = datetime.datetime.now().year
    year = int(request.GET.get("year", current_year))

    # ✅ Collect distinct years available in MonthlyEntry + current year
    years_qs = MonthlyEntry.objects.values_list("year", flat=True).distinct()
    years = sorted(set(list(years_qs) + [current_year]), reverse=True)

    projects = Project.objects.all()
    indicators = Indicator.objects.all()
    units = indicators.values_list("unit", flat=True).distinct()

    selected_unit = request.GET.get("unit") or None
    selected_indicator_ids = request.GET.getlist("indicators")

    base_qs = MonthlyEntry.objects.filter(year=year)
    if selected_unit:
        base_qs = base_qs.filter(indicator__unit=selected_unit)
    if selected_indicator_ids:
        base_qs = base_qs.filter(indicator_id__in=selected_indicator_ids)

    # -------------------------
    # Indicator Totals
    # -------------------------
    indicator_totals = (
        base_qs.values("indicator__id", "indicator__name", "indicator__unit")
        .annotate(total=Sum("value"))
        .order_by("indicator__name")
    )
    selected_indicators_data, overall_total = [], 0
    for row in indicator_totals:
        val = row["total"] or 0
        selected_indicators_data.append({
            "id": row["indicator__id"],
            "name": row["indicator__name"],
            "unit": row["indicator__unit"],
            "value": val
        })
        overall_total += val

    # -------------------------
    # Monthly Breakdown
    # -------------------------
    monthly_labels = list(range(1, 13))
    monthly_data = []
    for ind in indicators:
        ind_series = [
            base_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
            for m in monthly_labels
        ]
        if any(ind_series):
            monthly_data.append({
                "indicator": ind.name,
                "unit": ind.unit,
                "values": ind_series,
            })

    # -------------------------
    # Quarterly Breakdown
    # -------------------------
    quarterly_labels = ["Q1", "Q2", "Q3", "Q4"]
    quarterly_data = []
    for ind in indicators:
        ind_monthly = [
            base_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
            for m in monthly_labels
        ]
        if any(ind_monthly):
            quarterly_data.append({
                "indicator": ind.name,
                "unit": ind.unit,
                "values": [
                    sum(ind_monthly[0:3]),
                    sum(ind_monthly[3:6]),
                    sum(ind_monthly[6:9]),
                    sum(ind_monthly[9:12]),
                ]
            })

    # -------------------------
    # Project Totals (per project summary + per-indicator breakdown)
    # -------------------------
    project_totals = {}
    project_totals_chart = {}
    for project in projects:
        proj_qs = base_qs.filter(indicator__project=project)
        proj_rows = (
            proj_qs.values("indicator__id", "indicator__name", "indicator__unit")
            .annotate(total=Sum("value"))
            .order_by("indicator__name")
        )
        if proj_rows:
            project_totals[project.name] = list(proj_rows)
            project_totals_chart[project.name] = [
                {
                    "indicator": r["indicator__name"],
                    "unit": r["indicator__unit"],
                    "value": r["total"] or 0,
                }
                for r in proj_rows
            ]

    # ✅ Fix: aggregate per project (not empty anymore)
    project_totals_summary = (
        base_qs.values("indicator__project__id", "indicator__project__name")
        .annotate(total=Sum("value"))
        .order_by("indicator__project__name")
    )
    project_totals_labels = [p["indicator__project__name"] for p in project_totals_summary]
    project_totals_data = [p["total"] or 0 for p in project_totals_summary]

    # -------------------------
    # Project Trends
    # -------------------------
    project_trends = {}
    for project in projects:
        proj_qs = base_qs.filter(indicator__project=project)
        trend_data = []
        for ind in indicators.filter(project=project):
            ind_series = [
                proj_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
                for m in monthly_labels
            ]
            if any(ind_series):
                trend_data.append({
                    "indicator": ind.name,
                    "unit": ind.unit,
                    "months": monthly_labels,
                    "values": ind_series,
                })
        if trend_data:
            project_trends[project.name] = trend_data

    context = {
        "year": year,
        "years": years,   # ✅ Updated: always includes current year
        "projects": projects,
        "indicators": indicators,
        "units": units,
        "selected_unit": selected_unit,
        "selected_indicators": selected_indicator_ids,

        "indicator_totals": indicator_totals,
        "selected_indicators_data": selected_indicators_data,
        "overall_total": overall_total,
        "ytd_totals": indicator_totals,

        "monthly_labels": monthly_labels,
        "monthly_data": monthly_data,
        "quarterly_labels": quarterly_labels,
        "quarterly_data": quarterly_data,

        "project_totals": project_totals,
        "project_totals_chart": project_totals_chart,
        "project_totals_labels": project_totals_labels,
        "project_totals_data": project_totals_data,
        "project_trends": project_trends,
    }
    return render(request, "core/reports.html", context)



def export_project_kpis(request, pk):
    project = Project.objects.get(pk=pk)
    year = int(request.GET.get("year", 2025))  # fallback year

    # Prepare HTTP response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{project.name}_kpis_{year}.csv"'

    writer = csv.writer(response)
    # Header row
    months = range(1, 13)
    header = ["Indicator", "Unit"] + [f"{m:02d}" for m in months] + ["Total"]
    writer.writerow(header)

    # Data rows
    indicators = project.indicators.all()
    for ind in indicators:
        row = [ind.name, ind.unit]
        total = 0
        for m in months:
            entry = MonthlyEntry.objects.filter(indicator=ind, year=year, month=m).first()
            val = entry.value if entry else 0
            row.append(val)
            total += val
        row.append(total)
        writer.writerow(row)

    return response


@login_required
def export_project_kpis_excel(request, pk):
    project = Project.objects.get(pk=pk)
    year = int(request.GET.get("year", datetime.date.today().year))

    months = list(range(1, 13))
    month_headers = [calendar.month_abbr[m] for m in months]

    # --- Build target_dict exactly like in template view ---
    indicators = project.indicators.all()
    target_dict = {ind.id: ind.targets.filter(year=year).first().value if ind.targets.filter(year=year).exists() else 0
                   for ind in indicators}

    # --- Create Excel Workbook ---
    wb = Workbook()
    ws = wb.active
    ws.title = f"{project.name} KPIs"

    # --- Title row ---
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=3 + len(months))
    ws["A1"] = f"{project.name} - KPI Report {year}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = Alignment(horizontal="center")

    # --- Header row ---
    headers = ["Annual Target", "Indicator", "Unit"] + month_headers + ["Total"]
    ws.append(headers)
    header_row = ws[ws.max_row]

    thick_border = Side(border_style="medium", color="000000")
    for cell in header_row:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        cell.border = Border(top=thick_border, bottom=thick_border, left=thick_border, right=thick_border)

    # --- Data rows ---
    for ind in indicators:
        target = target_dict.get(ind.id, 0)  # ← get annual target from target_dict
        row_values = []
        total = 0
        for m in months:
            entry = MonthlyEntry.objects.filter(indicator=ind, year=year, month=m).first()
            val = entry.value if entry else 0
            row_values.append(val)
            total += val

        excel_row = [target, ind.name, ind.unit] + row_values + [total]
        ws.append(excel_row)

    # --- Totals row ---
    monthly_totals = [
        sum(MonthlyEntry.objects.filter(indicator__in=indicators, year=year, month=m).values_list('value', flat=True) or [0])
        for m in months
    ]
    grand_total = sum(monthly_totals)
    totals_row = ["", "Total", ""] + monthly_totals + [grand_total]
    ws.append(totals_row)
    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # --- Footer note ---
    ws.merge_cells(start_row=ws.max_row + 2, start_column=1, end_row=ws.max_row + 2, end_column=len(headers))
    ws.cell(row=ws.max_row, column=1).value = f"Exported from Life Concern Data Management System - {datetime.date.today():%Y-%m-%d}"
    ws.cell(row=ws.max_row, column=1).alignment = Alignment(horizontal="center")
    ws.cell(row=ws.max_row, column=1).font = Font(italic=True, size=10)

    # --- Borders and column widths ---
    thin = Side(border_style="thin", color="000000")
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row - 2):
        for cell in row:
            if cell.row == 2:
                continue
            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)
            if isinstance(cell.value, int):
                cell.alignment = Alignment(horizontal="center")

    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = max_length + 3

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{project.name}_kpis_{year}.xlsx"'
    wb.save(response)
    return response



from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
import datetime

@login_required
def monthly_trend_report(request):
    """
    AJAX view to return Monthly Trend data as JSON for chart rendering.
    """
    current_year = datetime.date.today().year

    # --- Get filters from request ---
    try:
        selected_year = int(request.GET.get("year", current_year))
    except ValueError:
        selected_year = current_year

    selected_unit = request.GET.get("unit") or None
    selected_project = request.GET.get("project")
    selected_project = int(selected_project) if selected_project and selected_project.isdigit() else None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    # --- Filter indicators ---
    indicators = Indicator.objects.all()
    if selected_unit:
        indicators = indicators.filter(unit=selected_unit)
    if selected_project:
        indicators = indicators.filter(project_id=selected_project)
    if selected_indicator:
        indicators = indicators.filter(id=selected_indicator)

    months = list(range(1, 13))
    month_labels = [datetime.date(1900, m, 1).strftime('%b') for m in months]

    # --- Prepare Monthly Trend data ---
    monthly_trends_data = []
    for ind in indicators:
        values = [int(MonthlyEntry.objects.filter(
            year=selected_year,
            month=m,
            indicator=ind
        ).aggregate(total=Sum("value"))["total"] or 0) for m in months]
        if any(values):
            monthly_trends_data.append({
                "indicator": ind.name,
                "values": values
            })

    return JsonResponse({
        "month_headers": month_labels,
        "monthly_trends_data": monthly_trends_data
    })



# -----------------------------
# More Reports View
# -----------------------------
# -----------------------------
@login_required
def more_reports(request):
    """
    Full HTML view that renders More Reports page with pivot table and charts.
    """
    current_year = datetime.date.today().year

    # --- Selected filters ---
    selected_year = request.GET.get("year")
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = current_year

    selected_unit = request.GET.get("unit") or None

    selected_project = request.GET.get("project")
    selected_project = int(selected_project) if selected_project and selected_project.isdigit() else None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    # --- Objects for selected project/indicator ---
    selected_project_obj = Project.objects.filter(id=selected_project).first() if selected_project else None
    selected_indicator_obj = Indicator.objects.filter(id=selected_indicator).first() if selected_indicator else None

    # --- Available filter lists ---
    years = list(MonthlyEntry.objects.values_list("year", flat=True).distinct().order_by("year"))
    units = list(Indicator.objects.values_list("unit", flat=True).distinct())
    projects = Project.objects.all()
    indicators = Indicator.objects.all()

    # --- IDs to check if selected_obj is already in the list ---
    project_ids = [p.id for p in projects]
    indicator_ids = [i.id for i in indicators]

    # --- Chart / pivot data ---
    context = _get_report_data(
        selected_year=selected_year,
        selected_unit=selected_unit,
        selected_project=selected_project,
        selected_indicator=selected_indicator
    )

    # --- Add filter context variables for template ---
    context.update({
        "selected_year": selected_year,
        "selected_unit": selected_unit,
        "selected_project": selected_project,
        "selected_indicator": selected_indicator,
        "selected_project_obj": selected_project_obj,
        "selected_indicator_obj": selected_indicator_obj,
        "years": years,
        "units": units,
        "projects": projects,
        "indicators": indicators,
        "project_ids": project_ids,
        "indicator_ids": indicator_ids,
    })

    return render(request, "core/more_reports.html", context)


# -----------------------------
@login_required
def pivot_filter_data_json(request):
    """
    AJAX endpoint: returns filtered chart & heatmap data as JSON.
    """
    current_year = datetime.date.today().year

    selected_year = request.GET.get("year")
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = current_year

    selected_unit = request.GET.get("unit") or None
    selected_project = request.GET.get("project")
    selected_project = int(selected_project) if selected_project and selected_project.isdigit() else None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    context = _get_report_data(
        selected_year=selected_year,
        selected_unit=selected_unit,
        selected_project=selected_project,
        selected_indicator=selected_indicator
    )

    # Return only chart/heatmap JSON (no HTML)
    data = {
        "indicator_distribution_labels": json.loads(context["indicator_distribution_labels"]),
        "indicator_distribution_data": json.loads(context["indicator_distribution_data"]),
        "indicator_progress_labels": json.loads(context["indicator_progress_labels"]),
        "indicator_progress_data": json.loads(context["indicator_progress_data"]),
        "cumulative_performance": json.loads(context["cumulative_performance"]),
        "top_indicators_labels": json.loads(context["top_indicators_labels"]),
        "top_indicators_data": json.loads(context["top_indicators_data"]),
        "facilities_json": json.loads(context["facilities_json"]),
        "correlation_data": json.loads(context["correlation_data"]),
        "yoy_labels": json.loads(context["yoy_labels"]),
        "yoy_data_values": json.loads(context["yoy_data_values"]),
        "month_headers": context["month_headers"],
    }
    return JsonResponse(data)


# -----------------------------
def _get_report_data(selected_year, selected_unit=None, selected_project=None, selected_indicator=None):
    """
    Helper function: computes all data for charts, heatmap, pivot table.
    """
    base_qs = MonthlyEntry.objects.filter(year=selected_year)
    if selected_unit:
        base_qs = base_qs.filter(indicator__unit=selected_unit)
    if selected_project:
        base_qs = base_qs.filter(indicator__project_id=selected_project)
    if selected_indicator:
        base_qs = base_qs.filter(indicator_id=selected_indicator)

    # --- Indicators ---
    indicators = Indicator.objects.all()
    if selected_unit:
        indicators = indicators.filter(unit=selected_unit)
    if selected_project:
        indicators = indicators.filter(project_id=selected_project)
    if selected_indicator:
        indicators = indicators.filter(id=selected_indicator)

    # --- Pivot Table ---
    months = list(range(1, 13))
    month_headers = [calendar.month_abbr[m] for m in months]
    pivot_data = []
    column_totals = {m: 0 for m in months}
    grand_total = 0

    for ind in indicators:
        row_values = []
        row_total = 0
        for m in months:
            val = base_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
            val = int(val)
            row_values.append(val)
            row_total += val
            column_totals[m] += val
        grand_total += row_total

        target_obj = IndicatorTarget.objects.filter(indicator=ind, year=selected_year).first()
        target_value = int(target_obj.value) if target_obj and target_obj.value > 0 else 1
        progress = row_total * 100 // target_value

        pivot_data.append({
            "year": selected_year,
            "project": ind.project.name if ind.project else "-",
            "indicator": ind.name,
            "unit": ind.unit,
            "values": row_values,
            "total": row_total,
            "target": target_value,
            "progress": progress,
        })

    pivot_data = sorted(pivot_data, key=lambda x: (x["project"], x["indicator"]))

    # --- Analytics ---
    indicator_distribution = base_qs.values("indicator__name").annotate(total=Sum("value")).order_by("-total")
    indicator_distribution_labels = [i["indicator__name"] for i in indicator_distribution]
    indicator_distribution_data = [int(i["total"]) for i in indicator_distribution]

    indicator_progress = []
    for ind in indicators:
        actual_total = int(base_qs.filter(indicator=ind).aggregate(total=Sum("value"))["total"] or 0)
        target_obj = IndicatorTarget.objects.filter(indicator=ind, year=selected_year).first()
        target_value = int(target_obj.value) if target_obj and target_obj.value > 0 else 1
        progress_pct = actual_total * 100 // target_value
        indicator_progress.append({"indicator": ind.name, "unit": ind.unit, "progress_pct": progress_pct})

    indicator_progress_labels = [i["indicator"] for i in indicator_progress]
    indicator_progress_data = [i["progress_pct"] for i in indicator_progress]

    cumulative_performance = []
    for ind in indicators:
        series = [int(base_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0) for m in months]
        running_total = 0
        cumulative_series = []
        for val in series:
            running_total += val
            cumulative_series.append(running_total)
        if any(series):
            cumulative_performance.append({"indicator": ind.name, "values": cumulative_series})

    totals = base_qs.values("indicator__name").annotate(total=Sum("value")).order_by("-total")
    top_indicators = list(totals[:5])
    top_indicators_labels = [i["indicator__name"] for i in top_indicators]
    top_indicators_data = [int(i["total"]) for i in top_indicators]

    # --- Heatmap ---
    facilities_data = []
    facilities = Facility.objects.prefetch_related("projects")
    for fac in facilities:
        projects_qs = fac.projects.all()
        if selected_project:
            projects_qs = projects_qs.filter(id=selected_project)
        if not projects_qs.exists():
            continue

        fac_qs = base_qs.filter(indicator__project__in=projects_qs)
        if selected_indicator:
            fac_qs = fac_qs.filter(indicator_id=selected_indicator)
        if selected_unit:
            fac_qs = fac_qs.filter(indicator__unit=selected_unit)

        total_value = fac_qs.aggregate(total=Sum("value"))["total"] or 0
        if total_value == 0:
            continue

        facilities_data.append({
            "id": fac.id,
            "name": fac.name,
            "latitude": float(fac.latitude) if fac.latitude else None,
            "longitude": float(fac.longitude) if fac.longitude else None,
            "projects": [{"id": p.id, "name": p.name} for p in projects_qs],
            "total": int(total_value),
        })

    # --- Correlation ---
    correlation_data = []
    ind_list = list(indicators[:2])
    if len(ind_list) == 2:
        x_values = [int(base_qs.filter(indicator=ind_list[0], month=m).aggregate(total=Sum("value"))["total"] or 0) for m in months]
        y_values = [int(base_qs.filter(indicator=ind_list[1], month=m).aggregate(total=Sum("value"))["total"] or 0) for m in months]
        correlation_data = [{"x": x, "y": y} for x, y in zip(x_values, y_values)]
    elif len(ind_list) == 1:
        x_values = [int(base_qs.filter(indicator=ind_list[0], month=m).aggregate(total=Sum("value"))["total"] or 0) for m in months]
        correlation_data = [{"x": x, "y": 0} for x in x_values]

    # --- Year-over-Year ---
    available_years = MonthlyEntry.objects.values_list("year", flat=True).distinct().order_by("year")
    yoy_data_values = []
    yoy_labels = []
    for y in available_years:
        qs = MonthlyEntry.objects.filter(year=y)
        if selected_unit:
            qs = qs.filter(indicator__unit=selected_unit)
        if selected_project:
            qs = qs.filter(indicator__project_id=selected_project)
        if selected_indicator:
            qs = qs.filter(indicator_id=selected_indicator)
        total = int(qs.aggregate(total=Sum("value"))["total"] or 0)
        yoy_data_values.append(total)
        yoy_labels.append(y)

    return {
        "month_headers": month_headers,
        "indicator_distribution_labels": json.dumps(indicator_distribution_labels),
        "indicator_distribution_data": json.dumps(indicator_distribution_data),
        "indicator_progress_labels": json.dumps(indicator_progress_labels),
        "indicator_progress_data": json.dumps(indicator_progress_data),
        "cumulative_performance": json.dumps(cumulative_performance),
        "top_indicators_labels": json.dumps(top_indicators_labels),
        "top_indicators_data": json.dumps(top_indicators_data),
        "facilities_json": json.dumps(facilities_data),
        "correlation_data": json.dumps(correlation_data),
        "yoy_labels": json.dumps(yoy_labels),
        "yoy_data_values": json.dumps(yoy_data_values),
        "pivot_data": pivot_data,
        "column_totals": column_totals,
        "grand_total": grand_total,
    }





# ------------------------
# Helper: get short month name
# ------------------------
def get_month_name(month_number):
    return calendar.month_abbr[month_number] if 1 <= month_number <= 12 else ""

# ------------------------
# CSV export view
# ------------------------
@login_required
def more_reports_export_csv(request):
    # ------------------------
    # Filters from GET
    # ------------------------
    selected_year = request.GET.get("year")
    selected_unit = request.GET.get("unit")
    selected_project = request.GET.get("project")
    selected_indicator = request.GET.get("indicator")

    # Cast numeric filters
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = None

    try:
        selected_project = int(selected_project)
    except (TypeError, ValueError):
        selected_project = None

    try:
        selected_indicator = int(selected_indicator)
    except (TypeError, ValueError):
        selected_indicator = None

    if selected_unit:
        selected_unit = selected_unit.strip()

    # ------------------------
    # Queryset of indicators filtered by project, unit, indicator
    # ------------------------
    indicators = Indicator.objects.all()
    if selected_project:
        indicators = indicators.filter(project_id=selected_project)
    if selected_unit:
        indicators = indicators.filter(unit=selected_unit)
    if selected_indicator:
        indicators = indicators.filter(id=selected_indicator)

    indicators = indicators.select_related("project").order_by("project__name", "name")

    # ------------------------
    # Get month headers
    # ------------------------
    months = list(range(1, 13))
    month_headers = [get_month_name(m) for m in months]

    # ------------------------
    # CSV response setup
    # ------------------------
    filename_parts = ["pivot"]
    if selected_year:
        filename_parts.append(str(selected_year))
    if selected_project:
        project_obj = Project.objects.filter(id=selected_project).first()
        if project_obj:
            filename_parts.append(project_obj.name.replace(" ", "_"))
    if selected_unit:
        filename_parts.append(selected_unit)
    filename = "_".join(filename_parts) + ".csv"

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    # ------------------------
    # Write header row
    # ------------------------
    headers = ["Year", "Project", "Indicator", "Unit"] + month_headers + ["Total", "Target", "Progress (%)"]
    writer.writerow(headers)

    # ------------------------
    # Totals tracking
    # ------------------------
    column_totals = {m: 0 for m in months}
    grand_total = 0

    # ------------------------
    # Write each indicator row
    # ------------------------
    for ind in indicators:
        row_values = []
        row_total = 0

        for m in months:
            qs = MonthlyEntry.objects.filter(indicator=ind, month=m)
            if selected_year:
                qs = qs.filter(year=selected_year)
            total_val = qs.aggregate(total=Sum("value"))["total"] or 0
            row_values.append(int(total_val))
            row_total += int(total_val)
            column_totals[m] += int(total_val)

        grand_total += row_total

        # Target and progress
        target_obj = IndicatorTarget.objects.filter(indicator=ind, year=selected_year).first() if selected_year else None
        target_value = int(target_obj.value) if target_obj and target_obj.value else getattr(ind, "target", 0) or 0
        progress = round((row_total / target_value * 100), 1) if target_value else 0

        writer.writerow([
            selected_year or "-",
            ind.project.name if ind.project else "-",
            ind.name,
            ind.unit,
            *row_values,
            row_total,
            target_value,
            f"{progress}%"
        ])

    # ------------------------
    # Write totals row
    # ------------------------
    totals_row = ["Column Totals", "", "", ""] + [column_totals[m] for m in months] + [grand_total, "-", "-"]
    writer.writerow(totals_row)

    return response




# -----------------------------
# Edit Indicator Targets View
# -----------------------------
@login_required
def edit_indicator_targets(request, indicator_id):
    indicator = get_object_or_404(Indicator, id=indicator_id)
    queryset = IndicatorTarget.objects.filter(indicator=indicator)

    # Create a modelformset with at least 1 extra blank form for new targets
    IndicatorTargetFormSetClass = modelformset_factory(
        IndicatorTarget,
        form=IndicatorTargetForm,
        extra=1,        # at least one blank form for adding
        can_delete=True # allows deletion
    )

    formset = IndicatorTargetFormSetClass(request.POST or None, queryset=queryset)
    numeric_errors = []

    if request.method == "POST" and formset.is_valid():
        try:
            with transaction.atomic():  # ensures atomic DB operations

                # 1️⃣ Delete targets marked for deletion
                for form in formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()

                # 2️⃣ Save or update remaining targets
                for form in formset:
                    if form.cleaned_data.get('DELETE'):
                        continue  # skip deleted forms

                    year = form.cleaned_data.get('year')
                    raw_value = form.cleaned_data.get('value')

                    if year is None or raw_value in [None, ""]:
                        continue  # skip incomplete forms

                    # Ensure value is a whole number
                    try:
                        value = safe_int(raw_value)
                    except (ValueError, TypeError):
                        numeric_errors.append(f"Year {year}: '{raw_value}' is not a whole number.")
                        continue

                    # Update existing target or create new one
                    IndicatorTarget.objects.update_or_create(
                        indicator=indicator,
                        year=year,
                        defaults={'value': value}
                    )

        except IntegrityError:
            formset.add_error(None, "Error: Duplicate target for the same year.")

        if numeric_errors:
            messages.warning(
                request,
                "Some targets were not saved due to invalid values: " + ", ".join(numeric_errors)
            )
        else:
            messages.success(request, "Indicator targets saved successfully.")

        return redirect('project_kpis', pk=indicator.project.id)

    # Prepare context with current year and year range
    current_year = datetime.date.today().year
    year_range = range(current_year - 5, current_year + 6)

    context = {
        "indicator": indicator,
        "formset": formset,
        "current_year": current_year,
        "year_range": year_range,
    }

    return render(request, "core/edit_indicator_targets.html", context)



@login_required
def data_story(request):
    """
    Dynamic Data Story dashboard with optional year filter.
    Shows top 10 indicators with most recent/significant changes.
    Tags indicators as Improving, Declining, Stable, or New.
    Targets are always for the current year only.
    Supports AJAX requests for dynamic year filtering.
    """

    current_year = date.today().year

    # -------------------------
    # Get all years with data for dropdown
    # -------------------------
    years = MonthlyEntry.objects.dates("created_at", "year", order="DESC")
    year_list = [y.year for y in years]

    # -------------------------
    # Get selected year from query param ?year=YYYY
    # Default to latest year
    # -------------------------
    selected_year = request.GET.get("year")
    if selected_year:
        try:
            selected_year = int(selected_year)
        except ValueError:
            selected_year = year_list[0] if year_list else current_year
    else:
        selected_year = year_list[0] if year_list else current_year

    # -------------------------
    # Get all entries for the selected year, latest first per indicator
    # -------------------------
    entries = MonthlyEntry.objects.filter(year=selected_year).order_by("indicator_id", "-created_at")

    top_insights = []
    seen = set()

    for entry in entries:
        if entry.indicator_id in seen:
            continue
        seen.add(entry.indicator_id)

        # Previous entry for comparison (any year)
        prev_entry = (
            MonthlyEntry.objects.filter(indicator=entry.indicator, created_at__lt=entry.created_at)
            .order_by("-created_at")
            .first()
        )

        if prev_entry:
            try:
                change = ((entry.value - prev_entry.value) / prev_entry.value * 100) if prev_entry.value != 0 else 0
            except (ZeroDivisionError, InvalidOperation):
                change = 0
            change_available = True
        else:
            change = 0
            change_available = False

        # -------------------------
        # Progress vs target
        # Targets are always for current year
        # -------------------------
        target_obj = IndicatorTarget.objects.filter(indicator=entry.indicator, year=current_year).first()
        target_value = float(target_obj.value) if target_obj else 0.0
        actual = float(entry.value)
        try:
            progress_percent = (actual / target_value * 100) if target_value > 0 else 0.0
        except (ZeroDivisionError, InvalidOperation):
            progress_percent = 0.0

        # Historical chart data (last 6 entries)
        last_6 = MonthlyEntry.objects.filter(indicator=entry.indicator).order_by("-created_at")[:6]
        chart_labels = [date(x.year, x.month, 1).strftime("%b %Y") for x in reversed(last_6)]
        chart_values = [float(x.value) for x in reversed(last_6)]

        # Determine tag + story
        if not change_available:
            tag = "New"
            story = f"{entry.indicator.name} has a new entry of {actual}, achieving {progress_percent:.1f}% of the target."
        elif change > 0:
            tag = "Improving"
            story = f"{entry.indicator.name} is currently at {actual}, showing an improvement of {change:.1f}% and achieving {progress_percent:.1f}% of the target."
        elif change < 0:
            tag = "Declining"
            story = f"{entry.indicator.name} is currently at {actual}, showing a decline of {abs(change):.1f}% and achieving {progress_percent:.1f}% of the target."
        else:
            tag = "Stable"
            story = f"{entry.indicator.name} is currently at {actual}, with no significant change and achieving {progress_percent:.1f}% of the target."

        top_insights.append({
            "title": entry.indicator.name,
            "chart_data": json.dumps({"labels": chart_labels, "values": chart_values}),
            "story": story,
            "tag": tag,
            "change": change if change_available else None,
            "last_updated": entry.created_at,
            "actual": actual,
            "target": target_value,
            "progress_percent": progress_percent,
        })

    # -------------------------
    # Sort by significance or recency and pick top 10
    # -------------------------
    ranked = sorted(
        top_insights,
        key=lambda x: (x["change"] if x["change"] is not None else -1, x["last_updated"]),
        reverse=True
    )[:10]

    context = {
        "insights": ranked,
        "selected_year": selected_year,
        "year_list": year_list
    }

    # -------------------------
    # AJAX request: return only KPI cards partial
    # -------------------------
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string("core/partials/_data_story_cards.html", context, request=request)
        return HttpResponse(html)

    # -------------------------
    # Normal full-page render
    # -------------------------
    return render(request, "core/data_story.html", context)




# -------------------------
# EXPORT CSV - Dynamic with Numeric Totals
# -------------------------

@login_required
def reports_export_csv(request):
    # Fetch all indicators
    indicators = Indicator.objects.all()

    # Dynamically determine fields to export (exclude ID if desired)
    exclude_fields = ['id']
    fields = [f.name for f in Indicator._meta.get_fields() if f.concrete and f.name not in exclude_fields]

    # Identify numeric fields for totals
    numeric_fields = [f.name for f in Indicator._meta.get_fields()
                      if f.concrete and isinstance(f, FloatField)]

    # Initialize totals dictionary
    totals = {f: 0 for f in numeric_fields}

    # Prepare CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow(fields)

    # Write data rows and accumulate totals
    for ind in indicators:
        row = []
        for f in fields:
            val = getattr(ind, f, "")
            row.append(val)
            # accumulate total if numeric
            if f in numeric_fields and isinstance(val, (int, float)):
                totals[f] += val
        writer.writerow(row)

    # Write totals row
    totals_row = []
    for f in fields:
        if f in numeric_fields:
            totals_row.append(totals[f])
        else:
            totals_row.append("Total" if f == fields[0] else "")
    writer.writerow(totals_row)

    return response



@login_required
def more_reports_export_excel(request):
    # --- Selected filters ---
    selected_year = request.GET.get("year")
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = datetime.date.today().year

    selected_unit = request.GET.get("unit") or None
    selected_project = request.GET.get("project")
    selected_project = int(selected_project) if selected_project and selected_project.isdigit() else None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    # --- Base queryset ---
    base_qs = MonthlyEntry.objects.filter(year=selected_year)
    if selected_unit:
        base_qs = base_qs.filter(indicator__unit=selected_unit)
    if selected_project:
        base_qs = base_qs.filter(indicator__project_id=selected_project)
    if selected_indicator:
        base_qs = base_qs.filter(indicator_id=selected_indicator)

    # --- Indicators ---
    indicators = Indicator.objects.all()
    if selected_unit:
        indicators = indicators.filter(unit=selected_unit)
    if selected_project:
        indicators = indicators.filter(project_id=selected_project)
    if selected_indicator:
        indicators = indicators.filter(id=selected_indicator)

    # --- Pivot Table Data ---
    months = list(range(1, 13))
    month_headers = [calendar.month_abbr[m] for m in months]
    pivot_data = []
    column_totals = {m: 0 for m in months}
    grand_total = 0

    for ind in indicators:
        row_values, row_total = [], 0
        for m in months:
            val = base_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
            val = int(val)
            row_values.append(val)
            row_total += val
            column_totals[m] += val
        grand_total += row_total

        target_obj = IndicatorTarget.objects.filter(indicator=ind, year=selected_year).first()
        target_value = int(target_obj.value) if target_obj and target_obj.value > 0 else 1
        progress = row_total / target_value  # decimal for % formatting

        pivot_data.append({
            "year": selected_year,
            "project": ind.project.name if ind.project else "-",
            "indicator": ind.name,
            "unit": ind.unit,
            "values": row_values,
            "total": row_total,
            "target": target_value,
            "progress": progress,
        })

    # Sort pivot_data
    pivot_data = sorted(pivot_data, key=lambda x: (x["project"], x["indicator"]))

    # --- Create Excel ---
    wb = Workbook()
    ws = wb.active
    ws.title = "Pivot Table"

    # Title row
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4 + len(months) + 3)
    ws["A1"] = "Life Concern - Pivot Table showing Projects, Indicators and Progress"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = Alignment(horizontal="center")

    # Headers (black & white for printing)
    headers = ["Year", "Project", "Indicator", "Unit"] + month_headers + ["Total", "Target", "Progress (%)"]
    ws.append(headers)
    header_row = ws[ws.max_row]

    # Define top and bottom border for headers
    thick_border = Side(border_style="medium", color="000000")
    for cell in header_row:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        # Apply top and bottom borders to make headers stand out
        cell.border = Border(top=thick_border, bottom=thick_border)

    # Data rows with subtle visual cues
    for row in pivot_data:
        excel_row = [
            row["year"], row["project"], row["indicator"], row["unit"],
            *row["values"], row["total"], row["target"], row["progress"]
        ]
        ws.append(excel_row)

        # Format progress column
        progress_cell = ws.cell(row=ws.max_row, column=len(excel_row))
        progress_cell.number_format = "0%"  # display as percent
        progress_val = row["progress"] * 100

        # Conditional coloring using subtle dark shades
        if progress_val >= 75:
            progress_cell.font = Font(bold=True, color="006100")  # dark green
        elif progress_val >= 50:
            progress_cell.font = Font(bold=True, color="9C6500")  # dark amber
        else:
            progress_cell.font = Font(bold=True, color="9C0006")  # dark red

        progress_cell.alignment = Alignment(horizontal="center")

    # Totals row
    totals_row = ["", "", "", "Column Totals"] + [column_totals[m] for m in months] + [grand_total, "-", "-"]
    ws.append(totals_row)
    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True)

    # Footer note
    ws.merge_cells(start_row=ws.max_row + 2, start_column=1, end_row=ws.max_row + 2, end_column=len(headers))
    ws.cell(row=ws.max_row, column=1).value = f"Exported from Life Concern Data Management System - {datetime.date.today():%Y-%m-%d}"
    ws.cell(row=ws.max_row, column=1).alignment = Alignment(horizontal="center")
    ws.cell(row=ws.max_row, column=1).font = Font(italic=True, size=10)

    # Apply subtle borders to data rows
    thin = Side(border_style="thin", color="000000")
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            # Skip overwriting header top/bottom borders
            if cell.row == 2:
                continue
            cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

    # Auto column widths
    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = max_length + 3

    # Response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="Pivot_Report_{selected_year}.xlsx"'
    wb.save(response)
    return response


@login_required
def monthly_performance_report(request):
    import datetime, calendar
    from django.db.models import Sum

    # --- Year filter ---
    current_year = datetime.date.today().year
    selected_year = request.GET.get("year")
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = current_year

    # --- Unit & Indicator filters ---
    selected_unit = request.GET.get("unit") or None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    # --- Month range filter ---
    month_from = request.GET.get("month_from")
    month_to = request.GET.get("month_to")

    try:
        month_from = int(month_from) if month_from else 1
        month_to = int(month_to) if month_to else 12
    except ValueError:
        month_from = 1
        month_to = 12

    # Ensure valid range
    if month_from < 1 or month_from > 12:
        month_from = 1
    if month_to < 1 or month_to > 12:
        month_to = 12
    if month_from > month_to:
        month_from, month_to = month_to, month_from

    # --- Base queryset for monthly entries ---
    base_qs = MonthlyEntry.objects.filter(year=selected_year)
    if selected_unit:
        base_qs = base_qs.filter(indicator__unit=selected_unit)
    if selected_indicator:
        base_qs = base_qs.filter(indicator_id=selected_indicator)

    # --- Months and headers based on selected range ---
    months = list(range(month_from, month_to + 1))
    month_headers = [calendar.month_abbr[m] for m in months]

    # --- Projects (only active) ---
    projects = Project.objects.filter(active=True).order_by("name")

    # --- Monthly trends per project ---
    monthly_trends = []
    for proj in projects:
        proj_qs = base_qs.filter(indicator__project=proj)
        series = [
            int(proj_qs.filter(month=m).aggregate(total=Sum("value"))["total"] or 0)
            for m in months
        ]

        # ✅ Keep project even if all values = 0 (so they appear in list)
        indicators_list = sorted(proj_qs.values_list("indicator__name", flat=True).distinct())
        monthly_trends.append({
            "project_id": proj.id,
            "project_name": proj.name,
            "indicator_summary": ", ".join(indicators_list) if indicators_list else "No indicators",
            "values": series,
        })

    # --- Units & indicators for filter dropdowns ---
    units = sorted(Indicator.objects.values_list("unit", flat=True).distinct())
    indicators = Indicator.objects.all().order_by("name")

    # --- Years for filter dropdown ---
    years = (
        list(MonthlyEntry.objects.values_list("year", flat=True).distinct().order_by("-year"))
        or [current_year]
    )

    # --- Month choices for dropdowns ---
    month_choices = [(i, calendar.month_abbr[i]) for i in range(1, 13)]

    context = {
        "selected_year": selected_year,
        "years": years,
        "selected_unit": selected_unit,
        "selected_indicator": selected_indicator,
        "units": units,
        "indicators": indicators,
        "months": months,
        "month_headers": month_headers,
        "monthly_trends": monthly_trends,
        "month_from": month_from,
        "month_to": month_to,
        "month_choices": month_choices,
    }

    return render(request, "core/monthly_performance_report.html", context)



from django.http import JsonResponse
from django import forms
from .models import Facility, Project
import json

# -----------------------------
# Facility Form
# -----------------------------
class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['name', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
        }

# -----------------------------
# Facilities Map View
# -----------------------------
def facilities_map(request):
    active_projects = Project.objects.filter(active=True)

    # Selected year from GET, default to current year
    current_year = date.today().year
    year = int(request.GET.get("year", current_year))

    # Year options for filter
    year_options = list(range(current_year - 5, current_year + 6))

    # Handle Add/Edit via AJAX POST
    if request.method == "POST":
        facility_id = request.POST.get("facility_id")
        project_ids = request.POST.getlist("projects")

        if facility_id:
            facility = get_object_or_404(Facility, id=facility_id)
            form = FacilityForm(request.POST, instance=facility)
        else:
            form = FacilityForm(request.POST)

        if form.is_valid():
            facility = form.save()
            # Update ManyToMany relation
            if project_ids:
                facility_projects = Project.objects.filter(id__in=project_ids)
                facility.projects.set(facility_projects)
            else:
                facility.projects.clear()

            facilities_qs = Facility.objects.filter(projects__in=active_projects).distinct().prefetch_related('projects')
            facilities_list = [
                {
                    "id": f.id,
                    "name": f.name,
                    "latitude": float(f.latitude),
                    "longitude": float(f.longitude),
                    "projects": [
                        {
                            "id": p.id,
                            "name": p.name,
                            # Only sum indicators where unit is "people reached"
                            "people_reached": sum(
                                ind.entries.filter(year=year).aggregate(total=models.Sum('value'))['total'] or 0
                                for ind in p.indicators.filter(unit__iexact='people reached')
                            )
                        }
                        for p in f.projects.all()
                    ],
                }
                for f in facilities_qs
            ]
            return JsonResponse({"success": True, "facilities": facilities_list})
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    # GET request
    facilities_qs = Facility.objects.filter(projects__in=active_projects).distinct().prefetch_related('projects')
    facilities_list = [
        {
            "id": f.id,
            "name": f.name,
            "latitude": float(f.latitude),
            "longitude": float(f.longitude),
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "people_reached": sum(
                        ind.entries.filter(year=year).aggregate(total=models.Sum('value'))['total'] or 0
                        for ind in p.indicators.filter(unit__iexact='people reached')
                    )
                }
                for p in f.projects.all()
            ],
        }
        for f in facilities_qs
    ]

    return render(request, "core/facilities_map.html", {
        "form": FacilityForm(),
        "facilities_json": json.dumps(facilities_list),
        "active_projects": active_projects,
        "year_options": year_options,
        "selected_year": year,
    })

# -----------------------------
# Delete Facility
# -----------------------------
def facility_delete(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    facility.delete()
    return JsonResponse({"success": True})



from weasyprint import HTML

@login_required
def more_reports_pdf(request):
    current_year = datetime.date.today().year

    # --- Selected filters ---
    selected_year = request.GET.get("year")
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = current_year

    selected_unit = request.GET.get("unit") or None
    selected_project = request.GET.get("project")
    selected_project = int(selected_project) if selected_project and selected_project.isdigit() else None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    # --- Base queryset ---
    base_qs = MonthlyEntry.objects.filter(year=selected_year)
    if selected_unit:
        base_qs = base_qs.filter(indicator__unit=selected_unit)
    if selected_project:
        base_qs = base_qs.filter(indicator__project_id=selected_project)
    if selected_indicator:
        base_qs = base_qs.filter(indicator_id=selected_indicator)

    # --- Indicators ---
    indicators = Indicator.objects.all()
    if selected_unit:
        indicators = indicators.filter(unit=selected_unit)
    if selected_project:
        indicators = indicators.filter(project_id=selected_project)
    if selected_indicator:
        indicators = indicators.filter(id=selected_indicator)

    # Sort indicators by project and name
    indicators = indicators.order_by('project__name', 'name')

    # --- Pivot Table Data ---
    months = list(range(1, 13))
    month_headers = [calendar.month_abbr[m] for m in months]
    pivot_data = []
    column_totals = {m: 0 for m in months}
    grand_total = 0

    for ind in indicators:
        row_values, row_total = [], 0
        for m in months:
            val = base_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
            val = int(val)
            row_values.append(val)
            row_total += val
            column_totals[m] += val
        grand_total += row_total

        target_obj = IndicatorTarget.objects.filter(indicator=ind, year=selected_year).first()
        target_value = int(target_obj.value) if target_obj and target_obj.value > 0 else 1
        progress = (row_total / target_value) * 100  # percentage

        # Determine CSS class for progress
        if progress >= 75:
            progress_class = "progress-high"
        elif progress >= 50:
            progress_class = "progress-medium"
        else:
            progress_class = "progress-low"

        pivot_data.append({
            "year": selected_year,
            "project": ind.project.name if ind.project else "-",
            "indicator": ind.name,
            "unit": ind.unit,
            "values": row_values,
            "total": row_total,
            "target": target_value,
            "progress": f"{progress:.1f}%",
            "progress_class": progress_class
        })

    # --- Render HTML ---
    html_string = render_to_string('core/more_reports_pdf.html', {
        "month_headers": month_headers,
        "pivot_data": pivot_data,
        "column_totals": column_totals,
        "grand_total": grand_total,
        "now": datetime.date.today(),
    })

    # --- Generate PDF ---
    pdf_file = HTML(string=html_string).write_pdf()

    # --- Return PDF response ---
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Pivot_Report_{selected_year}.pdf"'
    return response



