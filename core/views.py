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
from core.models import Report  # adjust if your Report model is in another app
from core.templatetags.custom_tags import get_month_name
import calendar


# -------------------------
# DASHBOARD
# -------------------------
@login_required
def dashboard(request):
    """Main dashboard view showing all active projects and summary info."""
    projects = Project.objects.filter(active=True)  # ✅ only active projects
    total_projects = projects.count()
    total_indicators = Indicator.objects.count()
    total_entries = MonthlyEntry.objects.count()

    # 🔹 Extra KPIs
    current_year = datetime.date.today().year
    # ✅ Only count People Reached
    annual_total = (
        MonthlyEntry.objects.filter(
            year=current_year,
            indicator__unit__iexact="People Reached"   # case-insensitive match
        ).aggregate(total=Sum("value"))["total"] or 0
    )

    user_count = User.objects.filter(is_active=True).count()

    # 🔹 Monthly performance (labels + data for chart)
    monthly = (
        MonthlyEntry.objects.filter(year=current_year)
        .values("month")
        .annotate(total=Sum("value"))
        .order_by("month")
    )
    monthly_labels = [
        datetime.date(1900, m["month"], 1).strftime("%b") for m in monthly
    ]
    monthly_data = [m["total"] for m in monthly]

    # 🔹 Project contribution (labels + data for chart)
    by_project = (
        MonthlyEntry.objects.filter(year=current_year)
        .values("indicator__project__name")
        .annotate(total=Sum("value"))
        .order_by("indicator__project__name")
    )
    by_project_labels = [p["indicator__project__name"] for p in by_project]
    by_project_data = [p["total"] for p in by_project]

    # 🔹 Recent activity (last 5 entries)
    recent_entries = (
        MonthlyEntry.objects.select_related("indicator", "indicator__project", "created_by")
        .order_by("-created_at")[:5]
    )

    # Optional: Include recent reports too
    recent_reports = Report.objects.select_related("user").order_by("-created_at")[:5]

    return render(request, "core/dashboard.html", {
        "projects": projects,
        "total_projects": total_projects,
        "total_indicators": total_indicators,
        "total_entries": total_entries,

        # 👇 Extra context
        "current_year": current_year,
        "annual_total": annual_total,
        "user_count": user_count,
        "monthly_labels": monthly_labels,
        "monthly_data": monthly_data,
        "by_project_labels": by_project_labels,
        "by_project_data": by_project_data,

        # 👇 Recent activity
        "recent_entries": recent_entries,
        "recent_reports": recent_reports,  # optional, if you want reports too
    })


# -------------------------
# PROJECT DETAIL
# -------------------------
@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    indicators = Indicator.objects.filter(project=project)
    months = list(range(1, 13))
    year = int(request.GET.get("year", datetime.datetime.now().year))

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


# -------------------------
# KPI Data Entry (Bulk Save + Totals)
# -------------------------
@login_required
def project_kpis(request, pk):
    project = get_object_or_404(Project, pk=pk)
    indicators = Indicator.objects.filter(project=project)
    months = list(range(1, 13))
    year = int(request.GET.get("year", request.POST.get("year", datetime.datetime.now().year)))

    if request.method == "POST":
        with transaction.atomic():
            for ind in indicators:
                for month in months:
                    field_name = f"val_{ind.id}_{month}"
                    raw_val = request.POST.get(field_name, "").strip()
                    if raw_val == "":
                        continue
                    try:
                        val = float(raw_val)
                    except ValueError:
                        continue
                    MonthlyEntry.objects.update_or_create(
                        indicator=ind,
                        year=year,
                        month=month,
                        defaults={"value": val, "created_by": request.user},
                    )
                # Update indicator progress
                total_val = MonthlyEntry.objects.filter(indicator=ind, year=year).aggregate(
                    total=Sum("value")
                )["total"] or 0
                ind.current_value = total_val
                ind.update_progress()

        messages.success(request, "KPI data saved successfully!")
        return redirect("project_kpis", pk=project.id)

    # -------------------------
    # Build grid + totals
    # -------------------------
    grid = defaultdict(dict)
    totals = {}           # ✅ Row totals per indicator
    monthly_totals = {}   # ✅ Column totals across indicators
    grand_total = 0       # ✅ Bottom-right grand total

    # Build grid and row totals
    for ind in indicators:
        row_total = 0
        for month in months:
            entry = MonthlyEntry.objects.filter(indicator=ind, year=year, month=month).first()
            val = entry.value if entry else 0
            grid[ind.id][month] = val if val != 0 else None
            row_total += val
        totals[ind.id] = row_total
        grand_total += row_total

    # Build column totals
    for month in months:
        monthly_totals[month] = sum(grid[ind.id].get(month, 0) or 0 for ind in indicators)

    return render(request, "core/project_kpis.html", {
        "project": project,
        "indicators": indicators,
        "months": months,
        "year": year,
        "grid": grid,
        "totals": totals,              # 👈 Row totals
        "monthly_totals": monthly_totals,  # 👈 Column totals
        "grand_total": grand_total,    # 👈 Grand total
    })


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


