from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
import datetime
from collections import defaultdict
from django.db.models import Sum
from django.db.models.functions import ExtractMonth   # ✅ Needed for monthly grouping
from django.contrib.auth.models import User

from .models import Project, Indicator, MonthlyEntry
from .forms import ProjectForm
from .forms import IndicatorForm   # <-- NEW import


# -------------------------
# DASHBOARD
# -------------------------
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
    annual_total = MonthlyEntry.objects.filter(year=current_year).aggregate(
        total=Sum("value")
    )["total"] or 0

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
# KPI Data Entry (Bulk Save)
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
                total_val = MonthlyEntry.objects.filter(indicator=ind, year=year).aggregate(
                    total=Sum("value")
                )["total"] or 0
                ind.current_value = total_val
                ind.update_progress()

        messages.success(request, "KPI data saved successfully!")
        return redirect("project_kpis", pk=project.id)

    grid = {}
    for ind in indicators:
        grid[ind.id] = {}
        for month in months:
            entry = MonthlyEntry.objects.filter(indicator=ind, year=year, month=month).first()
            grid[ind.id][month] = entry.value if entry else None

    return render(request, "core/project_kpis.html", {
        "project": project,
        "indicators": indicators,
        "months": months,
        "year": year,
        "grid": grid,
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
    # Project Totals (table + chart)
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
        "project_trends": project_trends,
    }
    return render(request, "core/reports.html", context)


    # -------------------------
    # Indicator Drilldown / Totals
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
    # Year-to-Date Totals
    # -------------------------
    ytd_totals = indicator_totals

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
    # Project Totals (table + chart)
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
            # For chart: name + value only
            project_totals_chart[project.name] = [
                {
                    "indicator": r["indicator__name"],
                    "unit": r["indicator__unit"],
                    "value": r["total"] or 0,
                }
                for r in proj_rows
            ]

    # -------------------------
    # Project Trends (monthly series per indicator in project)
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
        "projects": projects,
        "indicators": indicators,
        "units": units,
        "selected_unit": selected_unit,
        "selected_indicators": selected_indicator_ids,

        # Totals per indicator
        "indicator_totals": indicator_totals,
        "selected_indicators_data": selected_indicators_data,
        "overall_total": overall_total,
        "ytd_totals": ytd_totals,

        # Monthly / Quarterly
        "monthly_labels": monthly_labels,
        "monthly_data": monthly_data,
        "quarterly_labels": quarterly_labels,
        "quarterly_data": quarterly_data,

        # Project-based
        "project_totals": project_totals,
        "project_totals_chart": project_totals_chart,
        "project_trends": project_trends,
    }
    return render(request, "core/reports.html", context)



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