# -------------------------
# KPI MANAGEMENT
# -------------------------
@login_required
def indicator_add(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    if request.method == "POST":
        form = IndicatorForm(request.POST)
        if form.is_valid():
            indicator = form.save(commit=False)
            indicator.project = project
            indicator.save()
            messages.success(request, "KPI added successfully!")
            return redirect("project_detail", pk=project.pk)
    else:
        form = IndicatorForm()
    return render(request, "core/indicators/indicator_form.html",
                  {"form": form, "project": project, "title": "Add KPI"})


@login_required
def indicator_edit(request, project_pk, pk):
    project = get_object_or_404(Project, pk=project_pk)
    indicator = get_object_or_404(Indicator, pk=pk, project=project)
    if request.method == "POST":
        form = IndicatorForm(request.POST, instance=indicator)
        if form.is_valid():
            form.save()
            messages.success(request, "KPI updated successfully!")
            return redirect("project_detail", pk=project.pk)
    else:
        form = IndicatorForm(instance=indicator)
    return render(request, "core/indicators/indicator_form.html",
                  {"form": form, "project": project, "indicator": indicator, "title": "Edit KPI"})


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
# LIST PROJECTS
# -------------------------
@login_required
def projects(request):
    projects = Project.objects.all()
    return render(request, "core/projects.html", {"projects": projects})


# -------------------------
# BULK SAVE ENTRIES
# -------------------------
@login_required
def bulk_save_entries(request, pk):
    project = get_object_or_404(Project, pk=pk)
    indicators = Indicator.objects.filter(project=project)

    if request.method == "POST":
        year = int(request.POST.get("year", datetime.datetime.now().year))
        month = int(request.POST.get("month", datetime.datetime.now().month))
        with transaction.atomic():
            for indicator in indicators:
                value = request.POST.get(f"indicator_{indicator.id}")
                if value not in [None, ""]:
                    MonthlyEntry.objects.update_or_create(
                        indicator=indicator,
                        year=year,
                        month=month,
                        defaults={"value": float(value), "created_by": request.user},
                    )
        messages.success(request, f"Entries for {month}/{year} saved successfully!")
        return redirect("project_detail", pk=project.id)

    return render(request, "core/bulk_save_entries.html", {
        "project": project,
        "indicators": indicators,
        "year": datetime.datetime.now().year,
        "month": datetime.datetime.now().month,
    })


# -------------------------
# REPORTS
# -------------------------
@login_required
def reports(request):
    current_year = datetime.datetime.now().year
    year = int(request.GET.get("year", current_year))

    # ✅ Collect distinct years available in MonthlyEntry
    years = (
        MonthlyEntry.objects.values_list("year", flat=True)
        .distinct()
        .order_by("-year")
    )
    if not years:
        years = [current_year]

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
        "years": years,   # ✅ Send list of available years to template
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

# -------------------------
# MORE REPORTS (UPDATED YEAR-SENSITIVE)
# -------------------------
@login_required
def more_reports(request):


    # -------------------------
    # Year filter
    # -------------------------
    current_year = datetime.datetime.now().year
    selected_year = request.GET.get("year")
    try:
        selected_year = int(selected_year)
    except (TypeError, ValueError):
        selected_year = current_year

    # Reports per Staff
    reports_per_staff = (
        Report.objects.filter(created_at__year=selected_year)
        .values("user__username")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    # Reports per Month
    reports_per_month = (
        Report.objects.filter(created_at__year=selected_year)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    # Full Reports List (year filtered)
    reports = Report.objects.filter(created_at__year=selected_year).order_by("-created_at")

    # Pivot Table Filters
    units = Indicator.objects.values_list("unit", flat=True).distinct()
    projects = Project.objects.all()
    indicators = Indicator.objects.all()

    selected_unit = request.GET.get("unit") or None
    selected_project = request.GET.get("project")
    selected_project = int(selected_project) if selected_project and selected_project.isdigit() else None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    # -------------------------
    # Pivot QuerySet (YEAR FILTERED)
    # -------------------------
    pivot_qs = MonthlyEntry.objects.filter(year=selected_year)
    if selected_unit:
        pivot_qs = pivot_qs.filter(indicator__unit=selected_unit)
    if selected_project:
        pivot_qs = pivot_qs.filter(indicator__project_id=selected_project)
    if selected_indicator:
        pivot_qs = pivot_qs.filter(indicator_id=selected_indicator)

    # -------------------------
    # Build pivot table
    # -------------------------
    months = list(range(1, 13))
    month_headers = [calendar.month_abbr[m] for m in months]  # Short month names Jan, Feb, ...
    pivot_data = []
    column_totals = {m: 0 for m in months}
    grand_total = 0

    for ind in indicators:
        if selected_unit and ind.unit != selected_unit:
            continue
        if selected_project and ind.project.id != selected_project:
            continue
        if selected_indicator and ind.id != selected_indicator:
            continue

        row_total = 0
        row_values = []
        for m in months:
            val = pivot_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
            row_values.append(val)
            row_total += val
            column_totals[m] += val
        grand_total += row_total
        if row_total > 0:
            pivot_data.append({
                "indicator": ind.name,
                "unit": ind.unit,
                "values": row_values,
                "total": row_total
            })

    # -------------------------
    # List of available years for dropdown
    # -------------------------
    years = MonthlyEntry.objects.values_list("year", flat=True).distinct().order_by("-year")
    if not years:
        years = [current_year]

    context = {
        "selected_year": selected_year,
        "years": years,  # send to template
        "reports_per_staff": reports_per_staff,
        "reports_per_month": reports_per_month,
        "reports": reports,
        "units": units,
        "projects": projects,
        "indicators": indicators,
        "selected_unit": selected_unit,
        "selected_project": selected_project,
        "selected_indicator": selected_indicator,
        "months": months,
        "month_headers": month_headers,
        "pivot_data": pivot_data,
        "column_totals": column_totals,
        "grand_total": grand_total,
    }

    return render(request, "core/more_reports.html", context)




# -------------------------
# EXPORT CSV FOR MORE REPORTS
# -------------------------
@login_required
def more_reports_export_csv(request):
    selected_unit = request.GET.get("unit") or None
    selected_project = request.GET.get("project")
    selected_project = int(selected_project) if selected_project and selected_project.isdigit() else None
    selected_indicator = request.GET.get("indicator")
    selected_indicator = int(selected_indicator) if selected_indicator and selected_indicator.isdigit() else None

    pivot_qs = MonthlyEntry.objects.all()
    if selected_unit:
        pivot_qs = pivot_qs.filter(indicator__unit=selected_unit)
    if selected_project:
        pivot_qs = pivot_qs.filter(indicator__project_id=selected_project)
    if selected_indicator:
        pivot_qs = pivot_qs.filter(indicator_id=selected_indicator)

    indicators = Indicator.objects.all()
    if selected_unit:
        indicators = indicators.filter(unit=selected_unit)
    if selected_project:
        indicators = indicators.filter(project_id=selected_project)
    if selected_indicator:
        indicators = indicators.filter(id=selected_indicator)

    months = list(range(1, 13))
    month_headers = [get_month_name(m) for m in months]  # ✅ Month names in CSV
    column_totals = {m: 0 for m in months}
    grand_total = 0

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="custom_reports.csv"'
    writer = csv.writer(response)

    # Header
    writer.writerow(["Indicator", "Unit"] + month_headers + ["Total"])

    # Data rows
    for ind in indicators:
        row_values = []
        row_total = 0
        for m in months:
            val = pivot_qs.filter(indicator=ind, month=m).aggregate(total=Sum("value"))["total"] or 0
            row_values.append(val)
            row_total += val
            column_totals[m] += val
        grand_total += row_total
        writer.writerow([ind.name, ind.unit] + row_values + [row_total])

    # Column totals row
    totals_row = ["Column Totals", ""] + [column_totals[m] for m in months] + [grand_total]
    writer.writerow(totals_row)

    return response



# -------------------------
# EXPORT CSV
# -------------------------
@login_required
def reports_export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="report.csv"'
    response.write("indicator,value\n")
    response.write("Sample Indicator,123\n")
    return response
